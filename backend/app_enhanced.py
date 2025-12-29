#!/usr/bin/env python3
"""
Enhanced DrugTox-AI Backend API with Rate Limiting
==================================================
New Features:
- RDKit integration for advanced molecular descriptors
- SMILES validation and canonicalization
- 12 toxicity endpoints (expanded from 5)
- API rate limiting
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
from datetime import datetime
import json

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import rate limiter
from utils.rate_limiter import rate_limit, get_rate_limit_info, rate_limiter

# Import caching system
from utils.cache import PredictionCache, CachedPredictionWrapper, prediction_cache

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"])

# Global instances
predictor = None
predictor_cached = None
db_service = None
groq_client = None
cache = prediction_cache

def initialize_services():
    """Initialize all services with enhanced predictor"""
    global predictor, predictor_cached, db_service, groq_client, cache
    
    # Try to use enhanced predictor with RDKit
    try:
        from models.rdkit_predictor import EnhancedDrugToxPredictor
        predictor = EnhancedDrugToxPredictor(use_rdkit=True)
        if predictor.is_loaded:
            predictor_cached = CachedPredictionWrapper(predictor, cache)
            print("✅ Enhanced DrugTox predictor initialized (RDKit enabled)")
            print(f"✅ Prediction caching enabled (TTL: 1 hour, Max size: 10000)")
            print(f"✅ {len(predictor.endpoints)} toxicity endpoints available")
        else:
            print("❌ Enhanced predictor failed to load")
            return False
    except Exception as e:
        print(f"⚠️ Enhanced predictor not available: {e}")
        print("⚠️ Falling back to simple predictor...")
        try:
            from models.simple_predictor import SimpleDrugToxPredictor
            predictor = SimpleDrugToxPredictor()
            if predictor.is_loaded:
                predictor_cached = CachedPredictionWrapper(predictor, cache)
                print("✅ Simple DrugTox predictor initialized")
            else:
                print("❌ Simple predictor failed to load")
                return False
        except Exception as e2:
            print(f"❌ Error initializing simple predictor: {e2}")
            return False
    
    # Initialize Supabase database service
    try:
        from config.supabase import supabase_config
        if supabase_config.test_connection():
            db_service = supabase_config
            print("✅ Supabase database connected successfully")
        else:
            print("⚠️ Database service disabled - connection failed")
            db_service = None
    except Exception as e:
        print(f"⚠️ Database service disabled: {e}")
        db_service = None
    
    # Initialize Groq AI client
    try:
        from config.groq import groq_config
        groq_client = groq_config
        print("✅ Groq AI client initialized successfully")
    except Exception as e:
        print(f"⚠️ Groq AI client initialization failed: {e}")
        groq_client = None
    
    return True


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
@rate_limit(tier='default', cost=0)  # No cost for health checks
def health_check():
    """Health check endpoint"""
    has_rdkit = hasattr(predictor, 'use_rdkit') and predictor.use_rdkit
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'predictor_loaded': predictor is not None and predictor.is_loaded,
        'rdkit_enabled': has_rdkit,
        'cache_enabled': True,
        'cache_stats': cache.get_stats() if cache else None,
        'total_endpoints': len(predictor.endpoints) if predictor else 0,
        'rate_limiting_enabled': True
    })


@app.route('/api/endpoints', methods=['GET'])
@rate_limit(tier='default', cost=1)
def get_endpoints():
    """Get available toxicity endpoints with descriptions"""
    if not predictor or not predictor.is_loaded:
        return jsonify({'error': 'Predictor not loaded'}), 500
    
    # Get endpoint info if available
    endpoint_details = []
    if hasattr(predictor, 'endpoint_info'):
        for endpoint in predictor.endpoints:
            info = predictor.endpoint_info.get(endpoint, {})
            endpoint_details.append({
                'id': endpoint,
                'name': info.get('name', endpoint),
                'description': info.get('description', ''),
                'category': info.get('category', 'Unknown')
            })
    else:
        endpoint_details = [{'id': ep, 'name': ep} for ep in predictor.endpoints]
    
    return jsonify({
        'endpoints': endpoint_details,
        'count': len(predictor.endpoints),
        'description': 'Available toxicity prediction endpoints',
        'rdkit_enabled': hasattr(predictor, 'use_rdkit') and predictor.use_rdkit
    })


@app.route('/api/rate-limit/status', methods=['GET'])
def rate_limit_status():
    """Get current rate limit status for the client"""
    try:
        info = get_rate_limit_info()
        return jsonify({
            'success': True,
            'rate_limit_info': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SMILES VALIDATION ENDPOINT
# ============================================================================

@app.route('/api/validate/smiles', methods=['POST'])
@rate_limit(tier='default', cost=1)
def validate_smiles():
    """Validate and canonicalize SMILES string"""
    try:
        data = request.get_json()
        if not data or 'smiles' not in data:
            return jsonify({'error': 'SMILES string required'}), 400
        
        smiles = data['smiles'].strip()
        
        # Check if predictor has validation method
        if hasattr(predictor, 'validate_smiles'):
            is_valid, canonical_smiles, error_msg = predictor.validate_smiles(smiles)
            
            return jsonify({
                'success': is_valid,
                'original_smiles': smiles,
                'canonical_smiles': canonical_smiles,
                'is_valid': is_valid,
                'error': error_msg,
                'validation_method': 'rdkit' if hasattr(predictor, 'use_rdkit') and predictor.use_rdkit else 'basic',
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Basic validation
            if len(smiles) < 1:
                return jsonify({
                    'success': False,
                    'is_valid': False,
                    'error': 'SMILES string too short'
                }), 400
            
            return jsonify({
                'success': True,
                'original_smiles': smiles,
                'canonical_smiles': smiles,
                'is_valid': True,
                'validation_method': 'basic'
            })
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.route('/api/predict', methods=['POST'])
@rate_limit(tier='prediction', cost=1)
def predict_single():
    """Predict toxicity for a single molecule with validation"""
    try:
        if not predictor or not predictor.is_loaded:
            return jsonify({'error': 'Predictor not initialized'}), 500
        
        data = request.get_json()
        if not data or 'smiles' not in data:
            return jsonify({'error': 'SMILES string required'}), 400
        
        smiles = data['smiles'].strip()
        validate = data.get('validate', True)  # Validate by default
        
        if not smiles:
            return jsonify({'error': 'Empty SMILES string'}), 400
        
        # Get prediction with caching and validation
        if predictor_cached:
            result = predictor_cached.predict_single(smiles)
        else:
            # Use validation if available
            if hasattr(predictor, 'predict_single'):
                result = predictor.predict_single(smiles, validate=validate)
            else:
                result = predictor.predict_single(smiles)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Format response for frontend compatibility
        formatted_result = {
            'molecule': result.get('canonical_smiles', result['smiles']),
            'smiles': result['smiles'],
            'canonical_smiles': result.get('canonical_smiles'),
            'validated': result.get('validated', False),
            'feature_method': result.get('feature_method', 'simple'),
            'timestamp': result['timestamp'],
            'predictions': {},
            'overall_toxicity': result['summary']['overall_assessment'],
            'confidence': result['summary']['recommendation'],
            'toxic_endpoints': result['summary']['toxic_endpoints'],
            'average_probability': result['summary']['average_toxicity_probability'],
            'risk_category': result['summary'].get('risk_category', 'Unknown'),
            'total_endpoints': result['summary'].get('total_endpoints', len(predictor.endpoints))
        }
        
        # Format predictions to match frontend structure
        for endpoint, data in result['endpoints'].items():
            formatted_result['predictions'][endpoint] = {
                'probability': data['probability'],
                'prediction': data['prediction'],
                'confidence': data['confidence'],
                'risk': data['prediction'],
                'endpoint_info': data.get('endpoint_info', {}),
                'roc_auc': data.get('roc_auc', 0.75)
            }
        
        # Generate AI analysis if Groq is available
        if groq_client:
            try:
                ai_analysis = groq_client.analyze_molecule(smiles, result['endpoints'])
                formatted_result['ai_analysis'] = ai_analysis
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}")
                formatted_result['ai_analysis'] = "AI analysis temporarily unavailable."
        
        # Save to database if available
        if db_service:
            try:
                db_service.client.table('predictions').insert({
                    'smiles': smiles,
                    'canonical_smiles': result.get('canonical_smiles'),
                    'molecule_name': data.get('molecule_name'),
                    'endpoints': formatted_result['predictions'],
                    'ai_analysis': formatted_result.get('ai_analysis'),
                    'user_id': data.get('user_id', 'anonymous'),
                    'metadata': {
                        'overall_toxicity': formatted_result['overall_toxicity'],
                        'confidence': formatted_result['confidence'],
                        'toxic_endpoints': formatted_result['toxic_endpoints'],
                        'risk_category': formatted_result['risk_category'],
                        'feature_method': formatted_result['feature_method'],
                        'validated': formatted_result['validated'],
                        'source': 'api',
                        'version': '2.0'
                    }
                }).execute()
                print("✅ Prediction saved to database")
            except Exception as e:
                print(f"⚠️ Database save failed: {e}")
        
        return jsonify(formatted_result)
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/api/predict/batch', methods=['POST'])
@rate_limit(tier='batch', cost=1)
def predict_batch():
    """Predict toxicity for multiple molecules"""
    try:
        if not predictor or not predictor.is_loaded:
            return jsonify({'error': 'Predictor not initialized'}), 500
        
        data = request.get_json()
        if not data or 'smiles_list' not in data:
            return jsonify({'error': 'SMILES list required'}), 400
        
        smiles_list = data['smiles_list']
        if not isinstance(smiles_list, list):
            return jsonify({'error': 'SMILES list must be an array'}), 400
        
        if len(smiles_list) > 100:
            return jsonify({'error': 'Maximum 100 molecules per batch'}), 400
        
        validate = data.get('validate', True)
        
        # Get predictions
        if hasattr(predictor, 'predict_batch'):
            results = predictor.predict_batch(smiles_list, validate=validate)
        else:
            results = predictor.predict_batch(smiles_list)
        
        # Format results
        formatted_results = []
        for result in results:
            if 'error' not in result:
                formatted_results.append({
                    'smiles': result['smiles'],
                    'canonical_smiles': result.get('canonical_smiles'),
                    'validated': result.get('validated', False),
                    'timestamp': result['timestamp'],
                    'predictions': result['endpoints'],
                    'overall_toxicity': result['summary']['overall_assessment'],
                    'confidence': result['summary']['recommendation'],
                    'toxic_endpoints': result['summary']['toxic_endpoints'],
                    'average_probability': result['summary']['average_toxicity_probability'],
                    'risk_category': result['summary'].get('risk_category', 'Unknown')
                })
            else:
                formatted_results.append({
                    'smiles': result.get('smiles', 'unknown'),
                    'error': result['error']
                })
        
        return jsonify({
            'results': formatted_results,
            'total_processed': len(formatted_results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Batch prediction error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Batch prediction failed: {str(e)}'}), 500


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/cache/stats', methods=['GET'])
@rate_limit(tier='default', cost=1)
def get_cache_stats():
    """Get prediction cache statistics"""
    try:
        stats = cache.get_stats()
        stats['cache_size_mb'] = cache.get_cache_size_mb()
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
    except Exception as e:
        print(f"❌ Error getting cache stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
@rate_limit(tier='default', cost=5)  # Higher cost for cache clearing
def clear_cache():
    """Clear prediction cache"""
    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Starting Enhanced DrugTox-AI Backend API")
    print("=" * 70)
    
    if initialize_services():
        print("\n✅ All services initialized successfully")
        print("\n📊 API Features:")
        print("   ✅ RDKit molecular descriptors (200+ features)")
        print("   ✅ SMILES validation and canonicalization")
        print(f"   ✅ {len(predictor.endpoints)} toxicity endpoints")
        print("   ✅ API rate limiting enabled")
        print("   ✅ Prediction caching enabled")
        print("\n🔒 Rate Limits:")
        print("   • Default: 60 req/min")
        print("   • Predictions: 30 req/min")
        print("   • Batch: 10 req/min")
        print("   • AI: 20 req/min")
        print("\n" + "=" * 70)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    else:
        print("\n❌ Failed to initialize services")
        print("❌ Server startup aborted")
