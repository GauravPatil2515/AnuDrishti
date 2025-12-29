#!/usr/bin/env python3
"""
Complete Training Script for Molecular Toxicity Models
======================================================
Train high-accuracy XGBoost models for 12 toxicity endpoints

Usage:
    python train_models.py --data data/tox21_data.csv --output trained_models/
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, AllChem
    RDKIT_AVAILABLE = True
    print("✅ RDKit available")
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - install with: pip install rdkit-pypi")
    sys.exit(1)


class FeatureExtractor:
    """Extract molecular features from SMILES"""
    
    def __init__(self, use_morgan=True, morgan_radius=2, morgan_bits=2048):
        self.use_morgan = use_morgan
        self.morgan_radius = morgan_radius
        self.morgan_bits = morgan_bits
        
        # RDKit descriptor names
        self.descriptor_names = [name for name, _ in Descriptors.descList]
        print(f"RDKit descriptors: {len(self.descriptor_names)}")
    
    def extract_rdkit_descriptors(self, mol):
        """Extract RDKit molecular descriptors"""
        features = {}
        
        # Calculate all descriptors
        for name in self.descriptor_names:
            try:
                calc = getattr(Descriptors, name)
                features[name] = calc(mol)
            except:
                features[name] = np.nan
        
        # Additional descriptors
        try:
            features['NumSpiroAtoms'] = rdMolDescriptors.CalcNumSpiroAtoms(mol)
            features['NumBridgeheadAtoms'] = rdMolDescriptors.CalcNumBridgeheadAtoms(mol)
            features['NumAmideBonds'] = rdMolDescriptors.CalcNumAmideBonds(mol)
        except:
            pass
        
        return features
    
    def extract_morgan_fingerprint(self, mol):
        """Extract Morgan fingerprint"""
        fp = AllChem.GetMorganFingerprintAsBitVect(
            mol, 
            radius=self.morgan_radius, 
            nBits=self.morgan_bits
        )
        return {f'morgan_{i}': int(fp[i]) for i in range(self.morgan_bits)}
    
    def extract_features(self, smiles):
        """Extract all features for a SMILES string"""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            features = {}
            
            # RDKit descriptors
            rdkit_features = self.extract_rdkit_descriptors(mol)
            features.update(rdkit_features)
            
            # Morgan fingerprint
            if self.use_morgan:
                morgan_features = self.extract_morgan_fingerprint(mol)
                features.update(morgan_features)
            
            return features
            
        except Exception as e:
            print(f"Error extracting features for {smiles}: {e}")
            return None
    
    def extract_batch(self, smiles_list):
        """Extract features for multiple SMILES"""
        features_list = []
        
        for i, smiles in enumerate(smiles_list):
            if (i + 1) % 100 == 0:
                print(f"Extracted features for {i+1}/{len(smiles_list)} molecules")
            
            features = self.extract_features(smiles)
            if features:
                features_list.append(features)
            else:
                # Add empty row for failed extractions
                features_list.append({})
        
        df = pd.DataFrame(features_list)
        print(f"\nTotal features extracted: {df.shape[1]}")
        
        return df


class ModelTrainer:
    """Train XGBoost models for toxicity prediction"""
    
    def __init__(self, endpoint_name):
        self.endpoint_name = endpoint_name
        self.model = None
        self.scaler = None
    
    def train(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model"""
        
        # Handle class imbalance
        scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
        
        print(f"\nClass distribution:")
        print(f"  Train - Negative: {(y_train == 0).sum()}, Positive: {(y_train == 1).sum()}")
        print(f"  Val - Negative: {(y_val == 0).sum()}, Positive: {(y_val == 1).sum()}")
        print(f"  Scale pos weight: {scale_pos_weight:.2f}")
        
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
            'tree_method': 'hist',
            'n_jobs': -1
        }
        
        # Create model
        self.model = xgb.XGBClassifier(**params)
        
        # Train with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        # Evaluate
        y_val_pred = self.model.predict_proba(X_val)[:, 1]
        val_roc_auc = roc_auc_score(y_val, y_val_pred)
        
        print(f"\n{self.endpoint_name} - Validation ROC-AUC: {val_roc_auc:.4f}")
        
        return val_roc_auc
    
    def evaluate(self, X_test, y_test):
        """Evaluate model on test set"""
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # ROC-AUC
        test_roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"\n{self.endpoint_name} - Test ROC-AUC: {test_roc_auc:.4f}")
        print(f"Precision: {report['1']['precision']:.4f}")
        print(f"Recall: {report['1']['recall']:.4f}")
        print(f"F1-Score: {report['1']['f1-score']:.4f}")
        
        return {
            'test_roc_auc': test_roc_auc,
            'precision': report['1']['precision'],
            'recall': report['1']['recall'],
            'f1_score': report['1']['f1-score'],
            'confusion_matrix': cm.tolist()
        }


