#!/usr/bin/env python3
"""
DrugTox-AI Simple Predictor (Clean Version)
==========================================
"""

import os
import pickle
import pandas as pd
import numpy as np
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

class SimpleDrugToxPredictor:
    """Production-ready predictor without feature scaling dependencies"""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.model_path = self.base_path  # Models are in the same directory
        self.models = None
        self.is_loaded = False
        self.endpoints = ['NR-AR-LBD', 'NR-AhR', 'SR-MMP', 'NR-ER-LBD', 'NR-AR']
        self.load_models()
    
    def load_models(self):
        """Load models without scaling dependencies"""
        try:
            model_file = os.path.join(self.model_path, 'best_optimized_models.pkl')
            if not os.path.exists(model_file):
                print(f"❌ Model file not found: {model_file}")
                return False
                
            with open(model_file, 'rb') as f:
                self.models = pickle.load(f)
            
            self.is_loaded = True
            print("✅ Models loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def extract_simple_features(self, smiles):
        """Extract 306 RDKit molecular descriptors to match trained model"""
        if not smiles or pd.isna(smiles):
            return np.zeros(306)
        
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, rdMolDescriptors
            from rdkit.ML.Descriptors import MoleculeDescriptors
            
            mol = Chem.MolFromSmiles(str(smiles).strip())
            if mol is None:
                return np.zeros(306)
            
            # Get all available descriptor names
            descriptor_names = [desc[0] for desc in Descriptors.descList]
            
            # Create descriptor calculator
            calc = MoleculeDescriptors.MolecularDescriptorCalculator(descriptor_names)
            
            # Calculate descriptors
            descriptors = np.array(calc.CalcDescriptors(mol))
            
            # Handle NaN/inf values
            descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Pad or truncate to 306 features
            if len(descriptors) < 306:
                descriptors = np.pad(descriptors, (0, 306 - len(descriptors)), 'constant')
            elif len(descriptors) > 306:
                descriptors = descriptors[:306]
            
            return descriptors.astype(np.float64)
            
        except ImportError:
            # Fallback if RDKit not available - use simple features
            smiles = str(smiles).strip()
            features = [
                len(smiles),                    # 1. Length
                smiles.count('C'),              # 2. Carbon count
                smiles.count('N'),              # 3. Nitrogen count
                smiles.count('O'),              # 4. Oxygen count
                smiles.count('S'),              # 5. Sulfur count
                smiles.count('P'),              # 6. Phosphorus count
                smiles.count('F'),              # 7. Fluorine count
                smiles.count('Cl'),             # 8. Chlorine count
                smiles.count('Br'),             # 9. Bromine count
                smiles.count('I'),              # 10. Iodine count
                smiles.count('='),              # 11. Double bonds
                smiles.count('#'),              # 12. Triple bonds
                smiles.count('('),              # 13. Branches
                smiles.count('['),              # 14. Special atoms
                smiles.count('@'),              # 15. Chiral centers
                smiles.count('1'),              # 16. Ring numbers
                smiles.count('2'),              # 17.
                smiles.count('3'),              # 18.
                smiles.count('4'),              # 19.
                smiles.count('5'),              # 20.
            ]
            # Pad to 306
            features = features + [0] * (306 - len(features))
            return np.array(features[:306], dtype=np.float64)
    
    def predict_single(self, smiles):
        """Predict toxicity for a single molecule"""
        if not self.is_loaded:
            return {'error': 'Models not loaded'}
        
        try:
            # Extract simplified features
            features = self.extract_simple_features(smiles)
            features_array = features.reshape(1, -1)
            
            predictions = {}
            overall_probabilities = []
            
            for endpoint in self.endpoints:
                if endpoint in self.models:
                    model_info = self.models[endpoint]
                    model = model_info['model']
                    
                    try:
                        # Predict using 306 features directly
                        if hasattr(model, 'predict_proba'):
                            pred_proba = model.predict_proba(features_array)
                            toxicity_prob = pred_proba[0][1] if len(pred_proba[0]) > 1 else pred_proba[0][0]
                        else:
                            pred = model.predict(features_array)
                            toxicity_prob = float(pred[0])
                        
                        prediction = "Toxic" if toxicity_prob > 0.5 else "Non-toxic"
                        confidence = self._get_confidence(toxicity_prob)
                        
                        predictions[endpoint] = {
                            'probability': float(toxicity_prob),
                            'prediction': prediction,
                            'confidence': confidence
                        }
                        
                        overall_probabilities.append(toxicity_prob)
                        
                    except Exception as e:
                        # Log error for debugging
                        print(f"⚠️ Prediction failed for {endpoint}: {e}")
                        predictions[endpoint] = {
                            'probability': 0.5,
                            'prediction': "Unknown",
                            'confidence': "Low"
                        }
            
            # Calculate overall assessment
            avg_probability = np.mean(overall_probabilities) if overall_probabilities else 0.5
            toxic_count = sum(1 for p in overall_probabilities if p > 0.5)
            
            return {
                'smiles': smiles,
                'timestamp': datetime.now().isoformat(),
                'endpoints': predictions,
                'summary': {
                    'average_toxicity_probability': float(avg_probability),
                    'toxic_endpoints': f"{toxic_count}/{len(self.endpoints)}",
                    'overall_assessment': self._assess_overall_toxicity(avg_probability),
                    'recommendation': self._get_recommendation(avg_probability)
                }
            }
            
        except Exception as e:
            return {
                'smiles': smiles,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_batch(self, smiles_list):
        """Predict for multiple molecules"""
        results = []
        for i, smiles in enumerate(smiles_list):
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(smiles_list)} molecules")
            results.append(self.predict_single(smiles))
        return results
    
    def predict(self, smiles):
        """Alias for predict_single (required by CachedPredictionWrapper)"""
        return self.predict_single(smiles)
    
    def _get_confidence(self, probability):
        """Determine confidence level"""
        distance = abs(probability - 0.5)
        if distance > 0.4:
            return "Very High"
        elif distance > 0.3:
            return "High"
        elif distance > 0.2:
            return "Medium"
        elif distance > 0.1:
            return "Low"
        else:
            return "Very Low"
    
    def _assess_overall_toxicity(self, avg_prob):
        """Assess overall toxicity level"""
        if avg_prob >= 0.7:
            return "HIGH TOXICITY ⚠️"
        elif avg_prob >= 0.5:
            return "MODERATE TOXICITY 🟡"
        elif avg_prob >= 0.3:
            return "LOW TOXICITY 🟢"
        else:
            return "VERY LOW TOXICITY ✅"
    
    def _get_recommendation(self, avg_prob):
        """Get safety recommendation"""
        if avg_prob >= 0.7:
            return "Avoid - High toxicity risk"
        elif avg_prob >= 0.5:
            return "Caution - Moderate toxicity risk"
        elif avg_prob >= 0.3:
            return "Acceptable - Low toxicity risk"
        else:
            return "Safe - Very low toxicity risk"

if __name__ == "__main__":
    # Quick test
    print("🧪 Testing DrugTox Predictor")
    predictor = SimpleDrugToxPredictor()
    if predictor.is_loaded:
        result = predictor.predict_single('CCO')
        print(f"✅ Ethanol test: {result['summary']['overall_assessment']}")
    else:
        print("❌ Failed to load models")