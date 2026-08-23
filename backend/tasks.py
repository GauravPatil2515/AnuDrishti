"""
Celery Tasks for Async Batch Processing
=======================================
Long-running batch jobs and what-if optimizations run asynchronously.
"""
import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from celery_app import celery_app
import redis

# Redis client for progress updates
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=2,
    decode_responses=True
)


def _update_progress(task_id: str, current: int, total: int, status: str = "processing", result=None):
    """Update task progress in Redis for WebSocket polling."""
    progress_data = {
        'task_id': task_id,
        'current': current,
        'total': total,
        'progress': round((current / total) * 100, 1) if total > 0 else 0,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    if result is not None:
        progress_data['result'] = result
    
    redis_client.setex(f"task:{task_id}:progress", 3600, json.dumps(progress_data))
    # Also publish for real-time WebSocket
    redis_client.publish(f"task:{task_id}:updates", json.dumps(progress_data))


@celery_app.task(bind=True, max_retries=3)
def analyze_batch_task(self, smiles_list, include_explanation=False):
    """
    Async batch analysis task.
    Updates progress in Redis for real-time frontend updates.
    """
    task_id = self.request.id
    total = len(smiles_list)
    results = []
    
    try:
        # Import inside task to avoid circular imports
        import sys
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from routes.pharmaguard import (
            predictor, predictor_cached, _validate_smiles, 
            _build_pharmaguard_analysis
        )
        from rdkit import Chem
        import traceback
        
        def _process(smi):
            smi = smi.strip() if isinstance(smi, str) else smi
            mol, smiles_err = _validate_smiles(smi)
            if smiles_err:
                return {'smiles': smi, 'error': smiles_err, 'code': 'INVALID_SMILES'}
            try:
                a = _build_pharmaguard_analysis(
                    smi, 
                    include_explanation=include_explanation, 
                    include_ood=True, 
                    use_mc=False
                )
                if a and 'error' not in a:
                    return a
                return {'smiles': smi, 'error': (a or {}).get('error', 'failed')}
            except Exception as e:
                return {'smiles': smi, 'error': str(e)}
        
        # Process with progress updates
        for i, smi in enumerate(smiles_list):
            result = _process(smi)
            results.append(result)
            _update_progress(
                task_id, 
                current=i + 1, 
                total=len(smiles_list),
                status="processing"
            )
        
        # Sort by triage priority (RED first)
        def _priority(rec):
            t = rec.get('triage', {}).get('category', 'GREEN')
            return {'RED': 0, 'YELLOW': 1, 'GREEN': 2}.get(t, 3)
        results.sort(key=_priority)
        
        # Persist locally
        try:
            from pathlib import Path
            results_dir = Path(__file__).parent.parent / 'batch_results'
            results_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(results_dir / f'pharmaguard_batch_{ts}.json', 'w') as f:
                json.dump({
                    'results': results, 
                    'total': len(results),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Batch save failed: {e}")
        
        _update_progress(task_id, total, total, "completed", {
            'success': True,
            'mode': 'batch',
            'total_processed': len(results),
            'results': results
        })
        
        return {'success': True, 'total_processed': len(results), 'results': results}
        
    except Exception as exc:
        _update_progress(task_id, 0, total, "failed", {'error': str(exc)})
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, max_retries=3)
def optimize_whatif_task(self, smiles, n_variants=5):
    """
    Async what-if optimization task.
    """
    task_id = self.request.id
    
    try:
        import sys
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from routes.pharmaguard import predictor, predictor_cached, _validate_smiles
        from utils.counterfactual_generator import CounterfactualGenerator
        
        _update_progress(task_id, 0, 1, "generating_counterfactuals")
        
        smiles = smiles.strip()
        mol, smiles_err = _validate_smiles(smiles)
        if smiles_err:
            raise ValueError(smiles_err)
        
        cf_gen = CounterfactualGenerator()
        counterfactuals = cf_gen.generate_optimization_candidates(smiles, n_variants=n_variants)
        # Compute baseline toxicity
        baseline_result = predictor.predict(smiles)
        baseline_tox = 0.0
        if 'summary' in baseline_result:
            baseline_tox = float(baseline_result.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)
        
        _update_progress(task_id, 0, len(counterfactuals), "predicting_candidates")
        
        candidates = []
        for i, cf in enumerate(counterfactuals):
            try:
                if predictor_cached:
                    cf_result = predictor_cached.predict_single(cf.modified_smiles)
                else:
                    cf_result = predictor.predict(cf.modified_smiles)
                
                if 'error' in cf_result:
                    continue
                    
                cf_tox = 0.0
                if 'summary' in cf_result:
                    cf_tox = float(cf_result.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)
                    # Skip if candidate increases toxicity significantly
                    toxicity_reduction = baseline_tox - cf_tox
                    if toxicity_reduction < -0.01:
                        continue
                    
                candidates.append({
                    'original_smiles': cf.original_smiles,
                    'modified_smiles': cf.modified_smiles,
                    'modification_type': cf.modification_type.value if hasattr(cf.modification_type, 'value') else str(cf.modification_type),
                    'modification_description': cf.modification_description,
                    'expected_toxicity_change': cf.expected_toxicity_change.value if hasattr(cf.expected_toxicity_change, 'value') else str(cf.expected_toxicity_change),
                    'confidence': cf.confidence,
                    'qed': getattr(cf, 'qed', None),
                    'toxicity_probability': cf_tox,
                    'predictions': cf_result
                })
            except Exception as e:
                print(f"⚠️ CF prediction failed: {e}")
            
            _update_progress(task_id, i + 1, len(counterfactuals), "predicting_candidates")
        
        candidates.sort(key=lambda c: c.get('toxicity_probability', 1.0))
        
        result = {
            'success': True,
            'mode': 'what-if',
            'original_smiles': smiles,
            'candidates': candidates,
            'timestamp': datetime.now().isoformat()
        }
        
        _update_progress(task_id, len(counterfactuals), len(counterfactuals), "completed", result)
        return result
        
    except Exception as exc:
        _update_progress(task_id, 0, 1, "failed", {'error': str(exc)})
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task
def cleanup_old_tasks():
    """Periodic task to clean up old Redis progress keys."""
    try:
        # Scan and delete old progress keys (older than 24 hours)
        pattern = "task:*:progress"
        for key in redis_client.scan_iter(match=pattern):
            ttl = redis_client.ttl(key)
            if ttl == -1:  # No expiry set
                redis_client.expire(key, 86400)
    except Exception as e:
        print(f"Cleanup task error: {e}")


# Schedule periodic cleanup
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'backend.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}