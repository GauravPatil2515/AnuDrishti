#!/usr/bin/env python3
"""
DeNovo Quick Start Script
=========================
Run this script to verify your installation and start the backend.
"""

import sys
import os

def check_dependencies():
    """Check if all required packages are installed."""
    print("🔍 Checking dependencies...")
    
    required = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'torch': 'PyTorch',
        'torch_geometric': 'PyTorch Geometric',
        'rdkit': 'RDKit',
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'Scikit-learn',
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies installed!")
    return True


def check_models():
    """Check if trained models exist."""
    print("\n🧠 Checking trained models...")
    
    models_dir = os.path.join(os.path.dirname(__file__), 'results', 'trained_models')
    
    models = [
        ('attention_gin_model.pth', 'Tox21 (Attention-GIN)'),
        ('bbbp_gin_model.pth', 'BBBP'),
        ('clintox_gin_model.pth', 'ClinTox'),
        ('clearance_gin_model.pth', 'Clearance'),
    ]
    
    found = 0
    for filename, name in models:
        path = os.path.join(models_dir, filename)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  ✅ {name} ({size_mb:.1f} MB)")
            found += 1
        else:
            print(f"  ⚠️  {name} - NOT FOUND")
    
    print(f"\n✅ {found}/{len(models)} models available")
    return found > 0


def test_prediction():
    """Test a simple prediction."""
    print("\n🧪 Testing prediction pipeline...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from models.unified_predictor import UnifiedADMETPredictor
        
        predictor = UnifiedADMETPredictor()
        
        if not predictor.is_loaded:
            print("  ⚠️  Predictor could not load any models")
            return False
        
        # Test with ethanol
        result = predictor.predict('CCO')
        summary = result.get('summary', {})
        assessment = summary.get('overall_assessment', 'N/A')
        
        print(f"  ✅ Ethanol (CCO): {assessment}")
        print("  ✅ Prediction pipeline working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Prediction failed: {e}")
        return False


def start_server():
    """Start the Flask backend server."""
    print("\n🚀 Starting DeNovo Backend Server...")
    print("="*50)
    print("Server will be available at: http://localhost:5000")
    print("API Documentation: http://localhost:5000/api/health")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    os.system('python app.py')


def main():
    print("="*50)
    print("  DeNovo Drug Discovery Platform - Quick Start")
    print("="*50 + "\n")
    
    # Run checks
    deps_ok = check_dependencies()
    models_ok = check_models()
    pred_ok = test_prediction()
    
    print("\n" + "="*50)
    print("  Summary")
    print("="*50)
    print(f"  Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"  Models:       {'✅' if models_ok else '⚠️'}")
    print(f"  Predictions:  {'✅' if pred_ok else '❌'}")
    
    if deps_ok and models_ok and pred_ok:
        print("\n🎉 All checks passed! Ready to start server.")
        response = input("\nStart the server now? (y/n): ")
        if response.lower() == 'y':
            start_server()
    else:
        print("\n⚠️  Some checks failed. Please resolve issues before starting.")
        print("See README.md for installation instructions.")


if __name__ == '__main__':
    main()
