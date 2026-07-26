#!/usr/bin/env python3
"""
Deep Model Validation Script
============================
Tests all prediction models with known toxic and non-toxic molecules.
Validates predictions against real-world toxicity data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import json
from datetime import datetime

# Known molecules with established toxicity profiles
# Source: PubChem, EPA ToxCast, literature
TEST_MOLECULES = {
    # HIGHLY TOXIC - Should predict HIGH risk
    'toxic': [
        {
            'name': 'Aflatoxin B1',
            'smiles': 'COC1=C2C3=C(C(=O)OC3)C(=O)OC2=CC=C1',
            'known_effects': 'Potent carcinogen, hepatotoxic',
            'expected': 'High Risk'
        },
        {
            'name': 'Thalidomide',
            'smiles': 'O=C1CCC(N2C(=O)c3ccccc3C2=O)C(=O)N1',
            'known_effects': 'Teratogenic (birth defects)',
            'expected': 'High Risk'
        },
        {
            'name': 'Nitrobenzene',
            'smiles': 'c1ccc([N+](=O)[O-])cc1',
            'known_effects': 'Toxic, methemoglobinemia',
            'expected': 'High Risk'
        },
        {
            'name': 'Benzo[a]pyrene',
            'smiles': 'c1ccc2c(c1)cc3ccc4cccc5ccc2c3c45',
            'known_effects': 'Carcinogenic PAH',
            'expected': 'High Risk'
        },
        {
            'name': 'Arsenic trioxide',
            'smiles': 'O=[As]O[As]=O',
            'known_effects': 'Highly toxic, carcinogenic',
            'expected': 'High Risk'
        },
    ],
    
    # NON-TOXIC / LOW TOXICITY - Should predict LOW risk
    'safe': [
        {
            'name': 'Ethanol',
            'smiles': 'CCO',
            'known_effects': 'Low acute toxicity at normal doses',
            'expected': 'Low Risk'
        },
        {
            'name': 'Caffeine',
            'smiles': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
            'known_effects': 'Safe at normal doses, mild stimulant',
            'expected': 'Low Risk'
        },
        {
            'name': 'Glucose',
            'smiles': 'OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O',
            'known_effects': 'Essential nutrient, non-toxic',
            'expected': 'Low Risk'
        },
        {
            'name': 'Vitamin C (Ascorbic Acid)',
            'smiles': 'OC[C@H](O)[C@H]1OC(=O)C(O)=C1O',
            'known_effects': 'Essential vitamin, very low toxicity',
            'expected': 'Low Risk'
        },
        {
            'name': 'Glycerol',
            'smiles': 'OCC(O)CO',
            'known_effects': 'Non-toxic, used in food/cosmetics',
            'expected': 'Low Risk'
        },
    ],
    
    # MODERATE RISK - Edge cases
    'moderate': [
        {
            'name': 'Acetaminophen (Paracetamol)',
            'smiles': 'CC(=O)Nc1ccc(O)cc1',
            'known_effects': 'Safe at therapeutic doses, hepatotoxic in overdose',
            'expected': 'Moderate Risk'
        },
        {
            'name': 'Ibuprofen',
            'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(O)=O',
            'known_effects': 'NSAID, GI side effects possible',
            'expected': 'Moderate Risk'
        },
    ]
}

def load_predictor():
    """Load the UnifiedADMETPredictor"""
    try:
        from models.unified_predictor import UnifiedADMETPredictor
        predictor = UnifiedADMETPredictor()
        if not predictor.is_loaded:
            print("❌ Failed to load predictor models")
            return None
        print(f"✅ Loaded UnifiedADMETPredictor with {len(predictor.models)} model types")
        print(f"   Models: {list(predictor.models.keys())}")
        return predictor
    except Exception as e:
        print(f"❌ Error loading predictor: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_validation(predictor):
    """Run validation on test molecules"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'UnifiedADMETPredictor',
        'validation_results': [],
        'summary': {}
    }
    
    total_correct = 0
    total_tests = 0
    
    for category, molecules in TEST_MOLECULES.items():
        print(f"\n{'='*60}")
        print(f"Category: {category.upper()}")
        print('='*60)
        
        category_correct = 0
        
        for mol in molecules:
            total_tests += 1
            print(f"\n🧪 Testing: {mol['name']}")
            print(f"   SMILES: {mol['smiles']}")
            print(f"   Known Effects: {mol['known_effects']}")
            print(f"   Expected: {mol['expected']}")
            
            try:
                prediction = predictor.predict_single(mol['smiles'])
                
                if 'error' in prediction:
                    print(f"   ❌ Prediction Error: {prediction['error']}")
                    continue
                
                # Extract summary
                summary = prediction.get('summary', {})
                avg_prob = summary.get('average_toxicity_probability', 0.5)
                assessment = summary.get('overall_assessment', 'Unknown')
                
                print(f"   📊 Predicted: {assessment}")
                print(f"   📈 Avg Toxicity Probability: {avg_prob:.3f}")
                
                # Check if prediction matches expected category
                is_correct = False
                if mol['expected'] == 'High Risk' and avg_prob > 0.5:
                    is_correct = True
                elif mol['expected'] == 'Low Risk' and avg_prob < 0.4:
                    is_correct = True
                elif mol['expected'] == 'Moderate Risk' and 0.3 <= avg_prob <= 0.6:
                    is_correct = True
                
                status = "✅ CORRECT" if is_correct else "⚠️ MISMATCH"
                print(f"   {status}")
                
                if is_correct:
                    total_correct += 1
                    category_correct += 1
                
                # Store endpoint details
                endpoint_details = {}
                for ep, data in prediction.get('predictions', prediction.get('endpoints', {})).items():
                    endpoint_details[ep] = {
                        'probability': data.get('probability', 0),
                        'prediction': data.get('prediction', 'Unknown'),
                        'confidence': data.get('confidence', 'Unknown')
                    }
                
                results['validation_results'].append({
                    'name': mol['name'],
                    'smiles': mol['smiles'],
                    'category': category,
                    'expected': mol['expected'],
                    'predicted_assessment': assessment,
                    'avg_probability': avg_prob,
                    'is_correct': is_correct,
                    'endpoint_details': endpoint_details
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 {category.upper()} Category: {category_correct}/{len(molecules)} correct")
    
    # Calculate overall accuracy
    accuracy = total_correct / total_tests if total_tests > 0 else 0
    
    results['summary'] = {
        'total_tests': total_tests,
        'correct_predictions': total_correct,
        'accuracy': accuracy,
        'accuracy_percent': f"{accuracy*100:.1f}%"
    }
    
    return results

def print_summary(results):
    """Print validation summary"""
    print("\n" + "="*60)
    print("📋 VALIDATION SUMMARY")
    print("="*60)
    
    summary = results['summary']
    print(f"\n🎯 Overall Accuracy: {summary['accuracy_percent']}")
    print(f"   Correct: {summary['correct_predictions']}/{summary['total_tests']}")
    
    # Count by category
    categories = {}
    for r in results['validation_results']:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'correct': 0, 'total': 0}
        categories[cat]['total'] += 1
        if r['is_correct']:
            categories[cat]['correct'] += 1
    
    print("\n📊 Breakdown by Category:")
    for cat, data in categories.items():
        acc = data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"   {cat.upper()}: {data['correct']}/{data['total']} ({acc:.0f}%)")
    
    # Analysis
    print("\n🔍 Analysis:")
    if summary['accuracy'] >= 0.8:
        print("   ✅ Model shows GOOD alignment with known toxicity data")
    elif summary['accuracy'] >= 0.6:
        print("   🟡 Model shows MODERATE alignment - some improvement needed")
    else:
        print("   ⚠️ Model shows POOR alignment - significant calibration needed")

def main():
    print("="*60)
    print("🧬 DEEP MODEL VALIDATION")
    print("Testing predictions against real-world toxicity data")
    print("="*60)
    
    # Load predictor
    predictor = load_predictor()
    if not predictor:
        return
    
    # Run validation
    results = run_validation(predictor)
    
    # Print summary
    print_summary(results)
    
    # Save results
    output_file = 'results/model_validation_report.json'
    os.makedirs('results', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full results saved to: {output_file}")

if __name__ == "__main__":
    main()
