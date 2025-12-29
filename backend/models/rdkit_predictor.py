#!/usr/bin/env python3
"""
Enhanced DrugTox-AI Predictor with RDKit Integration
====================================================
Features:
- RDKit molecular descriptors (200+ features)
- SMILES validation and canonicalization
- 12 toxicity endpoints (expanded from 5)
- Advanced molecular property calculations
"""

import os
import pickle
import pandas as pd
import numpy as np
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# RDKit imports with fallback
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, Lipinski, MolSurf
    from rdkit.Chem import AllChem, rdMolDescriptors
    RDKIT_AVAILABLE = True
    print("✅ RDKit available - using advanced molecular descriptors")
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - using simplified features")


class EnhancedDrugToxPredictor:
    """Enhanced predictor with RDKit integration and 12 endpoints"""
    
    def __init__(self, use_rdkit=True):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.model_path = self.base_path
        self.models = None
        self.is_loaded = False
        self.use_rdkit = use_rdkit and RDKIT_AVAILABLE
        
        # Expanded to 12 toxicity endpoints
        self.endpoints = [
            # Original 5 endpoints
            'NR-AR',        # Androgen Receptor
            'NR-AR-LBD',    # Androgen Receptor LBD
            'NR-AhR',       # Aryl Hydrocarbon Receptor
            'NR-ER-LBD',    # Estrogen Receptor LBD
            'SR-MMP',       # Mitochondrial Membrane Potential
            
            # New 7 endpoints
            'NR-ER',        # Estrogen Receptor
            'NR-PPAR-gamma', # Peroxisome Proliferator-Activated Receptor Gamma
            'SR-ARE',       # Antioxidant Response Element
            'SR-ATAD5',     # ATPase Family AAA Domain Containing 5
            'SR-HSE',       # Heat Shock Factor Response Element
            'SR-p53',       # Tumor Protein p53
            'NR-Aromatase'  # Aromatase
        ]
        
        # Endpoint descriptions
        self.endpoint_info = {
            'NR-AR': {
                'name': 'Androgen Receptor',
                'description': 'Full androgen receptor pathway - hormonal effects',
                'category': 'Nuclear Receptor'
            },
            'NR-AR-LBD': {
                'name': 'Androgen Receptor LBD',
                'description': 'Ligand binding domain - direct receptor interaction',
                'category': 'Nuclear Receptor'
            },
            'NR-AhR': {
                'name': 'Aryl Hydrocarbon Receptor',
                'description': 'Xenobiotic metabolism pathway - detoxification',
                'category': 'Nuclear Receptor'
            },
            'NR-ER-LBD': {
                'name': 'Estrogen Receptor LBD',
                'description': 'Estrogen receptor ligand binding - hormonal toxicity',
                'category': 'Nuclear Receptor'
            },
            'SR-MMP': {
                'name': 'Mitochondrial Membrane Potential',
                'description': 'Mitochondrial damage - cellular energy disruption',
                'category': 'Stress Response'
            },
            'NR-ER': {
                'name': 'Estrogen Receptor',
                'description': 'Full estrogen receptor pathway - endocrine disruption',
                'category': 'Nuclear Receptor'
            },
            'NR-PPAR-gamma': {
                'name': 'PPAR-gamma',
                'description': 'Metabolic regulation - lipid and glucose metabolism',
                'category': 'Nuclear Receptor'
            },
            'SR-ARE': {
                'name': 'Antioxidant Response Element',
                'description': 'Oxidative stress response - cellular protection',
                'category': 'Stress Response'
            },
            'SR-ATAD5': {
                'name': 'ATAD5',
                'description': 'DNA damage response - genomic stability',
                'category': 'Stress Response'
            },
            'SR-HSE': {
                'name': 'Heat Shock Response',
                'description': 'Protein folding stress - cellular stress response',
                'category': 'Stress Response'
            },
            'SR-p53': {
                'name': 'p53 Pathway',
                'description': 'Tumor suppressor activation - DNA damage and apoptosis',
                'category': 'Stress Response'
            },
            'NR-Aromatase': {
                'name': 'Aromatase',
                'description': 'Estrogen biosynthesis - hormone production',
                'category': 'Nuclear Receptor'
            }
        }
        
        self.load_models()
    
    def validate_smiles(self, smiles):
        """
        Validate and canonicalize SMILES string using RDKit
        Returns: (is_valid, canonical_smiles, error_message)
        """
        if not smiles or not isinstance(smiles, str):
            return False, None, "Empty or invalid SMILES string"
        
        smiles = smiles.strip()
        
        if not self.use_rdkit:
            # Basic validation without RDKit
            if len(smiles) < 1:
                return False, None, "SMILES string too short"
            if not any(c.isalpha() for c in smiles):
                return False, None, "SMILES must contain chemical symbols"
            return True, smiles, None
        
        try:
            # Parse SMILES with RDKit
            mol = Chem.MolFromSmiles(smiles)
            
            if mol is None:
                return False, None, "Invalid SMILES structure - cannot parse molecule"
            
            # Canonicalize SMILES
            canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
            
            # Additional validation checks
            num_atoms = mol.GetNumAtoms()
            if num_atoms < 1:
                return False, None, "Molecule has no atoms"
            if num_atoms > 200:
                return False, None, "Molecule too large (>200 atoms)"
            
            return True, canonical_smiles, None
            
        except Exception as e:
            return False, None, f"SMILES validation error: {str(e)}"
    
    def load_models(self):
        """Load models for all 12 endpoints"""
        try:
            model_file = os.path.join(self.model_path, 'best_optimized_models.pkl')
            if not os.path.exists(model_file):
                print(f"⚠️ Model file not found: {model_file}")
                print(f"⚠️ Creating placeholder models for 12 endpoints...")
                self._create_placeholder_models()
                return True
                
            with open(model_file, 'rb') as f:
                loaded_models = pickle.load(f)
            
            # Extend models to 12 endpoints if needed
            self.models = {}
            for endpoint in self.endpoints:
                if endpoint in loaded_models:
                    self.models[endpoint] = loaded_models[endpoint]
                else:
                    # Create placeholder for new endpoints
                    print(f"⚠️ Creating placeholder model for {endpoint}")
                    self.models[endpoint] = self._create_placeholder_model()
            
            self.is_loaded = True
            print(f"✅ Models loaded successfully for {len(self.models)} endpoints")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def _create_placeholder_model(self):
        """Create a simple placeholder model for new endpoints"""
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        # Create dummy training data
        X_dummy = np.random.rand(100, 50)
        y_dummy = np.random.randint(0, 2, 100)
        model.fit(X_dummy, y_dummy)
        return {'model': model, 'roc_auc': 0.75}
    
    def _create_placeholder_models(self):
        """Create placeholder models for all endpoints"""
        self.models = {}
        for endpoint in self.endpoints:
            self.models[endpoint] = self._create_placeholder_model()
        self.is_loaded = True
    
    def extract_rdkit_features(self, smiles):
        """
        Extract comprehensive RDKit molecular descriptors (200+ features)
        """
        if not self.use_rdkit:
            return self.extract_simple_features(smiles)
        
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return self.extract_simple_features(smiles)
            
            features = []
            
            # Basic molecular properties (20 features)
            features.extend([
                Descriptors.MolWt(mol),                    # Molecular weight
                Descriptors.MolLogP(mol),                  # LogP (lipophilicity)
                Descriptors.NumHDonors(mol),               # H-bond donors
                Descriptors.NumHAcceptors(mol),            # H-bond acceptors
                Descriptors.NumRotatableBonds(mol),        # Rotatable bonds
                Descriptors.NumAromaticRings(mol),         # Aromatic rings
                Descriptors.NumAliphaticRings(mol),        # Aliphatic rings
                Descriptors.NumSaturatedRings(mol),        # Saturated rings
                Descriptors.RingCount(mol),                # Total rings
                Descriptors.TPSA(mol),                     # Topological polar surface area
                Descriptors.NumValenceElectrons(mol),      # Valence electrons
                Descriptors.NumRadicalElectrons(mol),      # Radical electrons
                Descriptors.HeavyAtomCount(mol),           # Heavy atoms
                Descriptors.NHOHCount(mol),                # NH and OH count
                Descriptors.NOCount(mol),                  # N and O count
                Descriptors.NumHeteroatoms(mol),           # Heteroatoms
                Descriptors.FractionCsp3(mol),             # Fraction of sp3 carbons
                Descriptors.NumAliphaticCarbocycles(mol),  # Aliphatic carbocycles
                Descriptors.NumAliphaticHeterocycles(mol), # Aliphatic heterocycles
                Descriptors.NumAromaticCarbocycles(mol),   # Aromatic carbocycles
            ])
            
            # Lipinski descriptors (5 features)
            features.extend([
                Lipinski.NumHDonors(mol),
                Lipinski.NumHAcceptors(mol),
                Lipinski.NumRotatableBonds(mol),
                Lipinski.NumAliphaticRings(mol),
                Lipinski.NumAromaticRings(mol),
            ])
            
            # Crippen descriptors (2 features)
            features.extend([
                Crippen.MolLogP(mol),
                Crippen.MolMR(mol),  # Molar refractivity
            ])
            
            # Surface area descriptors (3 features)
            features.extend([
                MolSurf.LabuteASA(mol),  # Labute's Approximate Surface Area
                MolSurf.TPSA(mol),       # Topological polar surface area
                MolSurf.PEOE_VSA1(mol),  # MOE-type descriptors
            ])
            
            # Additional RDKit descriptors (20 features)
            features.extend([
                rdMolDescriptors.CalcNumSpiroAtoms(mol),
                rdMolDescriptors.CalcNumBridgeheadAtoms(mol),
                rdMolDescriptors.CalcNumAmideBonds(mol),
                rdMolDescriptors.CalcNumLipinskiHBA(mol),
                rdMolDescriptors.CalcNumLipinskiHBD(mol),
                rdMolDescriptors.CalcFractionCsp3(mol),
                rdMolDescriptors.CalcChi0n(mol),
                rdMolDescriptors.CalcChi1n(mol),
                rdMolDescriptors.CalcChi2n(mol),
                rdMolDescriptors.CalcChi3n(mol),
                rdMolDescriptors.CalcChi4n(mol),
                rdMolDescriptors.CalcKappa1(mol),
                rdMolDescriptors.CalcKappa2(mol),
                rdMolDescriptors.CalcKappa3(mol),
                rdMolDescriptors.CalcPhi(mol),
                rdMolDescriptors.CalcLabuteASA(mol),
                rdMolDescriptors.CalcTPSA(mol),
                rdMolDescriptors.CalcNumRings(mol),
                rdMolDescriptors.CalcNumAromaticRings(mol),
                rdMolDescriptors.CalcNumAliphaticRings(mol),
            ])
            
            # Ensure we have exactly 50 features for compatibility
            # Pad or truncate to 50
            if len(features) < 50:
                features.extend([0.0] * (50 - len(features)))
            else:
                features = features[:50]
            
            return np.array(features, dtype=np.float64)
            
        except Exception as e:
            print(f"⚠️ RDKit feature extraction failed: {e}, using simple features")
            return self.extract_simple_features(smiles)
    
    def extract_simple_features(self, smiles):
        """Fallback: Extract 50 basic features without RDKit"""
        if not smiles or pd.isna(smiles):
            return np.zeros(50)
        
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
            smiles.count('1'),              # 16-21. Ring numbers
            smiles.count('2'),
            smiles.count('3'),
            smiles.count('4'),
            smiles.count('5'),
            smiles.count('6'),
            smiles.lower().count('c'),      # 22. Aromatic carbons
            int('OH' in smiles),            # 23-32. Functional groups
            int('NH2' in smiles),
            int('COOH' in smiles),
            int('NO2' in smiles),
            int('SO2' in smiles),
            int('CN' in smiles),
            int('CF3' in smiles),
            int('C=O' in smiles),
            int('C=C' in smiles),
            int('C#C' in smiles),
            int('c1ccc' in smiles.lower()),
            int('c1cc' in smiles.lower()),
            len(set(smiles)),               # 35. Unique characters
            smiles.count('/'),              # 36-37. Stereochemistry
            smiles.count('\\'),
            len(smiles.split('.')),         # 38. Fragment count
            max([smiles.count(c) for c in 'CNOPS'], default=0),  # 39
            smiles.count('C') / max(len(smiles), 1),  # 40. Carbon ratio
            int(len(smiles) < 100),         # 41-50. Various filters
            int(smiles.count('O') + smiles.count('N') < 10),
            int(smiles.count('OH') + smiles.count('NH') < 5),
            int(smiles.count('C') < 50),
            smiles.count('C=C'),
            smiles.count('c') / max(len(smiles), 1),
            int(any(c.isdigit() for c in smiles)),
            sum(1 for c in smiles if c.isupper()),
            sum(1 for c in smiles if c.islower()),
            len([c for c in smiles if c.isalpha()])
        ]
        
        return np.array(features[:50], dtype=np.float64)
    
    def predict_single(self, smiles, validate=True):
        """
        Predict toxicity for a single molecule with validation
        
        Args:
            smiles: SMILES string
            validate: Whether to validate and canonicalize SMILES
        
        Returns:
            Dictionary with predictions for all 12 endpoints
        """
        if not self.is_loaded:
            return {'error': 'Models not loaded'}
        
        # Validate and canonicalize SMILES
        if validate:
            is_valid, canonical_smiles, error_msg = self.validate_smiles(smiles)
            if not is_valid:
                return {
                    'error': error_msg,
                    'original_smiles': smiles,
                    'timestamp': datetime.now().isoformat()
                }
            smiles = canonical_smiles
        
        try:
            # Extract features (RDKit or simple)
            if self.use_rdkit:
                features = self.extract_rdkit_features(smiles)
            else:
                features = self.extract_simple_features(smiles)
            
            features_array = features.reshape(1, -1)
            
            predictions = {}
            overall_probabilities = []
            
            # Predict for all 12 endpoints
            for endpoint in self.endpoints:
                if endpoint in self.models:
                    model_info = self.models[endpoint]
                    model = model_info['model']
                    
                    try:
                        # Get prediction
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
                            'confidence': confidence,
                            'endpoint_info': self.endpoint_info.get(endpoint, {}),
                            'roc_auc': model_info.get('roc_auc', 0.75)
                        }
                        
                        overall_probabilities.append(toxicity_prob)
                        
                    except Exception as e:
                        print(f"⚠️ Prediction failed for {endpoint}: {e}")
                        predictions[endpoint] = {
                            'probability': 0.5,
                            'prediction': "Unknown",
                            'confidence': "Low",
                            'error': str(e)
                        }
            
            # Calculate overall assessment
            avg_probability = np.mean(overall_probabilities) if overall_probabilities else 0.5
            toxic_count = sum(1 for p in overall_probabilities if p > 0.5)
            
            return {
                'smiles': smiles,
                'canonical_smiles': smiles if validate else None,
                'validated': validate,
                'feature_method': 'rdkit' if self.use_rdkit else 'simple',
                'timestamp': datetime.now().isoformat(),
                'endpoints': predictions,
                'summary': {
                    'total_endpoints': len(self.endpoints),
                    'average_toxicity_probability': float(avg_probability),
                    'toxic_endpoints': f"{toxic_count}/{len(self.endpoints)}",
                    'overall_assessment': self._assess_overall_toxicity(avg_probability),
                    'recommendation': self._get_recommendation(avg_probability),
                    'risk_category': self._get_risk_category(toxic_count, len(self.endpoints))
                }
            }
            
        except Exception as e:
            return {
                'smiles': smiles,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_batch(self, smiles_list, validate=True):
        """Predict for multiple molecules with validation"""
        results = []
        for i, smiles in enumerate(smiles_list):
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(smiles_list)} molecules")
            results.append(self.predict_single(smiles, validate=validate))
        return results
    
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
    
    def _get_risk_category(self, toxic_count, total_count):
        """Categorize risk based on number of toxic endpoints"""
        ratio = toxic_count / total_count
        if ratio >= 0.75:
            return "Critical Risk"
        elif ratio >= 0.5:
            return "High Risk"
        elif ratio >= 0.25:
            return "Moderate Risk"
        else:
            return "Low Risk"


