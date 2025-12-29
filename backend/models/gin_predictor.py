"""
Multi-Model GIN Predictor for ADMET Properties
Loads and manages all trained GIN models from data_packages directory
"""

import os
import sys
import torch
import yaml
import numpy as np
from pathlib import Path

try:
    from .gin_model import GINModel, smiles_to_graph_pyg, load_gin_model
    from torch_geometric.data import Data, Batch
except ImportError:
    from gin_model import GINModel, smiles_to_graph_pyg, load_gin_model
    from torch_geometric.data import Data, Batch

import torch.nn.functional as F

# Add paths for imports
# gin_predictor.py is in DeNovo-main/backend/models/
# We need to access DeNovo-main/MODELS/tox21_model_full_package/ for dataset
backend_dir = Path(__file__).parent.parent  # DeNovo-main/backend
project_dir = backend_dir.parent  # DeNovo-main
tox21_package = project_dir / "data_packages" / "tox21_model_full_package"

if str(tox21_package) not in sys.path:
    sys.path.insert(0, str(tox21_package))

# Import dataset constants for SMILES preprocessing
from dataset.dataset_test import ATOM_LIST, CHIRALITY_LIST, BOND_LIST, BONDDIR_LIST
from rdkit import Chem

class MultiModelPredictor:
    """Manages predictions across multiple GIN models"""
    
    def __init__(self, models_base_path=None):
        """
        Initialize multi-model predictor
        
        Args:
            models_base_path: Path to data_packages directory (default: auto-detect)
        """
        if models_base_path is None:
            # Auto-detect MODELS directory
            backend_dir = Path(__file__).parent.parent
            project_dir = backend_dir.parent
            models_base_path = project_dir / "data_packages"
        
        self.models_base_path = Path(models_base_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}
        self.configs = {}
        self.is_loaded = False
        
        # Model metadata - Maps model IDs to their file paths and properties
        self.model_info = {
            'tox21': {
                'name': 'Tox21',
                'display_name': 'Tox21 Toxicity',
                'path': 'tox21_model_full_package/model.pth',
                'type': 'classification',
                'task': 'toxicity',
                'description': 'Tox21 multi-assay toxicity prediction (12 tasks)',
                'num_tasks': 12
            },
            'clintox': {
                'name': 'Clinical Toxicity',
                'display_name': 'Clinical Toxicity',
                'path': 'pretrained_gin_ClinTox_model.pth',
                'type': 'classification',
                'task': 'toxicity',
                'description': 'FDA clinical trial toxicity and approval prediction',
                'num_tasks': 2
            },
            'bbbp': {
                'name': 'BBBP',
                'display_name': 'Blood-Brain Barrier Penetration',
                'path': 'bbbp_model_full_package',
                'type': 'classification',
                'task': 'distribution',
                'description': 'BBB permeability for CNS targeting assessment',
                'num_tasks': 1
            },
            'caco2': {
                'name': 'Caco-2',
                'display_name': 'Caco-2 Permeability',
                'path': 'caco2_model_full_package',
                'type': 'regression',
                'task': 'absorption',
                'description': 'Intestinal epithelial permeability prediction',
                'num_tasks': 1
            },
            'clearance': {
                'name': 'Clearance',
                'display_name': 'Intrinsic Clearance',
                'path': 'clearance_model_full_package',
                'type': 'regression',
                'task': 'metabolism',
                'description': 'Enzyme-mediated clearance rate prediction',
                'num_tasks': 1
            },
            'hlm_clint': {
                'name': 'HLM CLint',
                'display_name': 'HLM Intrinsic Clearance',
                'path': 'hlm_clint_model_full_package',
                'type': 'regression',
                'task': 'metabolism',
                'description': 'Human liver microsomal clearance prediction',
                'num_tasks': 1
            }
        }
        
        self.load_models()
    
    def load_models(self):
        """Load all available models"""
        print(f"\n🔄 Loading models from: {self.models_base_path}")
        
        if not self.models_base_path.exists():
            print(f"❌ data_packages directory not found: {self.models_base_path}")
            return False
        
        loaded_count = 0
        
        for model_id, info in self.model_info.items():
            try:
                model_path = self.models_base_path / info['path']
                
                if model_id in ['tox21', 'clintox']:
                    # Tox21 and ClinTox models are single .pth files
                    if model_path.exists():
                        # Get num_tasks from model_info
                        num_tasks = info.get('num_tasks', 2)
                        self.models[model_id] = {
                            'model': self._load_single_model(model_path, num_tasks=num_tasks, task_type='classification'),
                            'info': info
                        }
                        loaded_count += 1
                        print(f"  ✅ Loaded {info['display_name']} ({info['type']}) - {num_tasks} tasks")
                    else:
                        print(f"  ⚠️ {info['display_name']} model file not found at {model_path}")
                else:
                    # Package models have model.pth and config
                    if model_path.is_dir():
                        model_file = model_path / 'model.pth'
                        config_file = model_path / 'config_finetune.yaml'
                        
                        if model_file.exists():
                            config = None
                            if config_file.exists():
                                with open(config_file, 'r') as f:
                                    config = yaml.safe_load(f)
                            
                            # Get num_tasks and task_type from model_info
                            task_type = info['type']  # 'classification' or 'regression'
                            num_tasks = info.get('num_tasks', 1)
                            self.models[model_id] = {
                                'model': self._load_single_model(model_file, num_tasks=num_tasks, task_type=task_type),
                                'config': config,
                                'info': info
                            }
                            loaded_count += 1
                            print(f"  ✅ Loaded {info['display_name']} ({info['type']})")
                        else:
                            print(f"  ⚠️ {info['display_name']} model.pth not found in package")
                    else:
                        print(f"  ⚠️ {info['display_name']} package directory not found")
                        
            except Exception as e:
                print(f"  ❌ Error loading {info['display_name']}: {e}")
        
        self.is_loaded = loaded_count > 0
        print(f"\n✅ Loaded {loaded_count}/{len(self.model_info)} models successfully")
        return self.is_loaded
    
    def _load_single_model(self, model_path, num_tasks=12, task_type='classification'):
        """
        Load a single GIN model with proper architecture (GINet)
        
        Args:
            model_path: Path to .pth checkpoint
            num_tasks: Number of prediction tasks (12 for Tox21, 2 for ClinTox, 1 for others)
            task_type: 'classification' or 'regression'
        
        Returns:
            Loaded GIN model ready for inference
        """
        try:
            # For packaged models, load GINet from the package's models directory
            model_path = Path(model_path)
            package_dir = model_path.parent if model_path.name == 'model.pth' else None
            
            if package_dir and (package_dir / 'models' / 'ginet_finetune.py').exists():
                # Load GINet from package
                sys.path.insert(0, str(package_dir / 'models'))
                from ginet_finetune import GINet
                sys.path.pop(0)
                
                # Create GINet model (matches config: 5 layers, 300 emb_dim, 512 feat_dim)
                model = GINet(num_tasks=num_tasks, num_layer=5, emb_dim=300, 
                              feat_dim=512, drop_ratio=0.3, pool='mean')
                
                # Load checkpoint
                checkpoint = torch.load(model_path, map_location=self.device)
                model.load_state_dict(checkpoint, strict=True)
                
                model.to(self.device)
                model.eval()
                return model
            else:
                # Fallback to GINModel for old models (tox21, clintox)
                model = load_gin_model(
                    checkpoint_path=model_path,
                    num_tasks=num_tasks,
                    device=self.device
                )
                return model
            
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            raise
    
    def predict(self, smiles, models=None):
        """
        Make REAL predictions using trained GIN models
        
        Args:
            smiles (str): SMILES string of molecule
            models (list): List of model IDs to use (None = all models)
        
        Returns:
            dict: Real predictions from each trained model
        """
        if not self.is_loaded:
            raise RuntimeError("No models loaded")
        
        if models is None:
            models = list(self.models.keys())
        
        # Convert SMILES to PyTorch Geometric Data object
        try:
            # Use the exact same preprocessing as inference_parallel.py
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'error': 'Invalid SMILES string'}
            mol = Chem.AddHs(mol)
            
            type_idx = []
            chirality_idx = []
            for atom in mol.GetAtoms():
                type_idx.append(ATOM_LIST.index(atom.GetAtomicNum()))
                chirality_idx.append(CHIRALITY_LIST.index(atom.GetChiralTag()))
            
            x1 = torch.tensor(type_idx, dtype=torch.long).view(-1, 1)
            x2 = torch.tensor(chirality_idx, dtype=torch.long).view(-1, 1)
            x = torch.cat([x1, x2], dim=-1)
            
            row, col, edge_feat = [], [], []
            for bond in mol.GetBonds():
                start, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
                row += [start, end]
                col += [end, start]
                edge_feat.append([
                    BOND_LIST.index(bond.GetBondType()),
                    BONDDIR_LIST.index(bond.GetBondDir())
                ])
                edge_feat.append([
                    BOND_LIST.index(bond.GetBondType()),
                    BONDDIR_LIST.index(bond.GetBondDir())
                ])
            
            if len(row) == 0:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                edge_attr = torch.empty((0, 2), dtype=torch.long)
            else:
                edge_index = torch.tensor([row, col], dtype=torch.long)
                edge_attr = torch.tensor(np.array(edge_feat), dtype=torch.long).view(-1, 2)
            
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data.batch = torch.zeros(x.size(0), dtype=torch.long)
            
            # Move to device
            data = data.to(self.device)
            
        except Exception as e:
            return {'error': f'Failed to process SMILES: {str(e)}'}
        
        results = {}
        
        for model_id in models:
            if model_id not in self.models:
                results[model_id] = {
                    'error': f"Model '{model_id}' not available"
                }
                continue
            
            try:
                model_data = self.models[model_id]
                model = model_data['model']
                info = model_data['info']
                
                # Run inference
                with torch.no_grad():
                    output = model(data)
                    
                    # Handle models that return (features, predictions) vs just predictions
                    if isinstance(output, tuple) and len(output) == 2:
                        _, predictions = output
                    else:
                        predictions = output
                    
                    if info['type'] == 'classification':
                        # Apply sigmoid for binary classification
                        probabilities = torch.sigmoid(predictions).cpu().numpy()[0]
                        
                        if model_id == 'tox21':
                            # Multi-task: return average toxicity probability
                            avg_prob = float(np.mean(probabilities))
                            prediction = 1 if avg_prob > 0.5 else 0
                            
                            results[model_id] = {
                                'prediction': int(prediction),
                                'probability': avg_prob,
                                'label': 'Toxic' if prediction == 1 else 'Non-toxic',
                                'type': 'classification',
                                'task_probabilities': probabilities.tolist()
                            }
                        elif model_id == 'clintox':
                            # 2 tasks: [FDA approval, Clinical toxicity]
                            fda_prob = float(probabilities[0])
                            tox_prob = float(probabilities[1])
                            
                            # Overall toxicity = clinical toxicity probability
                            prediction = 1 if tox_prob > 0.5 else 0
                            
                            results[model_id] = {
                                'prediction': int(prediction),
                                'probability': tox_prob,
                                'label': 'Toxic' if prediction == 1 else 'Non-toxic',
                                'type': 'classification',
                                'fda_approval_prob': fda_prob,
                                'clinical_tox_prob': tox_prob
                            }
                        else:
                            # Single binary classification (BBBP)
                            prob = float(probabilities[0])
                            prediction = 1 if prob > 0.5 else 0
                            
                            # For BBBP: 1 = BBB permeable, 0 = not permeable
                            if model_id == 'bbbp':
                                label = 'BBB Permeable' if prediction == 1 else 'Non-permeable'
                            else:
                                label = 'Positive' if prediction == 1 else 'Negative'
                            
                            results[model_id] = {
                                'prediction': int(prediction),
                                'probability': prob,
                                'label': label,
                                'type': 'classification'
                            }
                    
                    else:  # Regression
                        raw_value = float(predictions.cpu().numpy()[0, 0])
                        
                        # Apply transformations based on model type
                        if model_id in ['clearance', 'hlm_clint']:
                            # Models output log-scale values -> apply exp() for linear scale
                            # Match inference_parallel.py: math.exp(raw_value)
                            linear_value = float(np.exp(raw_value))
                            
                            results[model_id] = {
                                'prediction': raw_value,  # log scale
                                'value': raw_value,  # log scale
                                'linear_value': linear_value,  # exp(log) = linear
                                'type': 'regression',
                                'unit': 'mL/min/kg' if model_id == 'clearance' else 'μL/min/mg protein'
                            }
                        elif model_id == 'caco2':
                            # Caco-2 permeability (log Papp)
                            # Don't clip - allow full range
                            pass
                            
                            results[model_id] = {
                                'prediction': raw_value,
                                'value': raw_value,
                                'type': 'regression',
                                'unit': 'log Papp (cm/s)'
                            }
                        else:
                            results[model_id] = {
                                'prediction': raw_value,
                                'value': raw_value,
                                'type': 'regression'
                            }
                    
            except Exception as e:
                results[model_id] = {
                    'error': str(e)
                }
        
        return results
    
    def predict_batch(self, smiles_list):
        """
        Run predictions on multiple SMILES strings
        
        Args:
            smiles_list (list): List of SMILES strings
        
        Returns:
            list: List of prediction results for each SMILES
        """
        from datetime import datetime
        
        results = []
        for smiles in smiles_list:
            try:
                # Get predictions for this molecule
                predictions = self.predict(smiles)
                
                # Calculate summary statistics
                toxic_count = 0
                total_prob = 0
                count = 0
                
                for model_id, pred_data in predictions.items():
                    if 'error' not in pred_data and pred_data.get('type') == 'classification':
                        prob = pred_data.get('probability', 0)
                        if isinstance(prob, (int, float)):
                            total_prob += prob
                            count += 1
                            if pred_data.get('prediction', 0) == 1:
                                toxic_count += 1
                
                avg_prob = total_prob / count if count > 0 else 0
                
                # Determine overall assessment
                if avg_prob > 0.7:
                    assessment = "High Risk"
                elif avg_prob > 0.3:
                    assessment = "Medium Risk"
                else:
                    assessment = "Low Risk"
                
                results.append({
                    'smiles': smiles,
                    'timestamp': datetime.now().isoformat(),
                    'endpoints': predictions,
                    'summary': {
                        'overall_assessment': assessment,
                        'recommendation': f"{avg_prob:.1%} confidence",
                        'toxic_endpoints': toxic_count,
                        'average_toxicity_probability': avg_prob
                    }
                })
                
            except Exception as e:
                results.append({
                    'smiles': smiles,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def get_available_models(self):
        """Get list of available models with metadata"""
        available = []
        for model_id, model_data in self.models.items():
            info = model_data['info']
            available.append({
                'id': model_id,
                'name': info['name'],
                'type': info['type'],
                'task': info['task'],
                'loaded': True
            })
        return available
    
    def get_model_info(self, model_id):
        """Get detailed info about a specific model"""
        if model_id in self.models:
            model_data = self.models[model_id]
            info = model_data['info'].copy()
            if 'config' in model_data:
                info['config'] = model_data['config']
            return info
        return None


# For backwards compatibility
SimpleDrugToxPredictor = MultiModelPredictor


if __name__ == "__main__":
    # Test the predictor
    print("Testing Multi-Model Predictor")
    print("=" * 50)
    
    predictor = MultiModelPredictor()
    
    if predictor.is_loaded:
        print("\nAvailable Models:")
        for model in predictor.get_available_models():
            print(f"  - {model['name']} ({model['type']}) [{model['task']}]")
        
        print("\nTest Prediction:")
        test_smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        results = predictor.predict(test_smiles)
        
        for model_id, result in results.items():
            print(f"\n{predictor.model_info[model_id]['name']}:")
            print(f"  {result}")
    else:
        print("❌ No models could be loaded")
