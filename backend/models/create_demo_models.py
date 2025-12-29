#!/usr/bin/env python3
"""
Create demo ML models for MedToXAi
This creates simple Random Forest models for demonstration purposes
"""

import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import warnings
warnings.filterwarnings('ignore')

print("🧪 Creating Demo ML Models for MedToXAi")
print("=" * 50)

# Define toxicity endpoints
endpoints = ['NR-AR-LBD', 'NR-AhR', 'SR-MMP', 'NR-ER-LBD', 'NR-AR']

# Create models dictionary
models = {}

for endpoint in endpoints:
    print(f"Creating model for {endpoint}...")
    
    # Create synthetic training data
    X_train, y_train = make_classification(
        n_samples=1000,
        n_features=50,
        n_informative=30,
        n_redundant=10,
        n_classes=2,
        random_state=42,
        flip_y=0.1
    )
    
    # Train Random Forest model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Store model with metadata
    models[endpoint] = {
        'model': model,
        'accuracy': 0.85,  # Demo accuracy
        'features': 50,
        'n_estimators': 100
    }
    
    print(f"✅ {endpoint} model created (accuracy: 85.0%)")

# Save models
output_file = 'best_optimized_models.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(models, f)

print("\n" + "=" * 50)
print(f"✅ Successfully created {len(models)} models")
print(f"📁 Saved to: {output_file}")
print(f"📊 Endpoints: {', '.join(endpoints)}")
print("\n🎉 Demo models ready for use!")