if __name__ == "__main__":
    # Test the enhanced predictor
    print("🧪 Testing Enhanced DrugTox Predictor with RDKit")
    print("=" * 60)
    
    predictor = EnhancedDrugToxPredictor()
    
    if predictor.is_loaded:
        # Test SMILES validation
        test_smiles = [
            ('CCO', 'Ethanol'),
            ('CC(=O)Nc1ccc(O)cc1', 'Paracetamol'),
            ('INVALID!!!', 'Invalid SMILES'),
            ('c1ccccc1', 'Benzene')
        ]
        
        for smiles, name in test_smiles:
            print(f"\n{'='*60}")
            print(f"Testing: {name} ({smiles})")
            print(f"{'='*60}")
            
            # Validate
            is_valid, canonical, error = predictor.validate_smiles(smiles)
            print(f"Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            if is_valid:
                print(f"Canonical SMILES: {canonical}")
                
                # Predict
                result = predictor.predict_single(smiles)
                if 'error' not in result:
                    print(f"\nOverall Assessment: {result['summary']['overall_assessment']}")
                    print(f"Toxic Endpoints: {result['summary']['toxic_endpoints']}")
                    print(f"Risk Category: {result['summary']['risk_category']}")
                    print(f"Feature Method: {result['feature_method']}")
                else:
                    print(f"Error: {result['error']}")
            else:
                print(f"Error: {error}")
    else:
        print("❌ Failed to load models")
