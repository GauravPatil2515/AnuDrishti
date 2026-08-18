#!/usr/bin/env python3
"""
Unified ADMET Predictor
=======================
Combines multiple models for comprehensive ADMET property prediction.

Models:
1. Attention-GIN (Tox21) - Trained with ROC-AUC 0.8368
2. XGBoost (5 NR endpoints) - From best_optimized_models.pkl
3. BBBP, ClinTox, Clearance models
4. ChemBERTa encoder (transformer-based SMILES encoder) - Phase 3
5. GPS Graph Transformer - Phase 3
6. TDC models (hERG, DILI, Ames) - placeholders
"""

import os
import sys
import pickle
import numpy as np
import torch
from pathlib import Path
from datetime import datetime

# Add paths
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import unified featurizer
from utils.molecular_featurizer import (
    smiles_to_graph_simple,
    smiles_to_graph_rich,
    extract_rdkit_descriptors,
    mc_dropout_predict,
    validate_smiles,
)

class UnifiedADMETPredictor:
    """Unified predictor for all ADMET properties"""
    
    TOX21_ENDPOINTS = [
        'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD',
        'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
    ]
    
    def __init__(self, enable_ensemble=True):
        self.models = {}
        self.is_loaded = False
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.enable_ensemble = enable_ensemble
        
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all available models"""
        models_loaded = 0
        
        # 1. Load Attention-GIN for Tox21 (Full 12 endpoints)
        try:
            gin_loaded = self._load_attention_gin()
            if gin_loaded:
                models_loaded += 1
        except Exception as e:
            print(f"⚠️ Attention-GIN not loaded: {e}")
        
        # 2. Load XGBoost models (fallback for NR endpoints)
        try:
            xgb_loaded = self._load_xgboost_models()
            if xgb_loaded:
                models_loaded += 1
        except Exception as e:
            print(f"⚠️ XGBoost models not loaded: {e}")
        
        # 3. Load BBBP model
        try:
            if self._load_bbbp(): models_loaded += 1
        except Exception as e: print(f"⚠️ BBBP model not loaded: {e}")
           
        # 4. Load ClinTox model
        try:
            if self._load_clintox(): models_loaded += 1
        except Exception as e: print(f"⚠️ ClinTox model not loaded: {e}")
        
        # 5. Load Clearance model
        try:
            if self._load_clearance(): models_loaded += 1
        except Exception as e: print(f"⚠️ Clearance model not loaded: {e}")
        
        # 6. Load ChemBERTa encoder (Phase 3)
        if self.enable_ensemble:
            try:
                if self._load_chemberta_encoder():
                    models_loaded += 1
            except Exception as e:
                print(f"⚠️ ChemBERTa encoder not loaded: {e}")
        
        # 7. Load GPS Graph Transformer (Phase 3)
        if self.enable_ensemble:
            try:
                if self._load_gps_model():
                    models_loaded += 1
            except Exception as e:
                print(f"⚠️ GPS model not loaded: {e}")
        
        # 8. Load TDC models (hERG, DILI, Ames) - Phase 3
        if self.enable_ensemble:
            try:
                if self._load_tdc_models():
                    models_loaded += 1
            except Exception as e:
                print(f"⚠️ TDC models not loaded: {e}")
        
        self.is_loaded = models_loaded > 0
        print(f"✅ Unified ADMET Predictor: {models_loaded} model types loaded")
    
    def _load_chemberta_encoder(self):
        """Load ChemBERTa encoder for ensemble (Phase 3)"""
        try:
            from models.chemberta_encoder import get_chemberta_encoder
            self.chemberta_encoder = get_chemberta_encoder(device=self.device)
            if self.chemberta_encoder.is_loaded:
                self.models['chemberta_encoder'] = {
                    'encoder': self.chemberta_encoder,
                    'name': 'ChemBERTa-zinc-base-v1',
                    'type': 'encoder',
                    'embedding_dim': 768
                }
                print("✅ Loaded ChemBERTa encoder (768-dim SMILES embeddings)")
                return True
        except Exception as e:
            print(f"⚠️ ChemBERTa encoder load failed: {e}")
        return False
    
    def _load_gps_model(self):
        """Load GPS Graph Transformer model (Phase 3)"""
        try:
            from models.gps_model import GPSModel
            
            model = GPSModel(
                num_tasks=12,  # Tox21 endpoints
                num_layers=5,
                emb_dim=300,
                drop_ratio=0.3,
                heads=4
            )
            
            model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "gps_tox21_model.pth"
            if model_path.exists():
                model.load_state_dict(torch.load(model_path, map_location=self.device))
                print("✅ Loaded pre-trained GPS model")
            else:
                print("⚠️ GPS model weights not found, using random initialization")
            
            model.to(self.device)
            model.eval()
            
            self.models['gps'] = {
                'model': model,
                'name': 'GPS Graph Transformer (Tox21)',
                'type': 'classification',
                'num_tasks': 12,
                'endpoints': self.TOX21_ENDPOINTS
            }
            print("✅ GPS Graph Transformer ready")
            return True
        except Exception as e:
            print(f"⚠️ GPS model load failed: {e}")
            return False
    
    def _load_tdc_models(self):
        """Load TDC models for hERG, DILI, Ames (Phase 3)"""
        try:
            # Try to import TDC
            from tdc.single_pred import Tox
            
            # Just mark as available - we'll use the data for training if needed
            self.tdc_available = True
            print("✅ TDC package available (hERG, DILI, Ames datasets)")
            
            # We don't have pre-trained models yet, but the data is available
            self.models['tdc'] = {
                'datasets': ['hERG', 'DILI', 'AMES'],
                'name': 'TDC Toxicity Endpoints',
                'type': 'classification',
                'note': 'Datasets available for training; no pre-trained models yet'
            }
            return True
        except Exception as e:
            print(f"⚠️ TDC not available: {e}")
            self.tdc_available = False
            return False
    
    def _load_bbbp(self):
        """Load BBBP model"""
        model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "bbbp_gin_model.pth"
        if not model_path.exists(): return False
        
        model = SimplifiedAttentionGINet(num_tasks=1)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        
        self.models['bbbp'] = {
            'model': model,
            'name': 'BBBP GIN',
            'type': 'classification'
        }
        print("✅ Loaded BBBP: Blood-Brain Barrier Penetration")
        return True

    def _load_clintox(self):
        """Load ClinTox model"""
        model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "clintox_gin_model.pth"
        if not model_path.exists(): return False
        
        model = SimplifiedAttentionGINet(num_tasks=2)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        
        self.models['clintox'] = {
            'model': model,
            'name': 'ClinTox GIN',
            'type': 'classification'
        }
        print("✅ Loaded ClinTox: Clinical Toxicity")
        return True

    def _load_clearance(self):
        """Load Clearance model"""
        model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "clearance_gin_model.pth"
        if not model_path.exists(): return False
        
        model = SimplifiedAttentionGINet(num_tasks=1)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        
        self.models['clearance'] = {
            'model': model,
            'name': 'Clearance GIN',
            'type': 'regression'
        }
        print("✅ Loaded Clearance: Intrinsic Clearance")
        return True

    # Use unified featurizer
    def _smiles_to_graph_simple(self, smiles):
        """Convert SMILES to PyG Data object (Simple Featurization for Attention-GIN)"""
        return smiles_to_graph_simple(smiles)

    def _load_attention_gin(self):
        """Load trained Attention-GIN model"""
        model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "attention_gin_model.pth"
        
        if not model_path.exists():
            print(f"❌ Attention-GIN not found: {model_path}")
            return False
        
        try:
            # Import model architecture
            from models.attention_ginet import AttentionGINet
            
            # Create model with same config as training
            model = AttentionGINet(
                task='classification',
                num_layer=5,
                emb_dim=300,
                feat_dim=512,
                drop_ratio=0.3,
                num_tasks=12  # Tox21 has 12 endpoints
            )
            
            # Load weights
            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            
            self.models['attention_gin'] = {
                'model': model,
                'name': 'Attention-GIN (Tox21)',
                'type': 'classification',
                'num_tasks': 12,
                'endpoints': self.TOX21_ENDPOINTS
            }
            
            print(f"✅ Loaded Attention-GIN: 12 Tox21 endpoints (ROC-AUC 0.8368)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load Attention-GIN: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_xgboost_models(self):
        """Load XGBoost models for NR endpoints"""
        model_path = Path(__file__).parent / "best_optimized_models.pkl"
        
        if not model_path.exists():
            print(f"❌ XGBoost models not found: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                xgb_models = pickle.load(f)
            
            self.models['xgboost'] = {
                'models': xgb_models,
                'name': 'XGBoost (5 NR endpoints)',
                'type': 'classification',
                'endpoints': list(xgb_models.keys())
            }
            
            print(f"✅ Loaded XGBoost: {len(xgb_models)} endpoints")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load XGBoost: {e}")
            return False
    
    def _smiles_to_graph(self, smiles):
        """Convert SMILES to PyG Data object (Rich featurization for GPS/XGBoost models)"""
        from utils.molecular_featurizer import smiles_to_graph_rich
        return smiles_to_graph_rich(smiles)

    def _extract_rdkit_features(self, smiles):
        """Extract 306 RDKit descriptors for XGBoost"""
        from utils.molecular_featurizer import extract_rdkit_descriptors
        return extract_rdkit_features(smiles)
    
    def predict(self, smiles):
            """Make predictions using all available models"""
            if not self.is_loaded:
                return {'error': 'No models loaded'}
        
            results = {
                'smiles': smiles,
                'timestamp': datetime.now().isoformat(),
                'predictions': {},
                'tox21': {},
                'admet': {}
            }
        
            # 1. Attention-GIN predictions (Tox21 - 12 endpoints)
            if 'attention_gin' in self.models:
                try:
                    gin_result = self._predict_attention_gin(smiles)
                    if isinstance(gin_result, tuple):
                        gin_results, overall_mean, overall_std, overall_ci_low, overall_ci_high = gin_result
                    else:
                        # For backward compatibility, if it's not a tuple, then it's the old return
                        gin_results = gin_result
                        overall_mean = np.mean([v['probability'] for v in gin_results.values()]) if gin_results else 0.5
                        overall_std = 0.0
                        overall_ci_low = overall_mean
                        overall_ci_high = overall_mean
                
                    results['tox21'] = gin_results
                    results['predictions'].update(gin_results)
                except Exception as e:
                    print(f"⚠️ Attention-GIN prediction failed: {e}")
        
            # Handle gin_result for summary calculation
            if 'attention_gin' in self.models:
                if isinstance(gin_result, tuple):
                    gin_results, overall_mean, overall_std, overall_ci_low, overall_ci_high = gin_result
                else:
                    gin_results = gin_result
                    overall_mean = np.mean([v['probability'] for v in gin_results.values()]) if gin_results else 0.5
                    overall_std = 0.0
                    overall_ci_low = overall_mean
                    overall_ci_high = overall_mean
        
            # 2. GPS Graph Transformer predictions (Tox21 - 12 endpoints) - Phase 3
            if 'gps' in self.models:
                try:
                    gps_results = self._predict_gps(smiles)
                    results['gps'] = gps_results
                    results['predictions'].update(gps_results)
                except Exception as e:
                    print(f"⚠️ GPS prediction failed: {e}")
        
            # 3. ChemBERTa encoder embeddings (Phase 3)
            if 'chemberta_encoder' in self.models:
                try:
                    chemberta_emb = self._get_chemberta_embedding(smiles)
                    results['chemberta_embedding'] = chemberta_emb.tolist() if chemberta_emb is not None else None
                except Exception as e:
                    print(f"⚠️ ChemBERTa encoding failed: {e}")
        
            # 4. BBBP prediction
            if 'bbbp' in self.models:
                try:
                    bbbp_results = self._predict_bbbp(smiles)
                    results['admet'].update(bbbp_results)
                    results['predictions'].update(bbbp_results)
                except Exception as e:
                    print(f"⚠️ BBBP prediction failed: {e}")
        
            # 5. ClinTox prediction
            if 'clintox' in self.models:
                try:
                    clintox_results = self._predict_clintox(smiles)
                    results['admet'].update(clintox_results)
                    results['predictions'].update(clintox_results)
                except Exception as e:
                    print(f"⚠️ ClinTox prediction failed: {e}")
        
            # 6. Clearance prediction
            if 'clearance' in self.models:
                try:
                    clearance_results = self._predict_clearance(smiles)
                    results['admet'].update(clearance_results)
                    results['predictions'].update(clearance_results)
                except Exception as e:
                    print(f"⚠️ Clearance prediction failed: {e}")
        
            # 7. XGBoost predictions
            if 'xgboost' in self.models:
                try:
                    xgb_results = self._predict_xgboost(smiles)
                    results['predictions'].update(xgb_results)
                except Exception as e:
                    print(f"⚠️ XGBoost prediction failed: {e}")
        
            # 8. TDC endpoints (hERG, DILI, Ames) - Phase 3
            if 'tdc' in self.models:
                try:
                    tdc_results = self._predict_tdc(smiles)
                    results['admet'].update(tdc_results)
                    results['predictions'].update(tdc_results)
                except Exception as e:
                    print(f"⚠️ TDC prediction failed: {e}")
        
            # Calculate summary from all predictions
            all_probs = [r.get('probability', 0.5) for r in results['predictions'].values() 
                         if isinstance(r, dict) and 'probability' in r]
        
            # Use Attention-GIN overall if available, otherwise compute from all
            if 'attention_gin' in self.models and isinstance(gin_result, tuple):
                _, overall_mean, overall_std, overall_ci_low, overall_ci_high = gin_result
            else:
                overall_mean = np.mean(all_probs) if all_probs else 0.5
                overall_std = np.std(all_probs) if len(all_probs) > 1 else 0.1
                overall_ci_low = max(0.0, overall_mean - 1.96 * overall_std)
                overall_ci_high = min(1.0, overall_mean + 1.96 * overall_std)
        
            results['summary'] = {
                'average_toxicity_probability': float(overall_mean),
                'toxicity_std': float(overall_std),
                'toxicity_ci_low': float(overall_ci_low),
                'toxicity_ci_high': float(overall_ci_high),
                'num_endpoints': len(results['predictions']),
                'toxic_endpoints': sum(1 for p in all_probs if p > 0.5),
                'overall_assessment': self._get_assessment(overall_mean)
            }
        
            return results


    
    def _predict_attention_gin(self, smiles):
        """Predict using Attention-GIN (Tox21) with MC Dropout for uncertainty."""
        model_info = self.models['attention_gin']
        model = model_info['model']

        # Convert to graph using the CORRECT featurization (matches training)
        data = self._smiles_to_graph_simple(smiles)
        if data is None:
            return {}, 0.5, 0.0, 0.5, 0.5  # Return empty results and default overall values

        # Create batch
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)

        # Try MC Dropout for uncertainty estimation
        try:
            mc_result = model.predict_mc_dropout(batch, n_samples=50)
            mean_probs = mc_result['mean_probs']
            std_probs = mc_result['std_probs']
            ci_low_probs = mc_result['ci_low']
            ci_high_probs = mc_result['ci_high']
            # mean_probs, std_probs, etc. are numpy arrays of shape [num_tasks]
            probabilities = mean_probs
            # Build endpoint results
            results = {}
            for i, endpoint in enumerate(model_info['endpoints']):
                prob = float(probabilities[i])
                results[endpoint] = {
                    'probability': prob,
                    'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                    'confidence': self._get_confidence(prob),
                    'source': 'Attention-GIN (Tox21)',
                    'model_type': 'Graph Neural Network',
                    'dataset': 'Tox21 (7,831 compounds)'
                }
            # Compute overall toxicity as the mean of the endpoint probabilities
            overall_mean = np.mean(probabilities)
            # Compute the variance of the overall mean: sum of (std_probs[i]^2) / n^2
            n = len(probabilities)
            overall_var = np.sum(std_probs**2) / (n * n)
            overall_std = np.sqrt(overall_var)
            overall_ci_low = np.maximum(0.0, overall_mean - 1.96 * overall_std)
            overall_ci_high = np.minimum(1.0, overall_mean + 1.96 * overall_std)
            return results, overall_mean, overall_std, overall_ci_low, overall_ci_high
        except Exception as e:
            print(f"⚠️ MC dropout failed in _predict_attention_gin: {e}")
            # Fallback to original method
            with torch.no_grad():
                result = model(batch, return_attention=False)
                if len(result) == 3:
                    features, predictions, _ = result
                else:
                    features, predictions = result
                probabilities = torch.sigmoid(predictions).cpu().numpy()[0]
            results = {}
            for i, endpoint in enumerate(model_info['endpoints']):
                prob = float(probabilities[i])
                results[endpoint] = {
                    'probability': prob,
                    'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                    'confidence': self._get_confidence(prob),
                    'source': 'Attention-GIN (Tox21)',
                    'model_type': 'Graph Neural Network',
                    'dataset': 'Tox21 (7,831 compounds)'
                }
            # For fallback, we don't have uncertainty from MC Dropout, so we'll use a fixed uncertainty of 0.1 (as a placeholder)
            overall_mean = np.mean(probabilities)
            overall_std = 0.1  # Fixed uncertainty
            overall_ci_low = np.maximum(0.0, overall_mean - 1.96 * overall_std)
            overall_ci_high = np.minimum(1.0, overall_mean + 1.96 * overall_std)
            return results, overall_mean, overall_std, overall_ci_low, overall_ci_high
    def _predict_bbbp(self, smiles):
        """Predict Blood-Brain Barrier Penetration"""
        model_info = self.models['bbbp']
        model = model_info['model']
        
        data = self._smiles_to_graph_simple(smiles)
        if data is None: return {}
        
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)
        
        with torch.no_grad():
            out = model(batch)
            prob = float(torch.sigmoid(out).cpu().numpy().flatten()[0])
        
        return {
            'BBBP': {
                'probability': prob,
                'prediction': 'Permeable' if prob > 0.5 else 'Non-permeable',
                'confidence': self._get_confidence(prob),
                'source': 'Attention-GIN (BBBP)',
                'model_type': 'Graph Neural Network',
                'dataset': 'BBBP (1,000 compounds)'
            }
        }

    def _predict_clintox(self, smiles):
        """Predict Clinical Toxicity"""
        model_info = self.models['clintox']
        model = model_info['model']
        
        data = self._smiles_to_graph_simple(smiles)
        if data is None: return {}
        
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)
        
        with torch.no_grad():
            out = model(batch)
            probs = torch.sigmoid(out).cpu().numpy().flatten()
        
        return {
            'FDA_APPROVED': {
                'probability': float(probs[0]),
                'prediction': 'Approved' if probs[0] > 0.5 else 'Not Approved',
                'confidence': self._get_confidence(probs[0]),
                'source': 'Attention-GIN (ClinTox)',
                'model_type': 'Graph Neural Network',
                'dataset': 'ClinTox (1,478 compounds)'
            },
            'CT_TOX': {
                'probability': float(probs[1]) if len(probs) > 1 else 0.5,
                'prediction': 'Toxic in Trials' if (len(probs) > 1 and probs[1] > 0.5) else 'Safe in Trials',
                'confidence': self._get_confidence(probs[1] if len(probs) > 1 else 0.5),
                'source': 'Attention-GIN (ClinTox)',
                'model_type': 'Graph Neural Network',
                'dataset': 'ClinTox (1,478 compounds)'
            }
        }

    def _predict_clearance(self, smiles):
        """Predict Intrinsic Clearance"""
        model_info = self.models['clearance']
        model = model_info['model']
        
        data = self._smiles_to_graph_simple(smiles)
        if data is None: return {}
        
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)
        
        with torch.no_grad():
            out = model(batch)
            # Inverse log transform: expm1
            pred_val = float(np.expm1(out.cpu().numpy().flatten()[0]))
        
        return {
            'Clearance': {
                'value': pred_val,
                'unit': 'mL/min/kg',
                'interpretation': 'High' if pred_val > 15 else 'Low' if pred_val < 5 else 'Moderate',
                'source': 'Attention-GIN (Clearance)',
                'model_type': 'Graph Neural Network',
                'dataset': 'TDC Clearance (Hepatocyte)'
            }
        }

    def _predict_xgboost(self, smiles):
        """Predict using XGBoost models"""
        features = self._extract_rdkit_features(smiles).reshape(1, -1)
        xgb_models = self.models['xgboost']['models']
        
        results = {}
        for endpoint, model_info in xgb_models.items():
            try:
                model = model_info['model']
                if hasattr(model, 'predict_proba'):
                    prob = model.predict_proba(features)[0][1]
                else:
                    prob = float(model.predict(features)[0])
                
                results[endpoint] = {
                    'probability': float(prob),
                    'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                    'confidence': self._get_confidence(prob),
                    'source': 'XGBoost'
                }
            except Exception as e:
                print(f"⚠️ XGBoost endpoint {endpoint} failed: {e}")
        
        return results

    def _get_confidence(self, prob):
        distance = abs(prob - 0.5)
        if distance > 0.4: return "Very High"
        elif distance > 0.3: return "High"
        elif distance > 0.2: return "Medium"
        elif distance > 0.1: return "Low"
        else: return "Very Low"

    def _get_assessment(self, avg_prob):
        if avg_prob >= 0.7: return "HIGH TOXICITY ⚠️"
        elif avg_prob >= 0.5: return "MODERATE TOXICITY 🟡"
        elif avg_prob >= 0.3: return "LOW TOXICITY 🟢"
        else: return "VERY LOW TOXICITY ✅"

    # Alias for backwards compatibility
    def predict_single(self, smiles):
        return self.predict(smiles)

    # Phase 3: New prediction methods
    def _predict_gps(self, smiles):
        """Predict using GPS Graph Transformer (Tox21) with MC Dropout"""
        model_info = self.models['gps']
        model = model_info['model']
        
        data = self._smiles_to_graph_simple(smiles)
        if data is None:
            return {}
        
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)
        
        try:
            mc_result = model.predict_mc_dropout(batch, n_samples=30)
            probabilities = mc_result['mean'].cpu().numpy().flatten()
            std_probs = mc_result['std'].cpu().numpy().flatten()
            
            results = {}
            for i, endpoint in enumerate(model_info['endpoints']):
                prob = float(probabilities[i]) if i < len(probabilities) else 0.5
                std = float(std_probs[i]) if i < len(std_probs) else 0.1
                results[endpoint] = {
                    'probability': prob,
                    'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                    'confidence': self._get_confidence(prob),
                    'source': 'GPS Graph Transformer (Tox21)',
                    'std': std,
                    'ci_low': max(0.0, prob - 1.96 * std),
                    'ci_high': min(1.0, prob + 1.96 * std)
                }
            return results
        except Exception as e:
            print(f"⚠️ GPS MC dropout failed: {e}")
            # Fallback
            with torch.no_grad():
                out = model(batch)
                probs = torch.sigmoid(out).cpu().numpy().flatten()
            
            results = {}
            for i, endpoint in enumerate(model_info['endpoints']):
                prob = float(probs[i]) if i < len(probs) else 0.5
                results[endpoint] = {
                    'probability': prob,
                    'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                    'confidence': self._get_confidence(prob),
                    'source': 'GPS Graph Transformer (Tox21)'
                }
            return results
    
    def _get_chemberta_embedding(self, smiles):
        """Get ChemBERTa embedding for a SMILES string"""
        if 'chemberta_encoder' not in self.models:
            return None
        encoder = self.models['chemberta_encoder']['encoder']
        return encoder.encode(smiles)
    
    def _predict_tdc(self, smiles):
        """Predict hERG, DILI, Ames using TDC datasets (placeholder - would need trained models)"""
        # For now, return placeholder predictions
        # In production, this would use models trained on TDC data
        results = {}
        for endpoint in ['hERG', 'DILI', 'AMES']:
            results[endpoint] = {
                'probability': 0.5,
                'prediction': 'Unknown',
                'confidence': 'Very Low',
                'source': f'TDC {endpoint} (placeholder - no trained model)'
            }
        return results

# ==============================================================================
# Simplified Model Architecture (Must match training scripts)
# ==============================================================================
from torch import nn
from torch_geometric.nn import GINEConv
from torch_geometric.nn.aggr import AttentionalAggregation

class SimplifiedAttentionGINet(nn.Module):
    """Simplified Architecture used for BBBP, ClinTox, Clearance"""
    
    def __init__(self, num_tasks=1, emb_dim=300, drop_ratio=0.3):
        super().__init__()
        
        self.num_layer = 5
        self.emb_dim = emb_dim
        self.drop_ratio = drop_ratio
        
        # Embeddings
        self.x_embedding1 = nn.Embedding(120, emb_dim)
        self.x_embedding2 = nn.Embedding(4, emb_dim)
        
        # GIN layers
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        for _ in range(self.num_layer):
            mlp = nn.Sequential(
                nn.Linear(emb_dim, 2 * emb_dim),
                nn.BatchNorm1d(2 * emb_dim),
                nn.ReLU(),
                nn.Linear(2 * emb_dim, emb_dim)
            )
            conv = GINEConv(mlp, edge_dim=emb_dim)
            self.convs.append(conv)
            self.batch_norms.append(nn.BatchNorm1d(emb_dim))
        
        # Edge embedding
        self.edge_embedding1 = nn.Embedding(5, emb_dim)
        self.edge_embedding2 = nn.Embedding(3, emb_dim)
        
        # Attention pooling
        gate_nn = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Linear(emb_dim, 1)
        )
        self.pool = AttentionalAggregation(gate_nn)
        
        # Predictor
        self.pred = nn.Sequential(
            nn.Linear(emb_dim, emb_dim // 2),
            nn.ReLU(),
            nn.Dropout(drop_ratio),
            nn.Linear(emb_dim // 2, num_tasks)
        )
    
    def forward(self, data):
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        h = self.x_embedding1(x[:, 0]) + self.x_embedding2(x[:, 1])
        edge_emb = self.edge_embedding1(edge_attr[:, 0]) + self.edge_embedding2(edge_attr[:, 1])
        for i in range(self.num_layer):
            h = self.convs[i](h, edge_index, edge_emb)
            h = self.batch_norms[i](h)
            h = nn.functional.relu(h)
            h = nn.functional.dropout(h, p=self.drop_ratio, training=self.training)
        h_graph = self.pool(h, batch)
        out = self.pred(h_graph)
        return out
def predict_mc_dropout(self, smiles, n_samples=50):
        """Return dict endpoint -> {mean, std, ci_low, ci_upper} using MC dropout on applicable GNN models.
        Uses unified mc_dropout_predict utility for consistent uncertainty estimation."""
        if not self.is_loaded:
            return {}
        
        from utils.molecular_featurizer import mc_dropout_predict, smiles_to_graph_simple
        
        result = {}
        # Helper to process a model key
        def process_model(key):
            try:
                model_info = self.models.get(key)
                if model_info is None:
                    return
                model = model_info.get('model') if isinstance(model_info, dict) else model_info
                if model is None:
                    return
                # Check if model has dropout layers
                has_dropout = any(isinstance(m, torch.nn.Dropout) for m in model.modules())
                if not has_dropout:
                    return
                data = smiles_to_graph_simple(smiles)
                if data is None:
                    return
                mc_result = mc_dropout_predict(model, data, n_samples=n_samples, device=self.device)
                if mc_result is None:
                    return
                
                endpoints = model_info.get('endpoints', [])
                if not endpoints:
                    return
                for i, ep in enumerate(endpoints):
                    if i < len(mc_result['mean_probs']):
                        result[ep] = {
                            'mean': float(mc_result['mean_probs'][i]),
                            'std': float(mc_result['std_probs'][i]),
                            'ci_low': float(mc_result['ci_low'][i]),
                            'ci_high': float(mc_result['ci_high'][i]),
                        }
            except Exception as e:
                logger.warning(f"MC dropout failed for model {key}: {e}")
        
        # Process all GNN models that support MC dropout
        for key in ['attention_gin', 'gps', 'bbbp', 'clintox', 'clearance']:
            process_model(key)
        
        return result


if __name__ == "__main__":
    print("Testing Unified ADMET Predictor")
    print("=" * 50)
    
    predictor = UnifiedADMETPredictor()
    
    if predictor.is_loaded:
        # Test molecules
        test_molecules = [
            ("Caffeine", "Cn1cnc2c1c(=O)n(c(=O)n2C)C"),
            ("Aspirin", "CC(=O)Oc1ccccc1C(=O)O"),
            ("Benzene", "c1ccccc1")
        ]
        
        for name, smiles in test_molecules:
            print(f"\n🧪 {name} ({smiles})")
            result = predictor.predict(smiles)
            print("   Predictions:")
            for k, v in result['predictions'].items():
                if isinstance(v, dict) and 'prediction' in v:
                    print(f"     - {k}: {v['prediction']} ({v.get('probability', 0):.2f})")
                elif k == 'Clearance':
                    print(f"     - Clearance: {v['value']:.2f} {v['unit']} ({v['interpretation']})")
                    
            print(f"   Summary: {result['summary']['overall_assessment']}")
    else:
        print("❌ No models loaded")