# 🧠 High-Efficiency Model Training Guide

## Training Molecular Toxicity Models with Large Datasets

**Created**: December 9, 2025  
**Purpose**: Train production-grade toxicity prediction models  
**Target**: 12 toxicity endpoints with 90%+ accuracy

---

## 📋 Table of Contents

1. [Data Sources](#data-sources)
2. [Training Pipeline Architecture](#training-pipeline-architecture)
3. [Feature Engineering](#feature-engineering)
4. [Model Selection & Optimization](#model-selection--optimization)
5. [Training Implementation](#training-implementation)
6. [Evaluation & Validation](#evaluation--validation)
7. [Production Deployment](#production-deployment)

---

## 🗄️ DATA SOURCES

### Primary Datasets

#### 1. **Tox21 Dataset** (Recommended)

- **Source**: <https://tripod.nih.gov/tox21/challenge/>
- **Size**: ~12,000 compounds
- **Endpoints**: 12 toxicity assays
- **Quality**: High-quality, experimentally validated
- **Format**: SMILES + binary labels

**Download**:

```bash
# Download Tox21 data
wget https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_data_all.sdf
wget https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_challenge_test.sdf
```

#### 2. **PubChem BioAssay**

- **Source**: <https://pubchem.ncbi.nlm.nih.gov/>
- **Size**: Millions of compounds
- **Endpoints**: Various biological assays
- **Quality**: Variable, needs filtering

#### 3. **ChEMBL Database**

- **Source**: <https://www.ebi.ac.uk/chembl/>
- **Size**: 2M+ compounds
- **Endpoints**: Drug-like molecules with bioactivity
- **Quality**: Curated pharmaceutical data

#### 4. **ToxCast**

- **Source**: <https://www.epa.gov/chemical-research/toxicity-forecaster-toxcasttm-data>
- **Size**: 9,000+ compounds
- **Endpoints**: 700+ high-throughput assays
- **Quality**: EPA-validated

### Recommended Combination

```python
# Optimal dataset mix for training
DATASETS = {
    'tox21': {
        'size': 12000,
        'weight': 0.5,  # Primary dataset
        'endpoints': 12
    },
    'toxcast': {
        'size': 9000,
        'weight': 0.3,  # Secondary
        'endpoints': 700
    },
    'chembl': {
        'size': 50000,  # Filtered subset
        'weight': 0.2,  # Augmentation
        'endpoints': 'selected'
    }
}

# Total training data: ~71,000 compounds
```

---

## 🏗️ TRAINING PIPELINE ARCHITECTURE

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                          │
│  Tox21 + ToxCast + ChEMBL + PubChem                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  DATA PREPROCESSING                         │
│  • SMILES validation                                        │
│  • Duplicate removal                                        │
│  • Outlier detection                                        │
│  • Train/Val/Test split (70/15/15)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 FEATURE ENGINEERING                         │
│  • RDKit descriptors (200+)                                 │
│  • Morgan fingerprints (2048-bit)                           │
│  • ChemBERT embeddings (768-dim)                           │
│  • Graph neural network features                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   MODEL TRAINING                            │
│  • Random Forest (baseline)                                 │
│  • XGBoost (primary)                                        │
│  • LightGBM (fast)                                          │
│  • Deep Neural Network (advanced)                           │
│  • Graph Neural Network (state-of-art)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              HYPERPARAMETER OPTIMIZATION                    │
│  • Optuna/Ray Tune                                          │
│  • 5-fold cross-validation                                  │
│  • Early stopping                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION                               │
│  • ROC-AUC, Precision, Recall                              │
│  • Confusion matrix                                         │
│  • Feature importance                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                PRODUCTION DEPLOYMENT                        │
│  • Model serialization                                      │
│  • Version control                                          │
│  • A/B testing                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 FEATURE ENGINEERING

### 1. RDKit Molecular Descriptors (200+ features)

```python
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import numpy as np

class RDKitFeatureExtractor:
    """Extract comprehensive RDKit molecular descriptors"""
    
    def __init__(self):
        # List of all RDKit descriptors
        self.descriptor_names = [name for name, _ in Descriptors.descList]
        print(f"Total RDKit descriptors: {len(self.descriptor_names)}")
    
    def extract_features(self, smiles):
        """Extract all RDKit descriptors for a molecule"""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            features = {}
            
            # Calculate all descriptors
            for name in self.descriptor_names:
                try:
                    calc = getattr(Descriptors, name)
                    features[name] = calc(mol)
                except:
                    features[name] = np.nan
            
            # Additional descriptors
            features['NumSpiroAtoms'] = rdMolDescriptors.CalcNumSpiroAtoms(mol)
            features['NumBridgeheadAtoms'] = rdMolDescriptors.CalcNumBridgeheadAtoms(mol)
            features['NumAmideBonds'] = rdMolDescriptors.CalcNumAmideBonds(mol)
            
            return features
            
        except Exception as e:
            print(f"Error extracting features for {smiles}: {e}")
            return None
    
    def extract_batch(self, smiles_list):
        """Extract features for multiple molecules"""
        features_list = []
        for smiles in smiles_list:
            features = self.extract_features(smiles)
            if features:
                features_list.append(features)
        
        # Convert to DataFrame
        import pandas as pd
        return pd.DataFrame(features_list)
```

### 2. Morgan Fingerprints (2048-bit)

```python
from rdkit.Chem import AllChem

class MorganFingerprintExtractor:
    """Extract Morgan (circular) fingerprints"""
    
    def __init__(self, radius=2, n_bits=2048):
        self.radius = radius
        self.n_bits = n_bits
    
    def extract_fingerprint(self, smiles):
        """Extract Morgan fingerprint as bit vector"""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            # Generate Morgan fingerprint
            fp = AllChem.GetMorganFingerprintAsBitVect(
                mol, 
                radius=self.radius, 
                nBits=self.n_bits
            )
            
            # Convert to numpy array
            return np.array(fp)
            
        except Exception as e:
            print(f"Error generating fingerprint: {e}")
            return None
    
    def extract_batch(self, smiles_list):
        """Extract fingerprints for multiple molecules"""
        fingerprints = []
        for smiles in smiles_list:
            fp = self.extract_fingerprint(smiles)
            if fp is not None:
                fingerprints.append(fp)
        
        return np.array(fingerprints)
```

### 3. ChemBERT Embeddings (768-dim)

```python
from transformers import AutoTokenizer, AutoModel
import torch

class ChemBERTEmbedder:
    """Extract ChemBERT molecular embeddings"""
    
    def __init__(self, model_name='seyonec/ChemBERTa-zinc-base-v1'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
    
    def get_embedding(self, smiles):
        """Get ChemBERT embedding for a molecule"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                smiles, 
                return_tensors='pt', 
                padding=True, 
                truncation=True,
                max_length=512
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Use [CLS] token embedding
            embedding = outputs.last_hidden_state[:, 0, :].numpy()
            
            return embedding.flatten()
            
        except Exception as e:
            print(f"Error getting ChemBERT embedding: {e}")
            return None
    
    def get_batch_embeddings(self, smiles_list, batch_size=32):
        """Get embeddings for multiple molecules"""
        embeddings = []
        
        for i in range(0, len(smiles_list), batch_size):
            batch = smiles_list[i:i+batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Extract [CLS] embeddings
            batch_embeddings = outputs.last_hidden_state[:, 0, :].numpy()
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
```

### 4. Combined Feature Set

```python
class CombinedFeatureExtractor:
    """Combine multiple feature extraction methods"""
    
    def __init__(self, use_rdkit=True, use_morgan=True, use_chembert=False):
        self.use_rdkit = use_rdkit
        self.use_morgan = use_morgan
        self.use_chembert = use_chembert
        
        if use_rdkit:
            self.rdkit_extractor = RDKitFeatureExtractor()
        if use_morgan:
            self.morgan_extractor = MorganFingerprintExtractor()
        if use_chembert:
            self.chembert_embedder = ChemBERTEmbedder()
    
    def extract_features(self, smiles_list):
        """Extract all features for molecules"""
        features_list = []
        
        # RDKit descriptors
        if self.use_rdkit:
            rdkit_features = self.rdkit_extractor.extract_batch(smiles_list)
            features_list.append(rdkit_features)
        
        # Morgan fingerprints
        if self.use_morgan:
            morgan_features = self.morgan_extractor.extract_batch(smiles_list)
            features_list.append(pd.DataFrame(morgan_features))
        
        # ChemBERT embeddings
        if self.use_chembert:
            chembert_features = self.chembert_embedder.get_batch_embeddings(smiles_list)
            features_list.append(pd.DataFrame(chembert_features))
        
        # Combine all features
        combined = pd.concat(features_list, axis=1)
        
        print(f"Total features: {combined.shape[1]}")
        return combined
```

---

## 🤖 MODEL SELECTION & OPTIMIZATION

### Model Comparison

| Model | Pros | Cons | Best For |
|-------|------|------|----------|
| **Random Forest** | Fast, interpretable, robust | Lower accuracy | Baseline |
| **XGBoost** | High accuracy, handles imbalance | Slower training | Production |
| **LightGBM** | Very fast, memory efficient | Less accurate than XGBoost | Large datasets |
| **Deep Neural Network** | Can learn complex patterns | Needs more data, black box | Advanced |
| **Graph Neural Network** | State-of-art for molecules | Complex, slow | Research |

### Recommended: XGBoost

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

class XGBoostToxicityModel:
    """XGBoost model for toxicity prediction"""
    
    def __init__(self, endpoint_name):
        self.endpoint_name = endpoint_name
        self.model = None
        self.best_params = None
    
    def train(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model with optimal parameters"""
        
        # Handle class imbalance
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        
        # XGBoost parameters
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 500,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': scale_pos_weight,
            'random_state': 42,
            'tree_method': 'hist',  # Fast histogram-based
            'device': 'cuda'  # Use GPU if available
        }
        
        # Create model
        self.model = xgb.XGBClassifier(**params)
        
        # Train with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=True
        )
        
        # Evaluate
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]
        roc_auc = roc_auc_score(y_val, y_pred_proba)
        
        print(f"\n{self.endpoint_name} - Validation ROC-AUC: {roc_auc:.4f}")
        
        return roc_auc
    
    def predict(self, X):
        """Predict toxicity probability"""
        return self.model.predict_proba(X)[:, 1]
    
    def get_feature_importance(self):
        """Get feature importance scores"""
        return self.model.feature_importances_
```

### Hyperparameter Optimization with Optuna

```python
import optuna

class OptunaOptimizer:
    """Optimize XGBoost hyperparameters with Optuna"""
    
    def __init__(self, X_train, y_train, X_val, y_val):
        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
    
    def objective(self, trial):
        """Optuna objective function"""
        
        # Suggest hyperparameters
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0, 5),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
        }
        
        # Train model
        model = xgb.XGBClassifier(
            **params,
            objective='binary:logistic',
            eval_metric='auc',
            random_state=42,
            tree_method='hist'
        )
        
        model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_val, self.y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        # Evaluate
        y_pred_proba = model.predict_proba(self.X_val)[:, 1]
        roc_auc = roc_auc_score(self.y_val, y_pred_proba)
        
        return roc_auc
    
    def optimize(self, n_trials=100):
        """Run optimization"""
        study = optuna.create_study(direction='maximize')
        study.optimize(self.objective, n_trials=n_trials)
        
        print(f"\nBest ROC-AUC: {study.best_value:.4f}")
        print(f"Best params: {study.best_params}")
        
        return study.best_params
```

---

## 🚀 TRAINING IMPLEMENTATION

### Complete Training Pipeline

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import json
from datetime import datetime

class ToxicityModelTrainer:
    """Complete training pipeline for toxicity prediction models"""
    
    def __init__(self, data_path, output_dir='trained_models'):
        self.data_path = data_path
        self.output_dir = output_dir
        self.endpoints = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-ER-LBD', 'SR-MMP',
            'NR-ER', 'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 
            'SR-HSE', 'SR-p53', 'NR-Aromatase'
        ]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self):
        """Load and preprocess data"""
        print("Loading data...")
        
        # Load Tox21 data
        df = pd.read_csv(self.data_path)
        
        print(f"Loaded {len(df)} compounds")
        print(f"Endpoints: {self.endpoints}")
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess and validate data"""
        print("\nPreprocessing data...")
        
        # Validate SMILES
        from rdkit import Chem
        valid_smiles = []
        for smiles in df['smiles']:
            mol = Chem.MolFromSmiles(smiles)
            valid_smiles.append(mol is not None)
        
        df = df[valid_smiles].reset_index(drop=True)
        print(f"Valid SMILES: {len(df)}")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['smiles']).reset_index(drop=True)
        print(f"After removing duplicates: {len(df)}")
        
        return df
    
    def extract_features(self, df):
        """Extract molecular features"""
        print("\nExtracting features...")
        
        # Use combined feature extractor
        feature_extractor = CombinedFeatureExtractor(
            use_rdkit=True,
            use_morgan=True,
            use_chembert=False  # Set to True for better accuracy (slower)
        )
        
        features = feature_extractor.extract_features(df['smiles'].tolist())
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        print(f"Feature shape: {features.shape}")
        
        return features
    
    def train_endpoint_model(self, X, y, endpoint_name, optimize=True):
        """Train model for a single endpoint"""
        print(f"\n{'='*60}")
        print(f"Training model for {endpoint_name}")
        print(f"{'='*60}")
        
        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        print(f"Positive ratio - Train: {y_train.mean():.3f}, Val: {y_val.mean():.3f}")
        
        # Optimize hyperparameters
        if optimize:
            print("\nOptimizing hyperparameters...")
            optimizer = OptunaOptimizer(X_train, y_train, X_val, y_val)
            best_params = optimizer.optimize(n_trials=50)
        else:
            best_params = {}
        
        # Train final model
        print("\nTraining final model...")
        model = XGBoostToxicityModel(endpoint_name)
        val_roc_auc = model.train(X_train, y_train, X_val, y_val)
        
        # Evaluate on test set
        y_test_pred = model.predict(X_test)
        test_roc_auc = roc_auc_score(y_test, y_test_pred)
        
        print(f"\nTest ROC-AUC: {test_roc_auc:.4f}")
        
        # Save model
        model_info = {
            'model': model.model,
            'endpoint': endpoint_name,
            'roc_auc': test_roc_auc,
            'val_roc_auc': val_roc_auc,
            'best_params': best_params,
            'feature_count': X.shape[1],
            'train_size': len(X_train),
            'test_size': len(X_test),
            'trained_at': datetime.now().isoformat()
        }
        
        return model_info
    
    def train_all_endpoints(self, df, features, optimize=True):
        """Train models for all endpoints"""
        print("\n" + "="*60)
        print("TRAINING ALL ENDPOINTS")
        print("="*60)
        
        all_models = {}
        results = []
        
        for endpoint in self.endpoints:
            if endpoint not in df.columns:
                print(f"\n⚠️ Skipping {endpoint} - not in dataset")
                continue
            
            # Get labels
            y = df[endpoint].values
            
            # Skip if too few positive samples
            if y.sum() < 50:
                print(f"\n⚠️ Skipping {endpoint} - too few positive samples ({y.sum()})")
                continue
            
            # Train model
            model_info = self.train_endpoint_model(features, y, endpoint, optimize=optimize)
            all_models[endpoint] = model_info
            
            # Record results
            results.append({
                'endpoint': endpoint,
                'test_roc_auc': model_info['roc_auc'],
                'val_roc_auc': model_info['val_roc_auc'],
                'train_size': model_info['train_size']
            })
        
        # Save all models
        self.save_models(all_models)
        
        # Print summary
        self.print_summary(results)
        
        return all_models
    
    def save_models(self, models):
        """Save trained models"""
        output_file = os.path.join(self.output_dir, 'best_optimized_models.pkl')
        
        with open(output_file, 'wb') as f:
            pickle.dump(models, f)
        
        print(f"\n✅ Models saved to: {output_file}")
        
        # Save metadata
        metadata = {
            'endpoints': list(models.keys()),
            'feature_count': models[list(models.keys())[0]]['feature_count'],
            'trained_at': datetime.now().isoformat(),
            'model_count': len(models)
        }
        
        metadata_file = os.path.join(self.output_dir, 'model_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata saved to: {metadata_file}")
    
    def print_summary(self, results):
        """Print training summary"""
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        
        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))
        
        print(f"\nAverage Test ROC-AUC: {df_results['test_roc_auc'].mean():.4f}")
        print(f"Average Val ROC-AUC: {df_results['val_roc_auc'].mean():.4f}")
        
    def run(self, optimize=True):
        """Run complete training pipeline"""
        # Load data
        df = self.load_data()
        
        # Preprocess
        df = self.preprocess_data(df)
        
        # Extract features
        features = self.extract_features(df)
        
        # Train all models
        models = self.train_all_endpoints(df, features, optimize=optimize)
        
        return models


# Usage
if __name__ == "__main__":
    trainer = ToxicityModelTrainer(
        data_path='data/tox21_data.csv',
        output_dir='trained_models'
    )
    
    models = trainer.run(optimize=True)
```

---

## 📊 EVALUATION & VALIDATION

### Comprehensive Evaluation

```python
from sklearn.metrics import (
    roc_auc_score, roc_curve, 
    precision_recall_curve, confusion_matrix,
    classification_report
)
import matplotlib.pyplot as plt

class ModelEvaluator:
    """Comprehensive model evaluation"""
    
    def __init__(self, model, X_test, y_test, endpoint_name):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.endpoint_name = endpoint_name
        self.y_pred_proba = model.predict(X_test)
        self.y_pred = (self.y_pred_proba > 0.5).astype(int)
    
    def evaluate_all(self):
        """Run all evaluations"""
        print(f"\nEvaluation for {self.endpoint_name}")
        print("="*60)
        
        # ROC-AUC
        roc_auc = roc_auc_score(self.y_test, self.y_pred_proba)
        print(f"ROC-AUC: {roc_auc:.4f}")
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(self.y_test, self.y_pred))
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, self.y_pred)
        print("\nConfusion Matrix:")
        print(cm)
        
        # Plot ROC curve
        self.plot_roc_curve()
        
        # Plot precision-recall curve
        self.plot_precision_recall_curve()
        
        return {
            'roc_auc': roc_auc,
            'confusion_matrix': cm
        }
    
    def plot_roc_curve(self):
        """Plot ROC curve"""
        fpr, tpr, _ = roc_curve(self.y_test, self.y_pred_proba)
        roc_auc = roc_auc_score(self.y_test, self.y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.4f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {self.endpoint_name}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'plots/roc_{self.endpoint_name}.png')
        plt.close()
    
    def plot_precision_recall_curve(self):
        """Plot precision-recall curve"""
        precision, recall, _ = precision_recall_curve(self.y_test, self.y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(f'Precision-Recall Curve - {self.endpoint_name}')
        plt.grid(True)
        plt.savefig(f'plots/pr_{self.endpoint_name}.png')
        plt.close()
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Model Deployment Checklist

```python
class ProductionModelDeployer:
    """Deploy trained models to production"""
    
    def __init__(self, models_path, output_path):
        self.models_path = models_path
        self.output_path = output_path
    
    def validate_models(self):
        """Validate models before deployment"""
        print("Validating models...")
        
        with open(self.models_path, 'rb') as f:
            models = pickle.load(f)
        
        checks = []
        
        for endpoint, model_info in models.items():
            # Check ROC-AUC threshold
            roc_auc = model_info.get('roc_auc', 0)
            passed = roc_auc >= 0.70  # Minimum threshold
            
            checks.append({
                'endpoint': endpoint,
                'roc_auc': roc_auc,
                'passed': passed
            })
            
            if not passed:
                print(f"⚠️ {endpoint} failed validation (ROC-AUC: {roc_auc:.4f})")
        
        all_passed = all(c['passed'] for c in checks)
        
        if all_passed:
            print("✅ All models passed validation")
        else:
            print("❌ Some models failed validation")
        
        return all_passed
    
    def deploy(self):
        """Deploy models to production"""
        if not self.validate_models():
            print("❌ Deployment aborted - validation failed")
            return False
        
        # Copy to production path
        import shutil
        shutil.copy(self.models_path, self.output_path)
        
        print(f"✅ Models deployed to: {self.output_path}")
        return True
```

---

## 📝 QUICK START EXAMPLE

```python
# 1. Download Tox21 data
# wget https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_data_all.sdf

# 2. Convert to CSV (if needed)
# Use RDKit to convert SDF to CSV with SMILES

# 3. Train models
trainer = ToxicityModelTrainer(
    data_path='data/tox21_data.csv',
    output_dir='trained_models'
)

models = trainer.run(optimize=True)

# 4. Evaluate
# Models are automatically evaluated during training

# 5. Deploy
deployer = ProductionModelDeployer(
    models_path='trained_models/best_optimized_models.pkl',
    output_path='backend/models/best_optimized_models.pkl'
)

deployer.deploy()
```

---

## 🎯 EXPECTED RESULTS

### Target Metrics

| Endpoint | Target ROC-AUC | Expected Training Time |
|----------|----------------|------------------------|
| NR-AR | 0.85+ | 10-15 min |
| NR-AR-LBD | 0.90+ | 10-15 min |
| NR-AhR | 0.85+ | 10-15 min |
| NR-ER-LBD | 0.88+ | 10-15 min |
| SR-MMP | 0.82+ | 10-15 min |
| NR-ER | 0.87+ | 10-15 min |
| NR-PPAR-gamma | 0.83+ | 10-15 min |
| SR-ARE | 0.80+ | 10-15 min |
| SR-ATAD5 | 0.82+ | 10-15 min |
| SR-HSE | 0.81+ | 10-15 min |
| SR-p53 | 0.84+ | 10-15 min |
| NR-Aromatase | 0.85+ | 10-15 min |

**Total Training Time**: ~2-3 hours (with optimization)

---

## 💡 TIPS FOR BEST RESULTS

1. **Use GPU**: Enable CUDA for XGBoost (`tree_method='gpu_hist'`)
2. **More Data**: Combine multiple datasets for better generalization
3. **Feature Selection**: Use feature importance to remove noise
4. **Ensemble**: Combine multiple models for better accuracy
5. **Cross-Validation**: Use 5-fold CV for robust evaluation
6. **Class Balancing**: Use SMOTE or class weights for imbalanced data
7. **Regular Retraining**: Retrain models quarterly with new data

---

**Created**: December 9, 2025  
**Version**: 1.0  
**Status**: Production-Ready
