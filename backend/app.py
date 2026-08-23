#!/usr/bin/env python3
"""
DrugTox-AI Clean Backend API
===========================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sys
import traceback
from datetime import datetime
import uuid
import json
from rdkit import Chem
import numpy as np
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import caching system
from utils.cache import PredictionCache, CachedPredictionWrapper, prediction_cache

# Import ADMET rules interpreter
from utils.admet_rules import interpret_admet_predictions, calculate_molecular_properties

# Import MedToXAi feature
try:
    from models.meditox_feature import MedToXAi, analyze_chemical, get_safety_report
    MEDTOXAI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MedToXAi feature not available: {e}")
    MEDTOXAI_AVAILABLE = False

# Import PharmaGuard AI components
try:
    from utils.ood_detector import OODDetector
    OOD_DETECTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ OOD Detector not available: {e}")
    OOD_DETECTOR_AVAILABLE = False

try:
    from utils.triage_engine import TriageEngine
    TRIAGE_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Triage Engine not available: {e}")
    TRIAGE_ENGINE_AVAILABLE = False

try:
    from models.faithfulness_validator import FaithfulnessValidator, ValidationResult
    FAITHFULNESS_VALIDATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Faithfulness Validator not available: {e}")
    FAITHFULNESS_VALIDATOR_AVAILABLE = False

# Import PharmaGuard AI route blueprint (refactor: new endpoints live in routes/)
try:
    from routes.pharmaguard import pharmaguard_bp, init_pharmaguard
    PHARMAGUARD_BP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ PharmaGuard blueprint not available: {e}")
    PHARMAGUARD_BP_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate limiting - protect expensive LLM endpoints
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# PharmaGuard AI blueprint will be registered AFTER initialize_services() runs
# (see bottom of file in __main__ block) so all @route decorators have executed.
limiter.limit("10 per minute")(app.route('/api/report/pdf', methods=['POST']))
limiter.limit("10 per minute")(app.route('/api/report/export', methods=['POST']))

# Global instances
predictor = None
predictor_cached = None  # Cached predictor wrapper
db_service = None
groq_client = None
medtoxai_analyzer = None
cache = prediction_cache  # Use global cache instance
ood_detector = None
triage_engine = None
faithfulness_validator = None
tdc_models = None

def initialize_services():
    """Initialize all services (ML predictor, database, AI, MedToXAi, OOD, Triage, Faithfulness)"""
    global predictor, predictor_cached, db_service, groq_client, medtoxai_analyzer, cache
    global ood_detector, triage_engine, faithfulness_validator, tdc_models
    
    # Initialize ML predictor with caching
    try:
        from models.unified_predictor import UnifiedADMETPredictor
        predictor = UnifiedADMETPredictor()
        if predictor.is_loaded:
            predictor_cached = CachedPredictionWrapper(predictor, cache)
            print("✅ UnifiedADMETPredictor initialized (Attention-GIN + XGBoost)")
            print(f"   Models loaded: {list(predictor.models.keys())}")
        else:
            raise Exception("UnifiedADMETPredictor not loaded")
    except Exception as e:
        print(f"⚠️ UnifiedADMETPredictor failed: {e}")
        predictor = None
        predictor_cached = None

    # Final fallback: rule-based heuristic predictor (no trained weights needed).
    if predictor is None or not predictor.is_loaded:
        try:
            from models.heuristic_predictor import HeuristicFallbackPredictor
            predictor = HeuristicFallbackPredictor()
            if predictor.is_loaded:
                predictor_cached = CachedPredictionWrapper(predictor, cache)
                print("✅ Heuristic fallback predictor active (rule-based, no weights)")
        except Exception as e4:
            print(f"❌ Heuristic fallback failed: {e4}")
            predictor = None
            predictor_cached = None
    
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
    
    # Initialize MedToXAi analyzer
    if MEDTOXAI_AVAILABLE:
        try:
            medtoxai_analyzer = MedToXAi()
            print("✅ MedToXAi analyzer initialized successfully")
        except Exception as e:
            print(f"⚠️ MedToXAi analyzer initialization failed: {e}")
            medtoxai_analyzer = None
    else:
        print("⚠️ MedToXAi feature not available")
        medtoxai_analyzer = None
    
    # Initialize OOD Detector
    if OOD_DETECTOR_AVAILABLE and predictor and predictor.is_loaded:
        try:
            ref_path = os.path.join('results', 'trained_models', 'train_ecfp4.npz')
            ood_detector = OODDetector(predictor, reference_path=ref_path)
            n_ref = len(ood_detector._train_smiles) if ood_detector.fingerprints is not None else 0
            print(f"✅ OOD Detector initialized successfully ({n_ref}-molecule reference set)")
        except Exception as e:
            print(f"⚠️ OOD Detector initialization failed: {e}")
            ood_detector = None
    else:
        print("⚠️ OOD Detector not available or predictor not loaded")
        ood_detector = None
    
    # Initialize Triage Engine
    if TRIAGE_ENGINE_AVAILABLE:
        try:
            triage_engine = TriageEngine()
            print("✅ Triage Engine initialized successfully")
        except Exception as e:
            print(f"⚠️ Triage Engine initialization failed: {e}")
            triage_engine = None
    else:
        print("⚠️ Triage Engine not available")
        triage_engine = None
    
    # Initialize Faithfulness Validator
    if FAITHFULNESS_VALIDATOR_AVAILABLE and predictor and predictor.is_loaded:
        try:
            from utils.counterfactual_generator import CounterfactualGenerator
            cf_gen = CounterfactualGenerator()
            # Get the actual GNN model from unified predictor.
            # The multi-task predictor key for the Tox21 GNN is 'attention_gin'.
            gnn_model = None
            for key in ('attention_gin', 'tox21', 'gin'):
                if hasattr(predictor, 'models') and key in predictor.models:
                    entry = predictor.models[key]
                    gnn_model = entry.get('model') if isinstance(entry, dict) else entry
                    if gnn_model is not None:
                        break

            if gnn_model:
                faithfulness_validator = FaithfulnessValidator(
                    model=gnn_model,
                    counterfactual_generator=cf_gen,
                    faithfulness_threshold=0.70
                )
                print("✅ Faithfulness Validator initialized successfully")
            else:
                print("⚠️ GNN model not available for Faithfulness Validator")
                faithfulness_validator = None
        except Exception as e:
            print(f"⚠️ Faithfulness Validator initialization failed: {e}")
            faithfulness_validator = None
    else:
        print("⚠️ Faithfulness Validator not available or predictor not loaded")
        faithfulness_validator = None

    # Initialize TDC models for hERG, DILI, Ames.
    # Installed TDC exposes these as tasks inside the `Tox` group, not as
    # importable names (`from tdc.single_pred import hERG` raises ImportError).
    # TDC's `Tox` class is a dataset loader; it does NOT ship pretrained models
    # for hERG/DILI/Ames out of the box. `Tox.get_model()` returns None for
    # these endpoints. We gracefully degrade to rule-based predictors using
    # structural alerts and existing models as proxies.
    def _load_tdc_models():
        """Load or create predictors for hERG, DILI, Ames."""
        predictors = {}

        # Try TDC first (will likely return None as no pretrained models)
        tdc_predictors = {}
        try:
            from tdc.single_pred import Tox
            for task_name in ['hERG', 'DILI', 'AMES']:
                task = Tox(name=task_name)
                model = None
                try:
                    model = task.get_model()
                except Exception:
                    model = None
                if model is not None and hasattr(model, 'predict') and callable(model.predict):
                    tdc_predictors[task_name.lower()] = model
        except Exception:
            pass  # TDC not available

        # Rule-based predictor using structural alerts (RDKit)
        def make_rule_predictor(task_name):
            """Create a rule-based predictor for hERG/DILI/Ames."""
            def predict(smiles):
                try:
                    from rdkit import Chem
                    mol = Chem.MolFromSmiles(smiles)
                    if mol is None:
                        return 0.5  # Unknown
                    
                    prob = 0.0
                    alerts = 0
                    
                    if task_name == 'hERG':
                        # hERG: basic tertiary amine, lipophilicity, MW > 350
                        # SMARTS: basic tertiary amine
                        amine_pattern = Chem.MolFromSmarts('[#7;H0;v3](-[#6])-[#6]')
                        if mol.HasSubstructMatch(amine_pattern):
                            alerts += 1
                        # LogP > 3
                        from rdkit.Chem import Descriptors
                        logp = Descriptors.MolLogP(mol)
                        if logp > 3:
                            alerts += 1
                        # MW > 350
                        mw = Descriptors.MolWt(mol)
                        if mw > 350:
                            alerts += 1
                        prob = min(0.2 + alerts * 0.25, 0.95)
                        
                    elif task_name == 'DILI':
                        # DILI: reactive metabolic toxicophores, Rule-of-2
                        from rdkit.Chem import Descriptors
                        # Reactive groups
                        toxicophores = [
                            '[#6]-[#7]-[#6]',  # amine
                            '[#16]-[#6]',  # thiophene
                            '[#7+](=O)[O-]',  # nitro
                            '[#6]=[#8]',  # carbonyl
                        ]
                        for tp in toxicophores:
                            pat = Chem.MolFromSmarts(tp)
                            if pat and mol.HasSubstructMatch(pat):
                                alerts += 1
                        # Rule of 2: LogP > 3 and TPSA < 75
                        logp = Descriptors.MolLogP(mol)
                        tpsa = Descriptors.TPSA(mol)
                        if logp > 3 and tpsa < 75:
                            alerts += 2
                        prob = min(0.15 + alerts * 0.2, 0.9)
                        
                    elif task_name == 'AMES':
                        # Ames: Ashby-Tennant alerts
                        # Aromatic nitro, aromatic amines, epoxides, alkyl halides
                        ames_alerts = [
                            '[#7+](=O)[O-]',  # nitro
                            '[#7;H2]-[#6]',  # primary aromatic amine
                            '[#6]1[#6][#6][#6][#8]1',  # epoxide
                            '[#6]-[#9|#17|#35|#53]',  # alkyl halides
                        ]
                        for tp in ames_alerts:
                            pat = Chem.MolFromSmarts(tp)
                            if pat and mol.HasSubstructMatch(pat):
                                alerts += 1
                        prob = min(0.1 + alerts * 0.25, 0.95)
                    
                    return prob
                except Exception:
                    return 0.5
            
            return predict

        # Create predictors for each endpoint
        predictors = {
            'herg': tdc_predictors.get('herg') or make_rule_predictor('hERG'),
            'dili': tdc_predictors.get('dili') or make_rule_predictor('DILI'),
            'ames': tdc_predictors.get('ames') or make_rule_predictor('AMES'),
        }
        
        return predictors

    tdc_models = None
    try:
        import threading
        _result = {}
        _loader = threading.Thread(target=lambda: _result.setdefault('m', _load_tdc_models()), daemon=True)
        _loader.start()
        _loader.join(timeout=15)  # never block startup longer than 15s
        if _loader.is_alive():
            print("⚠️ TDC models initialization timed out (offline?), skipping")
            tdc_models = None
        else:
            tdc_models = _result.get('m')
            if tdc_models is not None:
                print("✅ TDC models (hERG, DILI, Ames) initialized successfully")
    except Exception as e:
        print(f"⚠️ TDC models initialization failed: {e}")
        tdc_models = None

    # Inject shared services into the PharmaGuard blueprint (refactor)
    if PHARMAGUARD_BP_AVAILABLE:
        init_pharmaguard(
            predictor=predictor,
            predictor_cached=predictor_cached,
            cache=cache,
            db_service=db_service,
            groq_client=groq_client,
            ood_detector=ood_detector,
            triage_engine=triage_engine,
            faithfulness_validator=faithfulness_validator,
            tdc_models=tdc_models,
        )

    return True

@app.route('/api/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint"""
    loaded_models = []
    model_source = 'none'
    if predictor is not None and getattr(predictor, 'is_loaded', False):
        loaded_models = list(getattr(predictor, 'models', {}).keys())
        model_source = getattr(predictor, 'model_source', 'trained')

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'predictor_loaded': predictor is not None and predictor.is_loaded,
        'model_source': model_source,
        'models_loaded': loaded_models,
        'models_loaded_count': len(loaded_models),
        'total_models': len(loaded_models) if loaded_models else 0,
        'chemberta_loaded': bool(getattr(predictor, 'chemberta_loaded', False)),
        'cache_enabled': True,
        'cache_stats': cache.get_stats() if cache else None
    })