class TrainingPipeline:
    """Complete training pipeline"""
    
    def __init__(self, data_path, output_dir, endpoints=None):
        self.data_path = data_path
        self.output_dir = output_dir
        
        # Default endpoints
        if endpoints is None:
            self.endpoints = [
                'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-ER-LBD', 'SR-MMP',
                'NR-ER', 'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 
                'SR-HSE', 'SR-p53', 'NR-Aromatase'
            ]
        else:
            self.endpoints = endpoints
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)
    
    def load_data(self):
        """Load training data"""
        print(f"\nLoading data from: {self.data_path}")
        
        # Load CSV
        df = pd.read_csv(self.data_path)
        
        print(f"Loaded {len(df)} compounds")
        print(f"Columns: {list(df.columns)}")
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess and validate data"""
        print("\nPreprocessing data...")
        
        # Validate SMILES
        valid_indices = []
        for i, smiles in enumerate(df['smiles']):
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                valid_indices.append(i)
        
        df = df.iloc[valid_indices].reset_index(drop=True)
        print(f"Valid SMILES: {len(df)}")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['smiles']).reset_index(drop=True)
        print(f"After removing duplicates: {len(df)}")
        
        return df
    
    def extract_features(self, df):
        """Extract molecular features"""
        print("\nExtracting features...")
        
        feature_extractor = FeatureExtractor(use_morgan=True)
        features = feature_extractor.extract_batch(df['smiles'].tolist())
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        # Fill any remaining NaNs with 0
        features = features.fillna(0)
        
        print(f"Feature shape: {features.shape}")
        
        return features
    
    def train_endpoint(self, X, y, endpoint_name):
        """Train model for a single endpoint"""
        print(f"\n{'='*70}")
        print(f"Training: {endpoint_name}")
        print(f"{'='*70}")
        
        # Check for sufficient positive samples
        if y.sum() < 50:
            print(f"⚠️ Skipping {endpoint_name} - too few positive samples ({y.sum()})")
            return None
        
        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )
        
        print(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # Train model
        trainer = ModelTrainer(endpoint_name)
        val_roc_auc = trainer.train(X_train, y_train, X_val, y_val)
        
        # Evaluate on test set
        test_metrics = trainer.evaluate(X_test, y_test)
        
        # Package model info
        model_info = {
            'model': trainer.model,
            'endpoint': endpoint_name,
            'roc_auc': test_metrics['test_roc_auc'],
            'val_roc_auc': val_roc_auc,
            'precision': test_metrics['precision'],
            'recall': test_metrics['recall'],
            'f1_score': test_metrics['f1_score'],
            'confusion_matrix': test_metrics['confusion_matrix'],
            'feature_count': X.shape[1],
            'train_size': len(X_train),
            'test_size': len(X_test),
            'trained_at': datetime.now().isoformat()
        }
        
        return model_info
    
    def train_all(self, df, features):
        """Train models for all endpoints"""
        print("\n" + "="*70)
        print("TRAINING ALL ENDPOINTS")
        print("="*70)
        
        all_models = {}
        results = []
        
        for endpoint in self.endpoints:
            if endpoint not in df.columns:
                print(f"\n⚠️ Skipping {endpoint} - not in dataset")
                continue
            
            # Get labels
            y = df[endpoint].values
            
            # Remove NaN labels
            valid_mask = ~pd.isna(y)
            X_valid = features[valid_mask]
            y_valid = y[valid_mask].astype(int)
            
            if len(y_valid) < 100:
                print(f"\n⚠️ Skipping {endpoint} - too few samples ({len(y_valid)})")
                continue
            
            # Train model
            model_info = self.train_endpoint(X_valid, y_valid, endpoint)
            
            if model_info:
                all_models[endpoint] = model_info
                
                results.append({
                    'endpoint': endpoint,
                    'test_roc_auc': model_info['roc_auc'],
                    'val_roc_auc': model_info['val_roc_auc'],
                    'precision': model_info['precision'],
                    'recall': model_info['recall'],
                    'f1_score': model_info['f1_score'],
                    'train_size': model_info['train_size']
                })
        
        # Save models
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
            'model_count': len(models),
            'feature_count': models[list(models.keys())[0]]['feature_count'],
            'trained_at': datetime.now().isoformat(),
            'training_data': self.data_path
        }
        
        metadata_file = os.path.join(self.output_dir, 'model_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata saved to: {metadata_file}")
        
        # Save results CSV
        results_data = []
        for endpoint, info in models.items():
            results_data.append({
                'endpoint': endpoint,
                'test_roc_auc': info['roc_auc'],
                'val_roc_auc': info['val_roc_auc'],
                'precision': info['precision'],
                'recall': info['recall'],
                'f1_score': info['f1_score'],
                'train_size': info['train_size'],
                'test_size': info['test_size']
            })
        
        results_df = pd.DataFrame(results_data)
        results_file = os.path.join(self.output_dir, 'training_results.csv')
        results_df.to_csv(results_file, index=False)
        
        print(f"✅ Results saved to: {results_file}")
    
    def print_summary(self, results):
        """Print training summary"""
        print("\n" + "="*70)
        print("TRAINING SUMMARY")
        print("="*70)
        
        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))
        
        print(f"\n{'='*70}")
        print(f"Average Test ROC-AUC: {df_results['test_roc_auc'].mean():.4f}")
        print(f"Average Val ROC-AUC: {df_results['val_roc_auc'].mean():.4f}")
        print(f"Average Precision: {df_results['precision'].mean():.4f}")
        print(f"Average Recall: {df_results['recall'].mean():.4f}")
        print(f"Average F1-Score: {df_results['f1_score'].mean():.4f}")
        print(f"{'='*70}")
    
    def run(self):
        """Run complete training pipeline"""
        print("\n" + "="*70)
        print("MOLECULAR TOXICITY MODEL TRAINING PIPELINE")
        print("="*70)
        
        # Load data
        df = self.load_data()
        
        # Preprocess
        df = self.preprocess_data(df)
        
        # Extract features
        features = self.extract_features(df)
        
        # Train all models
        models = self.train_all(df, features)
        
        print("\n✅ Training complete!")
        
        return models


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Train molecular toxicity prediction models')
    parser.add_argument('--data', type=str, required=True, help='Path to training data CSV')
    parser.add_argument('--output', type=str, default='trained_models', help='Output directory')
    parser.add_argument('--endpoints', type=str, nargs='+', help='Specific endpoints to train')
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = TrainingPipeline(
        data_path=args.data,
        output_dir=args.output,
        endpoints=args.endpoints
    )
    
    # Run training
    models = pipeline.run()
    
    print(f"\n✅ Trained {len(models)} models successfully!")


if __name__ == "__main__":
    main()
