#!/usr/bin/env python3
"""
Unified ADMET Predictor
=======================
Combines multiple models for comprehensive ADMET property prediction.

Models:
1. Attention-GIN (Tox21) - Trained with ROC-AUC 0.8368
2. XGBoost (5 NR endpoints) - From best_optimized_models.pkl
3. Future: BBBP, Caco2, Clearance, HLM_CLint models
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

class UnifiedADMETPredictor:
    """Unified predictor for all ADMET properties"""
    
    TOX21_ENDPOINTS = [
        'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD',
        'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
    ]
    
    def __init__(self):
        self.models = {}
        self.is_loaded = False
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
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
        
        self.is_loaded = models_loaded > 0
        print(f"✅ Unified ADMET Predictor: {models_loaded} model types loaded")
    
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

    def _smiles_to_graph_simple(self, smiles):
        """Convert SMILES to PyG Data object (Simple Featurization for SimplifiedGIN)"""
        try:
            from rdkit import Chem
            from torch_geometric.data import Data
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None: return None
            
            # Constants matching training script
            ATOM_LIST = list(range(1, 119))
            CHIRALITY_LIST = [
                Chem.rdchem.ChiralType.CHI_UNSPECIFIED,
                Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW,
                Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW,
                Chem.rdchem.ChiralType.CHI_OTHER
            ]
            BOND_LIST = [
                Chem.rdchem.BondType.SINGLE,
                Chem.rdchem.BondType.DOUBLE,
                Chem.rdchem.BondType.TRIPLE,
                Chem.rdchem.BondType.AROMATIC
            ]
            BONDDIR_LIST = [
                Chem.rdchem.BondDir.NONE,
                Chem.rdchem.BondDir.ENDUPRIGHT,
                Chem.rdchem.BondDir.ENDDOWNRIGHT
            ]
            
            # Atom features
            atom_features = []
            for atom in mol.GetAtoms():
                atom_type = atom.GetAtomicNum()
                chirality = atom.GetChiralTag()
                atom_features.append([
                    ATOM_LIST.index(atom_type) if atom_type in ATOM_LIST else len(ATOM_LIST),
                    CHIRALITY_LIST.index(chirality) if chirality in CHIRALITY_LIST else 0
                ])
            
            x = torch.tensor(atom_features, dtype=torch.long)
            
            # Edge features
            edge_index = []
            edge_attr = []
            for bond in mol.GetBonds():
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()
                bond_type = bond.GetBondType()
                bond_dir = bond.GetBondDir()
                
                bond_feat = [
                    BOND_LIST.index(bond_type) if bond_type in BOND_LIST else len(BOND_LIST),
                    BONDDIR_LIST.index(bond_dir) if bond_dir in BONDDIR_LIST else 0
                ]
                
                edge_index.extend([[i, j], [j, i]])
                edge_attr.extend([bond_feat, bond_feat])
            
            if len(edge_index) == 0:
                edge_index = torch.zeros((2, 0), dtype=torch.long)
                edge_attr = torch.zeros((0, 2), dtype=torch.long)
            else:
                edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
                edge_attr = torch.tensor(edge_attr, dtype=torch.long)
            
            return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
        except Exception as e:
            print(f"Error in graph conversion: {e}")
            return None
    
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
        """Convert SMILES to PyG Data object"""
        from rdkit import Chem
        from torch_geometric.data import Data
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Atom features
        atom_features = []
        for atom in mol.GetAtoms():
            features = [
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                int(atom.GetHybridization()),
                int(atom.GetIsAromatic()),
                atom.GetTotalNumHs(),
                int(atom.IsInRing()),
                atom.GetImplicitValence(),
                int(atom.GetChiralTag())
            ]
            atom_features.append(features)
        
        x = torch.tensor(atom_features, dtype=torch.float)
        
        # Edge indices
        edge_index = []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            edge_index.append([i, j])
            edge_index.append([j, i])
        
        if len(edge_index) == 0:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
        else:
            edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        
        return Data(x=x, edge_index=edge_index)
    
    def _extract_rdkit_features(self, smiles):
        """Extract 306 RDKit descriptors for XGBoost"""
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors
            from rdkit.ML.Descriptors import MoleculeDescriptors
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return np.zeros(306)
            
            descriptor_names = [desc[0] for desc in Descriptors.descList]
            calc = MoleculeDescriptors.MolecularDescriptorCalculator(descriptor_names)
            descriptors = np.array(calc.CalcDescriptors(mol))
            descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)
            
            if len(descriptors) < 306:
                descriptors = np.pad(descriptors, (0, 306 - len(descriptors)), 'constant')
            elif len(descriptors) > 306:
                descriptors = descriptors[:306]
            
            return descriptors.astype(np.float64)
        except:
            return np.zeros(306)
    
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
                gin_results = self._predict_attention_gin(smiles)
                results['tox21'] = gin_results
                results['predictions'].update(gin_results)
            except Exception as e:
                print(f"⚠️ Attention-GIN prediction failed: {e}")
        
        # 2. XGBoost predictions (fallback/additional endpoints)
        if 'xgboost' in self.models:
            try:
                xgb_results = self._predict_xgboost(smiles)
                # Only add XGBoost results if not already covered by GIN
                for endpoint, result in xgb_results.items():
                    if endpoint not in results['predictions']:
                        results['predictions'][endpoint] = result
            except Exception as e:
                print(f"⚠️ XGBoost prediction failed: {e}")
        
        # 3. BBBP Predictions
        if 'bbbp' in self.models:
            try:
                results['predictions'].update(self._predict_bbbp(smiles))
            except Exception as e:
                print(f"⚠️ BBBP prediction failed: {e}")
                
        # 4. ClinTox Predictions
        if 'clintox' in self.models:
            try:
                results['predictions'].update(self._predict_clintox(smiles))
            except Exception as e:
                print(f"⚠️ ClinTox prediction failed: {e}")
                
        # 5. Clearance Predictions
        if 'clearance' in self.models:
            try:
                results['predictions'].update(self._predict_clearance(smiles))
            except Exception as e:
                print(f"⚠️ Clearance prediction failed: {e}")
        
        # Calculate summary
        all_probs = [r.get('probability', 0.5) for r in results['predictions'].values() 
                     if isinstance(r, dict) and 'probability' in r]
        
        results['summary'] = {
            'average_toxicity_probability': float(np.mean(all_probs)) if all_probs else 0.5,
            'num_endpoints': len(results['predictions']),
            'toxic_endpoints': sum(1 for p in all_probs if p > 0.5),
            'overall_assessment': self._get_assessment(np.mean(all_probs) if all_probs else 0.5)
        }
        
        return results
    
    
    def _predict_attention_gin(self, smiles):
        """Predict using Attention-GIN (Tox21)"""
        model_info = self.models['attention_gin']
        model = model_info['model']
        
        # Convert to graph
        data = self._smiles_to_graph(smiles)
        if data is None:
            return {}
        
        # Create batch
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(self.device)
        
        # Predict
        with torch.no_grad():
            output, _ = model(batch)
            probabilities = torch.sigmoid(output).cpu().numpy()[0]
        
        # Map to endpoints
        results = {}
        for i, endpoint in enumerate(model_info['endpoints']):
            prob = float(probabilities[i])
            results[endpoint] = {
                'probability': prob,
                'prediction': 'Toxic' if prob > 0.5 else 'Non-toxic',
                'confidence': self._get_confidence(prob),
                'source': 'Attention-GIN (Tox21)'
            }
        
        return results
    
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
            prob = float(torch.sigmoid(out).cpu().numpy()[0])
            
        return {
            'BBBP': {
                'probability': prob,
                'prediction': 'Permeable' if prob > 0.5 else 'Non-permeable',
                'confidence': self._get_confidence(prob),
                'source': 'Attention-GIN (BBBP)'
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
            probs = torch.sigmoid(out).cpu().numpy()[0]
            
        return {
            'FDA_APPROVED': {
                'probability': float(probs[0]),
                'prediction': 'Approved' if probs[0] > 0.5 else 'Not Approved',
                'confidence': self._get_confidence(probs[0]),
                'source': 'Attention-GIN (ClinTox)'
            },
            'CT_TOX': {
                'probability': float(probs[1]),
                'prediction': 'Toxic in Trials' if probs[1] > 0.5 else 'Safe in Trials',
                'confidence': self._get_confidence(probs[1]),
                'source': 'Attention-GIN (ClinTox)'
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
            pred_val = float(np.expm1(out.cpu().numpy()[0]))
            
        return {
            'Clearance': {
                'value': pred_val,
                'unit': 'mL/min/kg',
                'interpretation': 'High' if pred_val > 15 else 'Low' if pred_val < 5 else 'Moderate',
                'source': 'Attention-GIN (Clearance)'
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