@app.route('/api/config/status', methods=['GET'])
def config_status():
    """Check API configuration status"""
    try:
        groq_configured = groq_client is not None
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        return jsonify({
            'success': True,
            'groq': {
                'configured': groq_configured,
                'api_key_set': groq_api_key is not None and len(groq_api_key.strip()) > 0,
                'instructions': {
                    'file': 'backend/.env',
                    'variable': 'GROQ_API_KEY',
                    'example': 'GROQ_API_KEY=gsk_your_api_key_here',
                    'steps': [
                        '1. Navigate to the Medtox/backend/ folder',
                        '2. Create or open the .env file',
                        '3. Add or update: GROQ_API_KEY=your_groq_api_key',
                        '4. Restart the backend server'
                    ]
                }
            },
            'models': {
                'loaded': predictor is not None and predictor.is_loaded,
                'count': len(predictor.models) if predictor and predictor.is_loaded else 0
            }
        })
    except Exception as e:
        print(f"❌ Error checking config status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats', methods=['GET'])
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

@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    """Get available toxicity endpoints"""
    if not predictor or not predictor.is_loaded:
        return jsonify({'error': 'Predictor not loaded'}), 500
    
    return jsonify({
        'endpoints': list(predictor.models.keys()),
        'count': len(predictor.models),
        'description': 'Available toxicity prediction endpoints'
    })

@app.route('/api/predict', methods=['POST'])
def predict_single():
    """Predict toxicity for a single molecule with AI analysis"""
    try:
        if not predictor or not predictor.is_loaded:
            return jsonify({'error': 'Predictor not initialized'}), 500
        
        data = request.get_json()
        if not data or 'smiles' not in data:
            return jsonify({'error': 'SMILES string required'}), 400
        
        smiles = data['smiles'].strip()
        if not smiles:
            return jsonify({'error': 'Empty SMILES string'}), 400

        # Validate SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return jsonify({'error': 'Invalid SMILES', 'code': 'INVALID_SMILES', 'example': 'CC(=O)Oc1ccccc1C(=O)O'}), 400
       
       # Get prediction with caching enabled
        if predictor_cached:
            result = predictor_cached.predict_single(smiles)
        else:
            result = predictor.predict(smiles)
        
        # Handle UnifiedADMETPredictor format (has 'predictions' key at top level)
        if 'predictions' in result and 'summary' in result:
            return jsonify({
                'smiles': result.get('smiles', smiles),
                'predictions': result['predictions'],
                'tox21': result.get('tox21', {}),
                'summary': result.get('summary', {}),
                'timestamp': result.get('timestamp'),
                'overall_toxicity': result.get('summary', {}).get('overall_assessment', 'Unknown'),
                'avg_probability': result.get('summary', {}).get('average_toxicity_probability', 0.5),
                'num_endpoints': result.get('summary', {}).get('num_endpoints', 0)
            })
        
        # Handle SimpleDrugToxPredictor format (has 'endpoints' key)
        if 'endpoints' in result:
            # Convert to expected format for API response
            return jsonify({
                'smiles': result.get('smiles', smiles),
                'predictions': result['endpoints'],
                'summary': result.get('summary', {}),
                'timestamp': result.get('timestamp'),
                'overall_toxicity': result.get('summary', {}).get('overall_assessment', 'Unknown'),
                'avg_probability': result.get('summary', {}).get('average_toxicity_probability', 0.5)
            })
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        # Separate toxicity and ADMET models
        toxicity_models = ['tox21', 'clintox']
        admet_models = ['bbbp', 'caco2', 'clearance', 'hlm_clint']
        
        # Calculate toxicity statistics (classification models only)
        tox_prob_sum = 0
        tox_count = 0
        toxic_endpoints = 0
        
        for model_id in toxicity_models:
            if model_id in result and 'error' not in result[model_id]:
                model_result = result[model_id]
                if 'probability' in model_result:
                    tox_prob_sum += model_result['probability']
                    tox_count += 1
                    if model_result.get('prediction', 0) == 1:
                        toxic_endpoints += 1
        
        avg_tox_probability = tox_prob_sum / tox_count if tox_count > 0 else 0
        overall_toxicity = "High Risk" if avg_tox_probability > 0.7 else "Medium Risk" if avg_tox_probability > 0.3 else "Low Risk"
        
        # Calculate ADMET property summary
        admet_summary = {}
        for model_id in admet_models:
            if model_id in result and 'error' not in result[model_id]:
                model_result = result[model_id]
                
                if model_id == 'bbbp':
                    # BBB penetration (classification)
                    prob = model_result.get('probability', 0)
                    pred = model_result.get('prediction', 0)
                    admet_summary['bbb_penetration'] = {
                        'value': prob,
                        'label': model_result.get('label', 'BBB Permeable' if pred == 1 else 'Non-permeable'),
                        'confidence': prob,
                        'interpretation': 'Crosses blood-brain barrier' if pred == 1 else 'Does not cross BBB'
                    }
                elif model_id == 'caco2':
                    # Caco-2 permeability (regression, log scale)
                    raw_value = model_result.get('prediction', model_result.get('value', 0))
                    # Caco-2 log Papp thresholds: >-5.15 = high, -5.15 to -6.0 = medium, <-6.0 = low
                    if raw_value > -5.15:
                        label = 'High'
                        interpretation = 'Good intestinal absorption'
                    elif raw_value > -6.0:
                        label = 'Medium'
                        interpretation = 'Moderate intestinal absorption'
                    else:
                        label = 'Low'
                        interpretation = 'Poor intestinal absorption'
                    
                    admet_summary['caco2_permeability'] = {
                        'log_value': round(raw_value, 3),
                        'label': label,
                        'unit': 'log Papp (cm/s)',
                        'interpretation': interpretation
                    }
                elif model_id == 'clearance':
                    # Hepatocyte clearance (regression, log scale -> linear via exp())
                    raw_value = model_result.get('prediction', model_result.get('value', 0))
                    linear_value = model_result.get('linear_value', np.exp(raw_value))
                    
                    if linear_value > 20:
                        label = 'High'
                        interpretation = 'Rapid hepatic clearance'
                    elif linear_value > 5:
                        label = 'Medium'
                        interpretation = 'Moderate hepatic clearance'
                    else:
                        label = 'Low'
                        interpretation = 'Slow hepatic clearance'
                    
                    admet_summary['hepatic_clearance'] = {
                        'log_value': round(raw_value, 3),
                        'linear_value': round(linear_value, 2),
                        'label': label,
                        'unit': 'mL/min/kg',
                        'interpretation': interpretation
                    }
                elif model_id == 'hlm_clint':
                    # HLM intrinsic clearance (regression, log scale -> linear via exp())
                    raw_value = model_result.get('prediction', model_result.get('value', 0))
                    linear_value = model_result.get('linear_value', np.exp(raw_value))
                    
                    if linear_value > 10:
                        label = 'High'
                        interpretation = 'High metabolic clearance'
                    elif linear_value > 2:
                        label = 'Medium'
                        interpretation = 'Moderate metabolic clearance'
                    else:
                        label = 'Low'
                        interpretation = 'Low metabolic clearance'
                    
                    admet_summary['hlm_clearance'] = {
                        'log_value': round(raw_value, 3),
                        'linear_value': round(linear_value, 2),
                        'label': label,
                        'unit': 'μL/min/mg protein',
                        'interpretation': interpretation
                    }
        
        # Format response for frontend compatibility
        formatted_result = {
            'molecule': smiles,
            'smiles': smiles,
            'timestamp': str(datetime.now()),
            'predictions': {},
            'overall_toxicity': overall_toxicity,
            'toxicity_confidence': f"{avg_tox_probability:.2%}",
            'toxic_endpoints': toxic_endpoints,
            'average_toxicity_probability': avg_tox_probability,
            'admet_properties': admet_summary
        }
        
        # Format predictions to match frontend structure
        for model_id, model_result in result.items():
            if 'error' not in model_result:
                # For clintox, use clinical_tox_prob if available
                prob = model_result.get('probability', model_result.get('clinical_tox_prob', model_result.get('value', 0)))
                
                formatted_result['predictions'][model_id] = {
                    'probability': prob,
                    'prediction': model_result.get('prediction', 0),
                    'confidence': prob,
                    'risk': model_result.get('label', 'Unknown'),
                    'type': model_result.get('type', 'unknown')
                }
            else:
                formatted_result['predictions'][model_id] = {
                    'error': model_result['error']
                }
        
        # Apply ADMET rule-based interpretation
        admet_interpretation = interpret_admet_predictions(smiles, result, is_approved_drug=False)
        formatted_result['admet_analysis'] = admet_interpretation
        formatted_result['molecular_properties'] = admet_interpretation.get('properties', {})
        formatted_result['drug_likeness'] = admet_interpretation.get('drug_likeness', {})
        
        # Generate AI analysis if Groq is available
        ai_analysis = None
        if groq_client:
            try:
                # Include ADMET interpretation in AI analysis
                ai_analysis = groq_client.analyze_molecule(smiles, result, admet_interpretation)
                formatted_result['ai_analysis'] = ai_analysis
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}")
                formatted_result['ai_analysis'] = "AI analysis temporarily unavailable."
        
        # Save to database if available
        if db_service:
            try:
                db_service.client.table('predictions').insert({
                    'smiles': smiles,
                    'molecule_name': data.get('molecule_name'),
                    'endpoints': formatted_result['predictions'],
                    'ai_analysis': ai_analysis,
                    'user_id': data.get('user_id', 'anonymous'),
                    'metadata': {
                        'overall_toxicity': formatted_result['overall_toxicity'],
                        'confidence': formatted_result['confidence'],
                        'toxic_endpoints': formatted_result['toxic_endpoints'],
                        'source': 'api',
                        'version': '1.0'
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

        # Validate each SMILES
        for i, smi in enumerate(smiles_list):
            if not isinstance(smi, str):
                return jsonify({'error': f'SMILES at index {i} is not a string', 'code': 'INVALID_SMILES_TYPE'}), 400
            mol = Chem.MolFromSmiles(smi.strip())
            if mol is None:
                return jsonify({'error': f'Invalid SMILES at index {i}: {smi}', 'code': 'INVALID_SMILES', 'example': 'CC(=O)Oc1ccccc1C(=O)O'}), 400
       
       # Get predictions
        results = predictor.predict_batch(smiles_list)
        
        # Format results
        formatted_results = []
        for result in results:
            if 'error' not in result:
                formatted_results.append({
                    'smiles': result['smiles'],
                    'timestamp': result['timestamp'],
                    'predictions': result['endpoints'],
                    'overall_toxicity': result['summary']['overall_assessment'],
                    'confidence': result['summary']['recommendation'],
                    'toxic_endpoints': result['summary']['toxic_endpoints'],
                    'average_probability': result['summary']['average_toxicity_probability']
                })
            else:
                formatted_results.append({
                    'smiles': result.get('smiles', 'unknown'),
                    'error': result['error']
                })
        
        # Save results locally instead of Supabase
        try:
            import json
            import os
            from pathlib import Path
            
            # Create results directory if it doesn't exist
            results_dir = Path(__file__).parent / 'batch_results'
            results_dir.mkdir(exist_ok=True)
            
            # Save to JSON file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f'batch_results_{timestamp}.json'
            
            with open(results_file, 'w') as f:
                json.dump({
                    'results': formatted_results,
                    'total_processed': len(formatted_results),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"✅ Saved batch results to {results_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not save batch results locally: {e}")
        
        return jsonify({
            'results': formatted_results,
            'total_processed': len(formatted_results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Batch prediction error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Batch prediction failed: {str(e)}'}), 500

@app.route('/api/analyze-image-vision', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_image_vision():
    """AI-powered vision analysis using Groq Vision + OCR fallback"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'image_base64' not in data:
            return jsonify({'error': 'Base64 image data required'}), 400
        
        image_base64 = data['image_base64']
        image_name = data.get('image_name', 'unknown')
        
        # AI prompt for vision-based chemical analysis
        ai_prompt = """Analyze this image which may contain:
- Chemical structures or molecular diagrams
- Medicine labels with ingredient lists
- SMILES notation or chemical formulas
- Drug composition information

Please extract and provide:
1. All visible chemical compounds, ingredients, or drug names
2. SMILES notation if any chemical structures are visible
3. Any molecular formulas or chemical formulas
4. Active ingredients and their quantities if visible

Respond in JSON format:
{
  "ingredients": ["list of identified chemicals/ingredients"],
  "smiles": ["SMILES strings for any structures found"],
  "formulas": ["chemical formulas if present"],
  "insights": "detailed analysis of what's in the image",
  "confidence": "high/medium/low"
}"""
        
        try:
            # Try Groq Vision API (llama-3.2-90b-vision-preview)
            response = groq_client.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": ai_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content.strip()
            
        except Exception as vision_error:
            print(f"⚠️ Vision API failed: {vision_error}")
            # Return user-friendly message
            return jsonify({
                'success': False,
                'error': 'Vision AI temporarily unavailable',
                'message': 'Please use the OCR text extraction feature in the frontend',
                'fallback': 'ocr'
            }), 200
        
        # Parse JSON response
        try:
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0].strip()
            
            result = json.loads(ai_response)
        except:
            result = {
                'ingredients': [],
                'smiles': [],
                'formulas': [],
                'insights': ai_response,
                'confidence': 'medium'
            }
        
        return jsonify({
            'success': True,
            'image_name': image_name,
            'method': 'vision_api',
            'ingredients': result.get('ingredients', []),
            'smiles': result.get('smiles', []),
            'formulas': result.get('formulas', []),
            'insights': result.get('insights', 'Analysis complete'),
            'confidence': result.get('confidence', 'medium'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Vision analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Vision analysis failed: {str(e)}'}), 500

@app.route('/api/analyze-chemical-text', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_chemical_text():
    """Enhanced AI-powered analysis of OCR text to identify chemical components and generate AI report"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content required'}), 400
        
        extracted_text = data['text']
        image_name = data.get('image_name', 'unknown')
        
        print(f"🔬 Analyzing chemical text from {image_name}: {extracted_text[:100]}...")
        
        # Enhanced AI prompt for chemical component analysis
        ai_prompt = f"""You are an expert chemical analyst and pharmacist. Analyze the following OCR-extracted text from a chemical/pharmaceutical image and identify chemical components, generate SMILES, and provide a comprehensive AI report.

EXTRACTED TEXT FROM IMAGE:
{extracted_text}

TASK: Identify chemical compounds, drugs, and active ingredients. Provide SMILES notation and detailed analysis.

INSTRUCTIONS:
1. Look for chemical names, drug names, active ingredients
2. Ignore excipients, colors, preservatives, and inactive ingredients  
3. Generate or provide correct SMILES notation for identified chemicals
4. Provide detailed AI analysis of the chemical components
5. Include safety considerations and chemical properties

COMMON CHEMICAL SMILES DATABASE:
- Paracetamol/Acetaminophen: CC(=O)Nc1ccc(O)cc1
- Aspirin: CC(=O)Oc1ccccc1C(=O)O
- Ibuprofen: CC(C)Cc1ccc(cc1)C(C)C(=O)O
- Caffeine: CN1C=NC2=C1C(=O)N(C(=O)N2C)C
- Sodium Chloride: [Na+].[Cl-]
- Glucose: C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O
- Ethanol: CCO
- Benzene: c1ccccc1
- Acetone: CC(=O)C
- Methanol: CO

RESPOND IN JSON FORMAT:
{{
  "success": true,
  "primary_ingredient": "main chemical/drug name",
  "ingredients": ["list of chemical compounds found"],
  "smiles": ["SMILES notation for each compound"],
  "formulas": ["molecular formulas"],
  "quantities": ["concentrations or amounts mentioned"],
  "confidence": "high/medium/low",
  "ai_report": "Detailed chemical analysis report including: molecular structure insights, pharmacological properties, safety considerations, potential interactions, and chemical classification. Be comprehensive and scientific.",
  "safety_notes": ["important safety considerations"],
  "chemical_class": ["classification of compounds (e.g., analgesic, antibiotic, etc.)"]
}}

Be thorough in your analysis and provide educational insights about the chemical components."""
        
        # Call Groq AI for chemical analysis
        response = groq_client.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert chemical analyst and pharmacist specializing in identifying chemical compounds from text and providing comprehensive analysis. Always respond with valid JSON and provide detailed, educational chemical insights."
                },
                {"role": "user", "content": ai_prompt}
            ],
            temperature=0.1,  # Low temperature for precise analysis
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"✅ Groq AI response received: {ai_response[:200]}...")
        
        # Parse JSON response
        try:
            result = json.loads(ai_response)
            print(f"✅ JSON parsed successfully: {list(result.keys())}")
        except Exception as parse_error:
            print(f"⚠️ JSON parsing failed: {parse_error}")
            print(f"Raw AI response: {ai_response}")
            # Fallback response
            result = {
                'success': False,
                'primary_ingredient': '',
                'ingredients': [],
                'smiles': [],
                'formulas': [],
                'quantities': [],
                'confidence': 'low',
                'ai_report': f'Chemical analysis could not be completed. Raw extracted text: {extracted_text}',
                'safety_notes': ['Unable to analyze - please verify chemical components manually'],
                'chemical_class': []
            }
        
        return jsonify({
            'success': result.get('success', True),
            'image_name': image_name,
            'method': 'ocr_chemical_analysis',
            'raw_text': extracted_text[:500],  # Include raw text for reference
            'primary_ingredient': result.get('primary_ingredient', ''),
            'ingredients': result.get('ingredients', []),
            'smiles': result.get('smiles', []),
            'formulas': result.get('formulas', []),
            'quantities': result.get('quantities', []),
            'confidence': result.get('confidence', 'medium'),
            'ai_report': result.get('ai_report', 'Chemical analysis completed'),
            'safety_notes': result.get('safety_notes', []),
            'chemical_class': result.get('chemical_class', []),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Chemical text analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Chemical analysis failed: {str(e)}'}), 500
@app.route('/api/analyze-image-text', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_image_text():
    """Enhanced AI-powered analysis of OCR extracted text to identify ingredients and SMILES"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content required'}), 400
        
        extracted_text = data['text']
        image_name = data.get('image_name', 'unknown')
        
        # Common drug SMILES database for reference
        common_drugs = {
            'paracetamol': 'CC(=O)Nc1ccc(O)cc1',
            'acetaminophen': 'CC(=O)Nc1ccc(O)cc1',
            'aspirin': 'CC(=O)Oc1ccccc1C(=O)O',
            'ibuprofen': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
            'caffeine': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
            'diphenhydramine': 'CN(C)CCOC(c1ccccc1)c1ccccc1',
            'cetirizine': 'O=C(O)COCCN1CCN(CC1)C(c1ccccc1)c1ccc(Cl)cc1',
            'amoxicillin': 'CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N2C1C(=O)O'
        }
        
        # Enhanced AI prompt for handling OCR errors and extracting chemical information
        ai_prompt = f"""You are an expert pharmaceutical AI that specializes in extracting chemical information from noisy OCR text. The text below was extracted from a medicine label using OCR and contains many spelling errors and formatting issues.

NOISY OCR TEXT FROM MEDICINE LABEL:
{extracted_text}

YOUR MISSION: Extract meaningful chemical/pharmaceutical information despite OCR errors.

CRITICAL SKILLS NEEDED:
1. **OCR ERROR CORRECTION**: Fix common OCR mistakes
   - "Paracetamol" may appear as: "Faracetamol", "Paracetaol", "Para cetamol", "P aracetamol"
   - "Ibuprofen" may appear as: "lbuprofen", "Ibu profen", "lbuprofan"
   - "Aspirin" may appear as: "Asp irin", "Asplrin", "A spirin"
   - "Diphenhydramine" may appear as: "Diphenhydram ine", "Diph enhydramine"
   - Numbers/dosages: "500mg" may appear as "S00mg", "5O0mg", "500 mg"

2. **ACTIVE INGREDIENT DETECTION**: Look for pharmaceutical terms even with errors:
   - Active ingredient sections
   - Drug names (even misspelled)
   - Chemical names or brand names
   - Ignore: colors, preservatives, excipients, inactive ingredients

3. **QUANTITY EXTRACTION**: Find dosage amounts:
   - mg, g, mcg, IU, mL patterns
   - Even with OCR errors like "S00mg" = "500mg"

4. **SMART CHEMICAL MATCHING**: Use fuzzy matching for common drugs:

DRUG DATABASE WITH SMILES:
- Paracetamol/Acetaminophen: CC(=O)Nc1ccc(O)cc1
- Aspirin: CC(=O)Oc1ccccc1C(=O)O  
- Ibuprofen: CC(C)Cc1ccc(cc1)C(C)C(=O)O
- Caffeine: CN1C=NC2=C1C(=O)N(C(=O)N2C)C
- Diphenhydramine: CN(C)CCOC(c1ccccc1)c1ccccc1
- Cetirizine: O=C(O)COCCN1CCN(CC1)C(c1ccccc1)c1ccc(Cl)cc1
- Loratadine: CCOC(=O)N1CCC(CC1)C(c2ccc(Cl)cc2)c3ccccn3
- Pseudoephedrine: CC(C)NC[C@@H](c1ccc(O)cc1)O
- Dextromethorphan: CN1CC[C@]2(CCCN2)[C@@H]1[C@@H]3c4ccccc4CC[C@H]3O

RESPONSE FORMAT (JSON only, no markdown):
{{
  "primary_ingredient": "corrected standardized drug name",
  "ingredients": ["list of active ingredients found"],
  "smiles": ["SMILES strings for identified drugs"],
  "formulas": ["molecular formulas if determinable"],
  "quantities": ["dosage amounts found"],
  "insights": "brief analysis of what medicine this likely is",
  "confidence": "high/medium/low",
  "ocr_corrections": ["original_text -> corrected_text"]
}}

EXAMPLE - OCR text "Drug Facts Active lngredient Faracetamol S00mg" should return:
{{
  "primary_ingredient": "Paracetamol",
  "ingredients": ["Paracetamol"],
  "smiles": ["CC(=O)Nc1ccc(O)cc1"],
  "formulas": ["C8H9NO2"],
  "quantities": ["500mg"],
  "insights": "Pain reliever and fever reducer containing acetaminophen",
  "confidence": "high",
  "ocr_corrections": ["Faracetamol -> Paracetamol", "S00mg -> 500mg"]
}}"""
        
        # Call Groq AI with enhanced model
        response = groq_client.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert pharmaceutical chemist. Your ONLY job is to identify ACTIVE pharmaceutical ingredients from medicine labels and provide their SMILES notation. IGNORE excipients, colors, and inactive ingredients. Respond ONLY with valid JSON, no markdown formatting."
                },
                {"role": "user", "content": ai_prompt}
            ],
            temperature=0.05,  # Very low temperature for precise extraction
            max_tokens=1000,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(ai_response)
        except Exception as parse_error:
            print(f"⚠️ JSON parsing failed: {parse_error}")
            print(f"Raw AI response: {ai_response}")
            
            # Enhanced fallback: Try to extract drug name from OCR text with error correction
            extracted_text_lower = extracted_text.lower()
            fallback_ingredient = None
            fallback_smiles = None
            
            # Enhanced OCR error patterns for common drugs
            drug_patterns = {
                'paracetamol': ['paracetamol', 'paracetaol', 'faracetamol', 'para cetamol', 'p aracetamol', 'acetaminophen'],
                'ibuprofen': ['ibuprofen', 'ibu profen', 'lbuprofen', 'ibuprofan', 'lbuprofan'],
                'aspirin': ['aspirin', 'asp irin', 'asplrin', 'a spirin'],
                'caffeine': ['caffeine', 'caff eine', 'cafeine', 'coffeine'],
                'diphenhydramine': ['diphenhydramine', 'diphenhydram ine', 'diph enhydramine', 'diphenhydram'],
                'cetirizine': ['cetirizine', 'cetir izine', 'cetirzine'],
                'amoxicillin': ['amoxicillin', 'amox icillin', 'amoxi cillin']
            }
            
            # Check for drug patterns with OCR error tolerance
            for drug, patterns in drug_patterns.items():
                for pattern in patterns:
                    if pattern in extracted_text_lower or any(part in extracted_text_lower for part in pattern.split()):
                        fallback_ingredient = drug.capitalize()
                        fallback_smiles = common_drugs.get(drug)
                        break
                if fallback_ingredient:
                    break
            
            # Also check original common_drugs for exact matches
            if not fallback_ingredient:
                for drug, smiles in common_drugs.items():
                    if drug in extracted_text_lower:
                        fallback_ingredient = drug.capitalize()
                        fallback_smiles = smiles
                        break
            
            result = {
                'primary_ingredient': fallback_ingredient or '',
                'ingredients': [fallback_ingredient] if fallback_ingredient else [],
                'smiles': [fallback_smiles] if fallback_smiles else [],
                'formulas': [],
                'quantities': [],
                'insights': f"Fallback detection: {fallback_ingredient or 'No drug identified'}" if fallback_ingredient else ai_response,
                'confidence': 'medium' if fallback_ingredient else 'low'
            }
        
        # Enhanced validation: ensure SMILES is present with better error handling
        if not result.get('smiles') or len(result.get('smiles', [])) == 0:
            # Try enhanced fallback detection with OCR error patterns
            extracted_text_lower = extracted_text.lower()
            
            # Enhanced OCR error patterns
            drug_patterns = {
                'paracetamol': ['paracetamol', 'paracetaol', 'faracetamol', 'para cetamol', 'p aracetamol', 'acetaminophen'],
                'ibuprofen': ['ibuprofen', 'ibu profen', 'lbuprofen', 'ibuprofan', 'lbuprofan'],
                'aspirin': ['aspirin', 'asp irin', 'asplrin', 'a spirin'],
                'caffeine': ['caffeine', 'caff eine', 'cafeine', 'coffeine'],
                'diphenhydramine': ['diphenhydramine', 'diphenhydram ine', 'diph enhydramine', 'diphenhydram'],
                'cetirizine': ['cetirizine', 'cetir izine', 'cetirzine'],
                'amoxicillin': ['amoxicillin', 'amox icillin', 'amoxi cillin']
            }
            
            for drug, patterns in drug_patterns.items():
                for pattern in patterns:
                    if pattern in extracted_text_lower:
                        result['primary_ingredient'] = drug.capitalize()
                        result['ingredients'] = [drug.capitalize()]
                        result['smiles'] = [common_drugs.get(drug)]
                        result['confidence'] = 'high'
                        result['insights'] = f"Detected {drug.capitalize()} via enhanced pattern matching"
                        break
                if result.get('smiles'):
                    break
            
            # Final fallback to original method
            if not result.get('smiles'):
                for drug, smiles in common_drugs.items():
                    if drug in extracted_text_lower:
                        result['primary_ingredient'] = drug.capitalize()
                        result['ingredients'] = [drug.capitalize()]
                        result['smiles'] = [smiles]
                        result['confidence'] = 'high'
                        result['insights'] = f"Detected {drug.capitalize()} via text matching"
                        break
        
        return jsonify({
            'success': True,
            'image_name': image_name,
            'raw_text': extracted_text,
            'primary_ingredient': result.get('primary_ingredient', ''),
            'ingredients': result.get('ingredients', []),
            'smiles': result.get('smiles', []),
            'formulas': result.get('formulas', []),
            'quantities': result.get('quantities', []),
            'insights': result.get('insights', 'Analysis complete'),
            'confidence': result.get('confidence', 'medium'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Image text analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/ai/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def ai_analyze_molecule():
    """Get AI analysis for a molecule and its toxicity results"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'smiles' not in data or 'toxicity_results' not in data:
            return jsonify({'error': 'SMILES and toxicity results required'}), 400
        
        smiles = data['smiles'].strip()
        toxicity_results = data['toxicity_results']
        # Validate SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return jsonify({'error': 'Invalid SMILES string', 'example': 'CC(=O)Oc1ccccc1C(=O)O'}), 400
        
        analysis = groq_client.analyze_molecule(smiles, toxicity_results)
        
        return jsonify({
            'smiles': smiles,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"❌ AI analysis error: {e}")
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/ai/explain/<endpoint_id>', methods=['GET'])
@limiter.limit("10 per minute")
def ai_explain_endpoint(endpoint_id):
    """Get AI explanation of a toxicity endpoint"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        explanation = groq_client.explain_endpoint(endpoint_id)
        
        return jsonify({
            'endpoint_id': endpoint_id,
            'explanation': explanation,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ AI explanation error: {e}")
        return jsonify({'error': f'AI explanation failed: {str(e)}'}), 500

@app.route('/api/ai/suggest-modifications', methods=['POST'])
@limiter.limit("5 per minute")
def ai_suggest_modifications():
    """Get AI suggestions for molecular modifications to reduce toxicity"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'smiles' not in data or 'toxic_endpoints' not in data:
            return jsonify({'error': 'SMILES and toxic endpoints required'}), 400
        
        smiles = data['smiles'].strip()
        toxic_endpoints = data['toxic_endpoints']
        # Validate SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return jsonify({'error': 'Invalid SMILES string', 'example': 'CC(=O)Oc1ccccc1C(=O)O'}), 400
        
        suggestions = groq_client.suggest_modifications(smiles, toxic_endpoints)
        
        return jsonify({
            'smiles': smiles,
            'toxic_endpoints': toxic_endpoints,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"❌ AI suggestions error: {e}")
        return jsonify({'error': f'AI suggestions failed: {str(e)}'}), 500

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """General AI chat endpoint for ChemBio questions"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Create a specialized chemistry/biology AI assistant
        messages = [
            {
                "role": "system",
                "content": """You are an expert ChemBio AI assistant with deep knowledge in chemistry, biology, toxicology, and pharmaceutical sciences.

EXPERTISE AREAS:
- Molecular structures, SMILES notation, and chemical properties
- Drug mechanisms of action and pharmacology (ADME, PK/PD)
- Toxicology and safety assessment (endpoints, testing methods)
- Computational chemistry and QSAR modeling
- Protein structure/function and enzyme kinetics
- Drug discovery and development processes
- Regulatory science and risk assessment

RESPONSE STYLE:
- Provide detailed, scientifically accurate explanations
- Use clear structure with headers, bullet points, and emojis
- Include specific examples and technical details when appropriate
- Explain complex concepts in accessible language
- Always mention when to consult healthcare professionals for medical advice

TOXICITY ENDPOINTS (key focus areas):
- NR-AR-LBD: Nuclear Receptor Androgen Receptor Ligand Binding Domain
- NR-AhR: Nuclear Receptor Aryl Hydrocarbon Receptor
- SR-MMP: Stress Response Mitochondrial Membrane Potential  
- NR-ER-LBD: Nuclear Receptor Estrogen Receptor Ligand Binding Domain
- NR-AR: Nuclear Receptor Androgen Receptor

Format responses with clear sections, technical accuracy, and educational value."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        response = groq_client.chat_completion(messages, temperature=0.7, max_tokens=1200)
        
        return jsonify({
            'message': user_message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ AI chat error: {e}")
        return jsonify({'error': f'AI chat failed: {str(e)}'}), 500

@app.route('/api/chat/ask', methods=['POST'])
def chat_ask():
    """Dedicated Chat page endpoint - specialized chemistry/toxicology AI assistant"""
    try:
        if not groq_client:
            return jsonify({'error': 'AI chat service not available'}), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message required'}), 400
        
        user_message = data['message'].strip()
        context = data.get('context', 'chemistry_toxicology')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Enhanced system prompt for dedicated chat page
        system_prompt = """You are MedToXAi Assistant, an expert AI specialized in chemistry, toxicology, pharmaceutical sciences, and drug discovery.

🧪 **CORE EXPERTISE:**
- Molecular structures, SMILES notation, and chemical properties analysis
- Toxicology endpoints and comprehensive safety assessment methodologies
- Drug discovery processes, ADME properties, and pharmacokinetic modeling
- Computational chemistry, QSAR modeling, and molecular descriptor analysis
- Protein-drug interactions, mechanism of action, and binding affinity studies
- Regulatory toxicology, risk assessment frameworks, and compliance guidelines

🎯 **SPECIALIZED KNOWLEDGE AREAS:**
- **Toxicity Endpoints**: NR-AR-LBD (Androgen Receptor), NR-AhR (Aryl Hydrocarbon Receptor), SR-MMP (Mitochondrial Membrane Potential), NR-ER-LBD (Estrogen Receptor), NR-AR (Androgen Receptor)
- **ADME Properties**: Absorption kinetics, Distribution patterns, Metabolism pathways, Excretion mechanisms
- **Safety Assessment**: Hepatotoxicity mechanisms, Cardiotoxicity indicators, Genotoxicity assays, Reproductive toxicity studies
- **Chemical Databases**: ChEMBL compound data, PubChem molecular information, ToxCast screening results, Tox21 assay data
- **ML Models**: Random Forest algorithms, Support Vector Machines, Neural networks for toxicity prediction, Ensemble methods

RESPONSE STRUCTURE GUIDELINES:
- Format: Use clear sections, bullet points (-), and simple formatting for better readability
- Scientific Accuracy: Provide precise, evidence-based information with appropriate caveats
- Explanations: Break down complex concepts into digestible parts with examples
- Practical Application: Include real-world applications and case studies when relevant
- Safety Notes: Always emphasize when to consult healthcare professionals or regulatory experts
- References: Mention relevant databases, literature, or methodologies when applicable
- NO MARKDOWN: Do not use bold, italic, headers, or code blocks - use plain text with clear structure

PLATFORM INTEGRATION:
You are the AI brain of MedToXAi, a cutting-edge molecular toxicity prediction platform featuring:
- 5-Endpoint Prediction System: Comprehensive toxicity assessment across key biological targets
- SMILES Analysis Engine: Advanced chemical structure interpretation and property prediction
- AI-Powered Insights: Machine learning-driven safety and efficacy predictions
- Research Support: Tools for safer chemical design and drug development decisions

RESPONSE STYLE:
- Start with a brief, direct answer to the user's question
- Follow with detailed explanation in structured sections
- Include practical examples or case studies when helpful
- End with actionable insights or next steps
- Maintain scientific rigor while being accessible and educational
- Use appropriate technical terminology but explain complex terms
- Use plain text formatting without markdown symbols

Always be helpful, accurate, and educational while maintaining the highest standards of scientific integrity."""

        # Create messages for the conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Use groq client to get response (potentially using gpt-oss-120b if configured)
        try:
            response = groq_client.client.chat.completions.create(
                model=os.getenv('AI_MODEL', 'llama3-8b-8192'),
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                top_p=0.9
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean response from markdown formatting
            cleaned_response = ai_response.replace('**', '').replace('*', '').replace('##', '').replace('#', '').replace('```', '').replace('`', '')
            
            return jsonify({
                'success': True,
                'response': cleaned_response,
                'message': user_message,
                'context': context,
                'model': os.getenv('AI_MODEL', 'llama3-8b-8192'),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as groq_error:
            print(f"❌ Groq API error: {groq_error}")
            # Enhanced fallback response with basic knowledge
            fallback_response = f"""Temporary Service Interruption

I am currently experiencing technical difficulties with the main AI service, but I can provide some basic guidance:

Your Question: {user_message}

Basic Chemistry & Toxicology Guidance:

If asking about SMILES notation:
- SMILES (Simplified Molecular Input Line Entry System) represents molecular structures as text strings
- Example: C1=CC=CC=C1 represents benzene (hexagonal ring)
- Each character represents atoms and bonds in a systematic way

If asking about toxicity endpoints:
- NR-AR-LBD: Androgen Receptor Ligand Binding Domain - affects hormonal activity
- NR-AhR: Aryl Hydrocarbon Receptor - involved in xenobiotic metabolism
- SR-MMP: Mitochondrial Membrane Potential - indicates cellular stress
- NR-ER-LBD: Estrogen Receptor - hormonal disruption indicator
- NR-AR: Androgen Receptor - endocrine disruption marker

If asking about drug safety:
- ADME properties (Absorption, Distribution, Metabolism, Excretion) are crucial
- Hepatotoxicity often results from reactive metabolites
- Cardiotoxicity may involve ion channel interactions

Try These Approaches:
- Rephrase your question more specifically
- Ask about individual concepts rather than complex combinations
- Use technical terms like "mechanism", "pathway", or "assessment"

Service Status: The full AI capabilities will be restored shortly. Try your question again in a moment for detailed, expert-level analysis!"""
            
            return jsonify({
                'success': False,
                'response': fallback_response,
                'message': user_message,
                'error': 'AI service temporarily unavailable',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        print(f"❌ Chat ask error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Chat service failed: {str(e)}'}), 500

@app.route('/api/database/predictions', methods=['GET'])
def get_user_predictions():
    """Get user's prediction history from database"""
    try:
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 503
        
        user_id = request.args.get('user_id', 'anonymous')
        limit = int(request.args.get('limit', 50))
        
        # Note: This should be async in production
        predictions = []  # await db_service.get_user_predictions(user_id, limit)
        
        return jsonify({
            'predictions': [pred.to_dict() for pred in predictions],
            'count': len(predictions),
            'user_id': user_id
        })
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500

@app.route('/api/database/molecules', methods=['GET'])
def get_molecule_library():
    """Get molecules from the library"""
    try:
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 503
        
        category = request.args.get('category')
        limit = int(request.args.get('limit', 100))
        
        # Note: This should be async in production
        molecules = []  # await db_service.get_molecule_library(category, limit)
        
        return jsonify({
            'molecules': [mol.to_dict() for mol in molecules],
            'count': len(molecules),
            'category': category
        })
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500

@app.route('/api/session/stats', methods=['POST', 'GET'])
def get_session_stats():
    data = request.get_json(silent=True) or {}
    history = data.get('history', [])
    total = len(history)
    toxic = sum(1 for h in history if h.get('overall_risk') in ['High Risk', 'CRITICAL'])
    safe = total - toxic
    return jsonify({
        'total_predictions': total,
        'toxic_count': toxic,
        'safe_count': safe,
        'status': 'success'
    })

@app.route('/api/stats', methods=['GET'])
def get_platform_stats():
    """Get platform statistics from database"""
    try:
        if db_service:
            # Fetch predictions from database
            predictions = db_service.client.table('predictions').select('*').execute()
            total = len(predictions.data) if predictions.data else 0
            
            # Count toxic vs safe
            toxic_count = 0
            safe_count = 0
            
            for pred in (predictions.data or []):
                endpoints = pred.get('endpoints', {})
                # Check if any endpoint is toxic
                is_toxic = any(
                    v.get('prediction', '').lower() == 'toxic' 
                    for k, v in endpoints.items() 
                    if isinstance(v, dict)
                )
                if is_toxic:
                    toxic_count += 1
                else:
                    safe_count += 1
            
            return jsonify({
                'total_predictions': total,
                'toxic_compounds': toxic_count,
                'safe_compounds': safe_count,
                'success_rate': 94.2,
                'processing_time': '1.4s',
                'active_models': 5,
                'compounds_analyzed': total
            })
        else:
            # Fallback to demo data if database not available
            return jsonify({
                'total_predictions': 0,
                'toxic_compounds': 0,
                'safe_compounds': 0,
                'success_rate': 94.2,
                'processing_time': '1.4s',
                'active_models': 5,
                'compounds_analyzed': 0
            })
    except Exception as e:
        print(f"❌ Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions', methods=['GET', 'POST'])
def handle_predictions():
    """Get or save predictions"""
    try:
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 503
            
        if request.method == 'GET':
            # Get query parameters
            limit = request.args.get('limit', 20, type=int)
            recent = request.args.get('recent', 'false').lower() == 'true'
            
            # Fetch predictions from database
            query = db_service.client.table('predictions')\
                .select('*')\
                .order('created_at', desc=True)
            
            if recent:
                query = query.limit(5)
            else:
                query = query.limit(limit)
            
            result = query.execute()
            
            return jsonify({
                'success': True,
                'count': len(result.data) if result.data else 0,
                'predictions': result.data or []
            })
        
        else:  # POST
            # Save new prediction
            data = request.json
            
            # Validate required fields
            if not data.get('smiles'):
                return jsonify({'error': 'SMILES string is required'}), 400
            
            # Validate SMILES format
            smiles = data.get('smiles').strip()
            if smiles:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    return jsonify({'error': 'Invalid SMILES string', 'example': 'CC(=O)Oc1ccccc1C(=O)O'}), 400
            
            # Insert into database
            result = db_service.client.table('predictions').insert({
                'smiles': data.get('smiles'),
                'molecule_name': data.get('molecule_name'),
                'endpoints': data.get('endpoints', {}),
                'ai_analysis': data.get('ai_analysis'),
                'user_id': data.get('user_id', 'anonymous'),
                'metadata': data.get('metadata', {})
            }).execute()
            
            return jsonify({
                'success': True,
                'prediction': result.data[0] if result.data else None
            })
            
    except Exception as e:
        print(f"❌ Error handling predictions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data from database"""
    try:
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 503
            
        # Fetch predictions
        predictions = db_service.client.table('predictions').select('*').execute()
        
        # Calculate endpoint performance
        endpoints_stats = {
            'NR-AR-LBD': {'accuracy': 83.9, 'predictions': 0, 'toxic': 0},
            'NR-AhR': {'accuracy': 83.4, 'predictions': 0, 'toxic': 0},
            'SR-MMP': {'accuracy': 80.8, 'predictions': 0, 'toxic': 0},
            'NR-ER-LBD': {'accuracy': 77.6, 'predictions': 0, 'toxic': 0},
            'NR-AR': {'accuracy': 75.2, 'predictions': 0, 'toxic': 0}
        }
        
        total_predictions = len(predictions.data) if predictions.data else 0
        toxic_count = 0
        safe_count = 0
        
        for pred in (predictions.data or []):
            endpoints = pred.get('endpoints', {})
            is_toxic = False
            for endpoint_id, endpoint_data in endpoints.items():
                if endpoint_id in endpoints_stats:
                    endpoints_stats[endpoint_id]['predictions'] += 1
                    if isinstance(endpoint_data, dict):
                        if endpoint_data.get('prediction', '').lower() == 'toxic':
                            endpoints_stats[endpoint_id]['toxic'] += 1
                            is_toxic = True
            
            if is_toxic:
                toxic_count += 1
            else:
                safe_count += 1
        
        # Recent activity
        recent = db_service.client.table('predictions')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        activity = []
        for pred in (recent.data or []):
            is_toxic = False
            endpoints = pred.get('endpoints', {})
            if isinstance(endpoints, dict):
                is_toxic = any(
                    v.get('prediction', '').lower() == 'toxic'
                    for v in endpoints.values()
                    if isinstance(v, dict)
                )
            
            molecule_name = pred.get('molecule_name') or pred.get('smiles') or 'Unknown'
            activity.append({
                'compound': str(molecule_name)[:50],
                'result': 'Toxic' if is_toxic else 'Safe',
                'timestamp': pred.get('created_at', ''),
                'created_at': pred.get('created_at', ''),
                'smiles': pred.get('smiles', '')
            })
        
        return jsonify({
            'overview': {
                'total_predictions': total_predictions,
                'toxic_compounds': toxic_count,
                'safe_compounds': safe_count,
                'average_accuracy': 80.2
            },
            'endpoint_performance': [
                {
                    'endpoint': k,
                    'name': k.replace('-', ' '),
                    'accuracy': v['accuracy'],
                    'predictions': v['predictions']
                }
                for k, v in endpoints_stats.items()
            ],
            'recent_activity': activity
        })
        
    except Exception as e:
        print(f"❌ Error fetching analytics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/results', methods=['GET'])
def download_results():
    """Download batch processing results as CSV from local files"""
    try:
        import csv
        import io
        import json
        from pathlib import Path
        
        # Get format from query parameter (csv, json)
        format_type = request.args.get('format', 'csv').lower()
        
        # Get batch results directory
        results_dir = Path(__file__).parent / 'batch_results'
        
        # Check if directory exists and has files
        if not results_dir.exists() or not list(results_dir.glob('batch_results_*.json')):
            # Return helpful message instead of 404
            if format_type == 'csv':
                output = io.StringIO()
                output.write('No batch results available yet.\n')
                output.write('Please run a batch prediction first using the "Batch Processing" feature in the frontend.\n')
                csv_data = output.getvalue()
                output.close()
                
                from flask import Response
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=no_results_{datetime.now().strftime("%Y-%m-%d")}.csv'
                    }
                )
            else:
                return jsonify({
                    'error': 'No batch results found',
                    'message': 'Please run a batch prediction first using the Batch Processing feature'
                }), 404
        
        # Get all result files, sorted by timestamp (newest first)
        result_files = sorted(results_dir.glob('batch_results_*.json'), reverse=True)
        
        # Get the most recent results or combine all
        combine_all = request.args.get('all', 'false').lower() == 'true'
        
        export_data = []
        if combine_all:
            # Combine all result files
            for result_file in result_files:
                try:
                    with open(result_file, 'r') as f:
                        data = json.load(f)
                        for result in data.get('results', []):
                            if 'error' not in result:
                                row = {
                                    'SMILES': result.get('smiles', ''),
                                    'Timestamp': result.get('timestamp', ''),
                                    'Overall_Toxicity': result.get('overall_toxicity', 'Unknown'),
                                    'Confidence': result.get('confidence', 'Unknown'),
                                    'Toxic_Endpoints': result.get('toxic_endpoints', 0),
                                    'Average_Probability': result.get('average_probability', 0.0)
                                }
                                
                                # Add individual model predictions
                                for model_id, pred_data in result.get('predictions', {}).items():
                                    if isinstance(pred_data, dict):
                                        row[f'{model_id}_prediction'] = pred_data.get('prediction', 'Unknown')
                                        row[f'{model_id}_probability'] = pred_data.get('probability', 0.0)
                                
                                export_data.append(row)
                except Exception as e:
                    print(f"⚠️ Error reading {result_file}: {e}")
                    continue
        else:
            # Use most recent file only
            try:
                with open(result_files[0], 'r') as f:
                    data = json.load(f)
                    for result in data.get('results', []):
                        if 'error' not in result:
                            row = {
                                'SMILES': result.get('smiles', ''),
                                'Timestamp': result.get('timestamp', ''),
                                'Overall_Toxicity': result.get('overall_toxicity', 'Unknown'),
                                'Confidence': result.get('confidence', 'Unknown'),
                                'Toxic_Endpoints': result.get('toxic_endpoints', 0),
                                'Average_Probability': result.get('average_probability', 0.0)
                            }
                            
                            # Add individual model predictions
                            for model_id, pred_data in result.get('predictions', {}).items():
                                if isinstance(pred_data, dict):
                                    row[f'{model_id}_prediction'] = pred_data.get('prediction', 'Unknown')
                                    row[f'{model_id}_probability'] = pred_data.get('probability', 0.0)
                            
                            export_data.append(row)
            except Exception as e:
                print(f"⚠️ Error reading most recent file: {e}")
                return jsonify({'error': 'Failed to read batch results'}), 500
        
        if not export_data:
            return jsonify({'error': 'No valid results to export'}), 404
        
        if format_type == 'csv':
            # Create CSV response
            output = io.StringIO()
            
            fieldnames = export_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
            
            csv_data = output.getvalue()
            output.close()
            
            from flask import Response
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=batch_results_{datetime.now().strftime("%Y-%m-%d")}.csv'
                }
            )
        
        elif format_type == 'json':
            from flask import Response
            return Response(
                json.dumps(export_data, indent=2),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=batch_results_{datetime.now().strftime("%Y-%m-%d")}.json'
                }
            )
        
        else:
            return jsonify({'error': f'Unsupported format: {format_type}'}), 400
            
    except Exception as e:
        print(f"❌ Error downloading results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/molecule', methods=['POST'])
def visualize_molecule():
    """Generate molecular structure visualization from SMILES using RDKit"""
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw
        import base64
        from io import BytesIO
        
        data = request.get_json()
        if not data or 'smiles' not in data:
            return jsonify({'error': 'SMILES string required'}), 400
        
        smiles = data['smiles'].strip()
        if not smiles:
            return jsonify({'error': 'Empty SMILES string'}), 400
        
        # Parse SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return jsonify({'error': 'Invalid SMILES string'}), 400
        
        # Get image size from request or use default
        img_size = data.get('size', 400)
        
        # Generate 2D structure image
        img = Draw.MolToImage(mol, size=(img_size, img_size))
        
        # Convert to base64 for frontend display
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Get molecular properties
        mol_weight = Chem.Descriptors.MolWt(mol)
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        num_rings = Chem.Descriptors.RingCount(mol)
        
        return jsonify({
            'success': True,
            'smiles': smiles,
            'image': f'data:image/png;base64,{img_base64}',
            'properties': {
                'molecular_weight': round(mol_weight, 2),
                'num_atoms': num_atoms,
                'num_bonds': num_bonds,
                'num_rings': num_rings
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except ImportError as e:
        print(f"❌ RDKit import error: {e}")
        return jsonify({'error': 'RDKit not available. Please install: pip install rdkit'}), 500
    except Exception as e:
        print(f"❌ Visualization error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Visualization failed: {str(e)}'}), 500

@app.route('/api/models/status', methods=['GET'])
def get_model_status():
    """Get model status and performance"""
    try:
        models = [
            {
                'name': 'NR-AR-LBD XGBoost',
                'accuracy': '83.9%',
                'status': 'active',
                'endpoint': 'NR-AR-LBD'
            },
            {
                'name': 'NR-AhR Random Forest',
                'accuracy': '83.4%',
                'status': 'active',
                'endpoint': 'NR-AhR'
            },
            {
                'name': 'SR-MMP Gradient Boosting',
                'accuracy': '80.8%',
                'status': 'active',
                'endpoint': 'SR-MMP'
            },
            {
                'name': 'NR-ER-LBD XGBoost',
                'accuracy': '77.6%',
                'status': 'active',
                'endpoint': 'NR-ER-LBD'
            },
            {
                'name': 'NR-AR Random Forest',
                'accuracy': '75.2%',
                'status': 'active',
                'endpoint': 'NR-AR'
            }
        ]
        
        return jsonify({
            'success': True,
            'models': models,
            'total_active': len([m for m in models if m['status'] == 'active']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error fetching model status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/molecules', methods=['GET'])
def get_molecules():
    """Get molecule library from database"""
    try:
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 503
            
        # Fetch from database
        result = db_service.client.table('molecule_library').select('*').execute()
        
        return jsonify({
            'success': True,
            'count': len(result.data) if result.data else 0,
            'molecules': result.data or []
        })
        
    except Exception as e:
        print(f"❌ Error fetching molecules: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chemical-name-to-smiles', methods=['POST'])
def chemical_name_to_smiles():
    """Convert chemical name to SMILES using AI and chemical databases"""
    try:
        data = request.get_json()
        if not data or 'chemical_name' not in data:
            return jsonify({'error': 'Chemical name required'}), 400
        
        chemical_name = data['chemical_name'].strip()
        if not chemical_name:
            return jsonify({'error': 'Empty chemical name'}), 400
        
        include_suggestions = data.get('include_suggestions', False)
        
        # Common chemical database for quick lookup
        common_chemicals = {
            'aspirin': {'smiles': 'CC(=O)OC1=CC=CC=C1C(=O)O', 'name': 'Aspirin'},
            'caffeine': {'smiles': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', 'name': 'Caffeine'},
            'ethanol': {'smiles': 'CCO', 'name': 'Ethanol'},
            'acetaminophen': {'smiles': 'CC(=O)NC1=CC=C(C=C1)O', 'name': 'Acetaminophen'},
            'paracetamol': {'smiles': 'CC(=O)NC1=CC=C(C=C1)O', 'name': 'Acetaminophen'},
            'ibuprofen': {'smiles': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', 'name': 'Ibuprofen'},
            'benzene': {'smiles': 'C1=CC=CC=C1', 'name': 'Benzene'},
            'toluene': {'smiles': 'CC1=CC=CC=C1', 'name': 'Toluene'},
            'methanol': {'smiles': 'CO', 'name': 'Methanol'},
            'acetone': {'smiles': 'CC(=O)C', 'name': 'Acetone'},
            'phenol': {'smiles': 'C1=CC=C(C=C1)O', 'name': 'Phenol'},
            'nicotine': {'smiles': 'CN1CCCC1C2=CN=CC=C2', 'name': 'Nicotine'},
            'glucose': {'smiles': 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O', 'name': 'Glucose'},
            'morphine': {'smiles': 'CN1CC[C@]23[C@@H]4[C@H]1C[C@H]([C@@H]4O)C=C2[C@H]([C@@H]([C@@H]3O)O)O', 'name': 'Morphine'},
            'penicillin': {'smiles': 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', 'name': 'Penicillin'},
            'water': {'smiles': 'O', 'name': 'Water'},
            'carbon dioxide': {'smiles': 'O=C=O', 'name': 'Carbon Dioxide'},
            'ammonia': {'smiles': 'N', 'name': 'Ammonia'},
            'sulfuric acid': {'smiles': 'O=S(=O)(O)O', 'name': 'Sulfuric Acid'},
            'hydrochloric acid': {'smiles': 'Cl', 'name': 'Hydrochloric Acid'},
            'sodium chloride': {'smiles': '[Na+].[Cl-]', 'name': 'Sodium Chloride'},
            'testosterone': {'smiles': 'CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C', 'name': 'Testosterone'},
            'estradiol': {'smiles': 'CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O', 'name': 'Estradiol'},
            'cholesterol': {'smiles': 'CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C', 'name': 'Cholesterol'},
            'dopamine': {'smiles': 'C1=CC(=C(C=C1CCN)O)O', 'name': 'Dopamine'},
            'serotonin': {'smiles': 'C1=CC2=C(C=C1O)C(=CN2)CCN', 'name': 'Serotonin'},
            'adrenaline': {'smiles': 'CNCC(C1=CC(=C(C=C1)O)O)O', 'name': 'Adrenaline'},
            'epinephrine': {'smiles': 'CNCC(C1=CC(=C(C=C1)O)O)O', 'name': 'Epinephrine'}
        }
        
        # Search for exact match or fuzzy match
        chemical_key = chemical_name.lower().strip()
        result = None
        
        # Exact match
        if chemical_key in common_chemicals:
            result = common_chemicals[chemical_key]
        else:
            # Fuzzy match - find partial matches
            for key, value in common_chemicals.items():
                if chemical_key in key or key in chemical_key:
                    result = value
                    break
        
        # Prepare response
        response = {'success': False}
        
        if result:
            response.update({
                'success': True,
                'smiles': result['smiles'],
                'name': result['name'],
                'source': 'database'
            })
        else:
            # Try AI-powered conversion using Groq
            try:
                if groq_client:
                    ai_prompt = f"""Convert the chemical name "{chemical_name}" to SMILES notation. 
                    
                    Respond with a valid JSON object containing:
                    - "smiles": the SMILES string (or null if not found)
                    - "name": the standard chemical name
                    - "confidence": high/medium/low
                    
                    If you cannot find the chemical, set smiles to null."""
                    
                    ai_response = groq_client.chat.completions.create(
                        model=os.getenv('AI_MODEL', 'llama3-8b-8192'),
                        messages=[{"role": "user", "content": ai_prompt}],
                        temperature=0.1,
                        max_tokens=256
                    )
                    
                    ai_text = ai_response.choices[0].message.content.strip()
                    
                    # Try to parse JSON response
                    import json
                    try:
                        ai_data = json.loads(ai_text)
                        if ai_data.get('smiles'):
                            response.update({
                                'success': True,
                                'smiles': ai_data['smiles'],
                                'name': ai_data.get('name', chemical_name),
                                'confidence': ai_data.get('confidence', 'medium'),
                                'source': 'ai'
                            })
                    except json.JSONDecodeError:
                        pass
            except Exception as ai_error:
                print(f"AI conversion failed: {ai_error}")
        
        # Add suggestions if requested
        if include_suggestions:
            suggestions = []
            query_lower = chemical_name.lower()
            for key, value in common_chemicals.items():
                if (query_lower in key or key in query_lower) and len(suggestions) < 8:
                    chemical_type = 'drug' if key in ['aspirin', 'acetaminophen', 'ibuprofen', 'morphine', 'penicillin'] else \
                                    'alcohol' if key in ['ethanol', 'methanol'] else \
                                    'solvent' if key in ['benzene', 'toluene', 'acetone'] else \
                                    'hormone' if key in ['testosterone', 'estradiol', 'adrenaline'] else \
                                    'neurotransmitter' if key in ['dopamine', 'serotonin'] else 'chemical'
                    
                    suggestions.append({
                        'name': value['name'],
                        'smiles': value['smiles'],
                        'type': chemical_type
                    })
            
            response['suggestions'] = suggestions
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Chemical name to SMILES conversion error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/natural-language-to-chemical', methods=['POST'])
def natural_language_to_chemical():
    """Convert natural language query to chemical name and SMILES using AI"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Natural language query required'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Empty query'}), 400
        
        print(f"🔍 Processing natural language query: '{query}'")
        
        # Enhanced chemical database with natural language keywords
        chemical_db = {
            # Pain relievers / Analgesics
            'aspirin': {
                'smiles': 'CC(=O)OC1=CC=CC=C1C(=O)O',
                'name': 'Aspirin',
                'type': 'Pain Relief',
                'keywords': ['painkiller', 'pain relief', 'headache', 'anti-inflammatory', 'fever reducer', 'analgesic', 'nsaid']
            },
            'acetaminophen': {
                'smiles': 'CC(=O)NC1=CC=C(C=C1)O',
                'name': 'Acetaminophen',
                'type': 'Pain Relief',
                'keywords': ['paracetamol', 'tylenol', 'painkiller', 'pain relief', 'headache', 'fever reducer', 'analgesic']
            },
            'ibuprofen': {
                'smiles': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
                'name': 'Ibuprofen',
                'type': 'Pain Relief',
                'keywords': ['advil', 'motrin', 'painkiller', 'pain relief', 'anti-inflammatory', 'fever reducer', 'nsaid']
            },
            'morphine': {
                'smiles': 'CN1CC[C@]23[C@@H]4[C@H]1C[C@H]([C@@H]4O)C=C2[C@H]([C@@H]([C@@H]3O)O)O',
                'name': 'Morphine',
                'type': 'Pain Relief',
                'keywords': ['strong painkiller', 'opioid', 'narcotic', 'severe pain', 'opiates']
            },
            
            # Stimulants
            'caffeine': {
                'smiles': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
                'name': 'Caffeine',
                'type': 'Stimulant',
                'keywords': ['coffee', 'stimulant', 'energy', 'alertness', 'wake up', 'tea', 'energy drink']
            },
            'nicotine': {
                'smiles': 'CN1CCCC1C2=CN=CC=C2',
                'name': 'Nicotine',
                'type': 'Stimulant',
                'keywords': ['tobacco', 'cigarette', 'smoking', 'stimulant', 'addiction']
            },
            
            # Alcohols
            'ethanol': {
                'smiles': 'CCO',
                'name': 'Ethanol',
                'type': 'Alcohol',
                'keywords': ['alcohol', 'drinking alcohol', 'ethyl alcohol', 'booze', 'liquor', 'beer', 'wine']
            },
            'methanol': {
                'smiles': 'CO',
                'name': 'Methanol',
                'type': 'Toxic Alcohol',
                'keywords': ['wood alcohol', 'methyl alcohol', 'toxic alcohol', 'poisonous alcohol', 'antifreeze']
            },
            
            # Antibiotics
            'penicillin': {
                'smiles': 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C',
                'name': 'Penicillin',
                'type': 'Antibiotic',
                'keywords': ['antibiotic', 'infection', 'bacteria', 'antimicrobial', 'penicillin']
            },
            
            # Hormones
            'testosterone': {
                'smiles': 'CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C',
                'name': 'Testosterone',
                'type': 'Hormone',
                'keywords': ['male hormone', 'testosterone', 'steroid hormone', 'sex hormone', 'androgen']
            },
            'estradiol': {
                'smiles': 'CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O',
                'name': 'Estradiol',
                'type': 'Hormone',
                'keywords': ['female hormone', 'estrogen', 'estradiol', 'sex hormone', 'reproductive hormone']
            },
            'adrenaline': {
                'smiles': 'CNCC(C1=CC(=C(C=C1)O)O)O',
                'name': 'Adrenaline',
                'type': 'Hormone',
                'keywords': ['epinephrine', 'stress hormone', 'fight or flight', 'emergency hormone', 'adrenaline']
            },
            
            # Neurotransmitters
            'dopamine': {
                'smiles': 'C1=CC(=C(C=C1CCN)O)O',
                'name': 'Dopamine',
                'type': 'Neurotransmitter',
                'keywords': ['neurotransmitter', 'reward', 'pleasure', 'motivation', 'brain chemical']
            },
            'serotonin': {
                'smiles': 'C1=CC2=C(C=C1O)C(=CN2)CCN',
                'name': 'Serotonin',
                'type': 'Neurotransmitter',
                'keywords': ['neurotransmitter', 'happiness', 'mood', 'depression', 'brain chemical']
            },
            
            # Basic chemicals
            'glucose': {
                'smiles': 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O',
                'name': 'Glucose',
                'type': 'Sugar',
                'keywords': ['sugar', 'blood sugar', 'energy', 'diabetes', 'glucose']
            },
            'cholesterol': {
                'smiles': 'CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C',
                'name': 'Cholesterol',
                'type': 'Lipid',
                'keywords': ['cholesterol', 'fat', 'lipid', 'heart disease', 'blood cholesterol']
            },
            'water': {
                'smiles': 'O',
                'name': 'Water',
                'type': 'Basic',
                'keywords': ['water', 'h2o', 'hydration', 'liquid']
            },
            
            # Toxic solvents
            'benzene': {
                'smiles': 'C1=CC=CC=C1',
                'name': 'Benzene',
                'type': 'Toxic Solvent',
                'keywords': ['benzene', 'toxic solvent', 'carcinogen', 'industrial solvent', 'aromatic']
            },
            'toluene': {
                'smiles': 'CC1=CC=CC=C1',
                'name': 'Toluene',
                'type': 'Toxic Solvent',
                'keywords': ['toluene', 'solvent', 'paint thinner', 'industrial chemical', 'aromatic']
            },
            'acetone': {
                'smiles': 'CC(=O)C',
                'name': 'Acetone',
                'type': 'Solvent',
                'keywords': ['acetone', 'nail polish remover', 'solvent', 'ketone']
            },
            'phenol': {
                'smiles': 'C1=CC=C(C=C1)O',
                'name': 'Phenol',
                'type': 'Toxic Chemical',
                'keywords': ['phenol', 'carbolic acid', 'toxic', 'disinfectant', 'antiseptic']
            }
        }
        
        # First try local keyword matching
        query_lower = query.lower()
        matches = []
        
        for chem_key, chem_data in chemical_db.items():
            relevance_score = 0
            matched_keywords = []
            
            # Check for keyword matches
            for keyword in chem_data['keywords']:
                if keyword in query_lower:
                    relevance_score += len(keyword)  # Longer matches get higher scores
                    matched_keywords.append(keyword)
            
            # Check chemical name match
            if chem_data['name'].lower() in query_lower or chem_key in query_lower:
                relevance_score += 20  # Boost for direct name matches
                matched_keywords.append(chem_data['name'].lower())
            
            if relevance_score > 0:
                matches.append({
                    'chemical': chem_key,
                    'data': chem_data,
                    'score': relevance_score,
                    'matched_keywords': matched_keywords
                })
        
        # Sort by relevance score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # If we have good local matches, return the best one
        if matches:
            best_match = matches[0]
            print(f"✅ Found local match: {best_match['data']['name']} (score: {best_match['score']})")
            
            return jsonify({
                'success': True,
                'chemical_name': best_match['data']['name'],
                'smiles': best_match['data']['smiles'],
                'type': best_match['data']['type'],
                'source': 'local_database',
                'relevance_score': best_match['score'],
                'matched_keywords': best_match['matched_keywords']
            })
        
        # If no local matches, try AI processing
        if groq_client:
            try:
                print("🤖 Using AI for natural language processing...")
                
                ai_prompt = f"""You are a chemistry expert. Convert this natural language query to a specific chemical name and SMILES notation: "{query}"

Examples:
- "painkiller" → Aspirin (CC(=O)OC1=CC=CC=C1C(=O)O)
- "stimulant in coffee" → Caffeine (CN1C=NC2=C1C(=O)N(C(=O)N2C)C)
- "drinking alcohol" → Ethanol (CCO)
- "toxic solvent" → Benzene (C1=CC=CC=C1)

Respond with valid JSON:
{{
    "chemical_name": "exact chemical name",
    "smiles": "SMILES notation",
    "type": "category like Pain Relief, Stimulant, etc",
    "confidence": "high/medium/low"
}}

If you cannot identify a specific chemical, set chemical_name and smiles to null."""

                ai_response = groq_client.chat.completions.create(
                    model=os.getenv('AI_MODEL', 'llama3-8b-8192'),
                    messages=[{"role": "user", "content": ai_prompt}],
                    temperature=0.1,
                    max_tokens=512
                )
                
                ai_text = ai_response.choices[0].message.content.strip()
                print(f"🤖 AI Response: {ai_text}")
                
                # Parse AI response
                import json
                try:
                    ai_data = json.loads(ai_text)
                    if ai_data.get('chemical_name') and ai_data.get('smiles'):
                        print(f"✅ AI converted '{query}' to {ai_data['chemical_name']}")
                        return jsonify({
                            'success': True,
                            'chemical_name': ai_data['chemical_name'],
                            'smiles': ai_data['smiles'],
                            'type': ai_data.get('type', 'Unknown'),
                            'confidence': ai_data.get('confidence', 'medium'),
                            'source': 'ai_groq'
                        })
                except json.JSONDecodeError as je:
                    print(f"❌ AI JSON parse error: {je}")
                    
            except Exception as ai_error:
                print(f"❌ AI processing error: {ai_error}")
        
        # If all else fails
        return jsonify({
            'success': False,
            'error': f'Could not find chemical for query: "{query}". Try being more specific (e.g., "painkiller", "coffee stimulant", "drinking alcohol").'
        })
        
    except Exception as e:
        print(f"❌ Natural language processing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/medtoxai/analyze', methods=['POST'])
def medtoxai_analyze():
    """Analyze medicine using MedToXAi"""
    try:
        if not medtoxai_analyzer:
            return jsonify({'error': 'MedToXAi service not available'}), 503
        
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({'error': 'Input required (chemical name or image)'}), 400
        
        input_data = data['input'].strip()
        if not input_data:
            return jsonify({'error': 'Empty input'}), 400
        
        # Analyze using MedToXAi
        results = medtoxai_analyzer.analyze_medicine(input_data)
        
        # Generate report if requested
        report_format = data.get('format', 'json')
        if data.get('include_report', False):
            report = medtoxai_analyzer.generate_report(results, report_format)
            results['report'] = report
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ MediTox analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'MedToXAi analysis failed: {str(e)}'}), 500

@app.route('/api/medtoxai/safety-report', methods=['POST'])
def medtoxai_safety_report():
    """Generate safety report for medicine/chemical"""
    try:
        if not medtoxai_analyzer:
            return jsonify({'error': 'MedToXAi service not available'}), 503
        
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({'error': 'Input required'}), 400
        
        input_data = data['input'].strip()
        format_type = data.get('format', 'json')
        
        # Generate safety report
        report = get_safety_report(input_data, format=format_type)
        
        return jsonify({
            'success': True,
            'input': input_data,
            'format': format_type,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ MediTox safety report error: {e}")
        return jsonify({'error': f'Safety report generation failed: {str(e)}'}), 500

@app.route('/api/medtoxai/chemical-info', methods=['GET'])
def medtoxai_chemical_info():
    """Get chemical information from database"""
    try:
        if not medtoxai_analyzer:
            return jsonify({'error': 'MedToXAi service not available'}), 503
        
        chemical_name = request.args.get('name')
        if not chemical_name:
            return jsonify({'error': 'Chemical name required'}), 400
        
        # Get chemical info
        chem_info = medtoxai_analyzer.get_chemical_info(chemical_name)
        
        return jsonify({
            'success': True,
            'chemical_name': chemical_name,
            'chemical_info': chem_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Chemical info error: {e}")
        return jsonify({'error': f'Chemical info retrieval failed: {str(e)}'}), 500




@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("\n🛡️  PharmaGuard AI — Trustworthy Drug-Safety Decision Support")
    print("=" * 50)

    # Initialize predictor
    if initialize_services():
        # Register the PharmaGuard AI blueprint NOW (after all @route decorators executed)
        if PHARMAGUARD_BP_AVAILABLE:
            app.register_blueprint(pharmaguard_bp)
            print("✅ PharmaGuard AI blueprint registered")

            # Apply rate limits to expensive blueprint endpoints
            # Note: view_functions on blueprint are populated after registration with app prefix
            limiter.limit("10 per minute")(app.view_functions['pharmaguard.analyze_single'])
            limiter.limit("5 per minute")(app.view_functions['pharmaguard.analyze_batch'])
            limiter.limit("5 per minute")(app.view_functions['pharmaguard.optimize_what_if'])
            limiter.limit("10 per minute")(app.view_functions['pharmaguard.explain_verify'])
            limiter.limit("10 per minute")(app.view_functions['pharmaguard.report_export'])
            limiter.limit("20 per minute")(app.view_functions['pharmaguard.visualize_attention_heatmap'])
            limiter.limit("20 per minute")(app.view_functions['pharmaguard.lookup_smiles'])
            limiter.limit("10 per minute")(app.view_functions['pharmaguard.report_pdf'])
            limiter.limit("10 per minute")(app.view_functions['pharmaguard.natural_language_query'])

        model_count = len(predictor.models) if predictor and getattr(predictor, 'models', None) is not None else 0
        model_status = 'Loaded' if predictor and getattr(predictor, 'is_loaded', False) else 'Mock/Not loaded'
        print(f"📊 Available models: {model_count}")
        print(f"🔬 Model status: {model_status}")
        print(f"🚧 OOD Detector: {'Active' if ood_detector else 'Disabled'}")
        print(f"🚦 Triage Engine: {'Active' if triage_engine else 'Disabled'}")
        print(f"✅ Faithfulness Validator: {'Active' if faithfulness_validator else 'Disabled'}")
        print("🌐 Starting server on http://localhost:5000")
        print("=" * 50)

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    else:
        print("❌ Failed to initialize predictor. Exiting.")
        sys.exit(1)