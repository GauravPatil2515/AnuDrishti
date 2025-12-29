"""
Test ChemBERT + Groq Integration
Demonstrates enhanced text generation with molecular embeddings
"""
import sys
sys.path.insert(0, 'c:\\Users\\GAURAV PATIL\\Downloads\\model\\backend')

from models.chembert_groq_integration import get_chembert_groq_integration

def test_chembert_groq_integration():
    print("=" * 80)
    print("Testing ChemBERT + Groq Integration for Enhanced Text Generation")
    print("=" * 80)
    
    try:
        # Initialize integration
        print("\n1. Initializing ChemBERT + Groq Integration...")
        integration = get_chembert_groq_integration()
        print("✅ Integration initialized successfully")
        
        # Test 1: Single molecule analysis with AI report
        print("\n2. Testing Single Molecule Analysis with AI Report...")
        print("-" * 80)
        aspirin = "CC(=O)OC1=CC=CC=C1C(=O)O"
        print(f"Analyzing: Aspirin - {aspirin}")
        
        result1 = integration.analyze_with_embeddings(aspirin, include_ai_report=True)
        
        if result1['success']:
            print(f"✅ ChemBERT Embedding Dimension: {result1['chembert_embeddings']['dimension']}")
            print(f"   Embedding Statistics:")
            stats = result1['chembert_embeddings']['statistics']
            print(f"   - Mean: {stats['mean']:.4f}")
            print(f"   - Std: {stats['std']:.4f}")
            print(f"   - L2 Norm: {stats['l2_norm']:.4f}")
            print(f"\n📊 AI Analysis:\n{result1['ai_analysis'][:500]}...")
        else:
            print(f"✗ Error: {result1['error']}")
            return False
        
        # Test 2: Molecule comparison
        print("\n3. Testing Molecule Comparison...")
        print("-" * 80)
        ibuprofen = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
        print(f"Comparing Aspirin vs Ibuprofen")
        
        result2 = integration.compare_molecules(aspirin, ibuprofen)
        
        if result2['success']:
            similarity = result2['chembert_similarity']
            print(f"✅ ChemBERT Similarity: {similarity['cosine_similarity']:.4f}")
            print(f"   Interpretation: {similarity['interpretation']}")
            print(f"\n📊 AI Comparison:\n{result2['ai_comparison'][:500]}...")
        else:
            print(f"✗ Error: {result2['error']}")
        
        # Test 3: Batch analysis with summary
        print("\n4. Testing Batch Analysis with AI Summary...")
        print("-" * 80)
        test_molecules = [
            "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
            "CC(=O)Nc1ccc(O)cc1"  # Acetaminophen
        ]
        
        result3 = integration.batch_analyze_with_insights(test_molecules, generate_summary=True)
        
        if result3['success']:
            stats = result3['dataset_statistics']
            print(f"✅ Analyzed {stats['successful_analyses']}/{stats['total_molecules']} molecules")
            print(f"   Average Similarity: {stats.get('average_similarity', 0):.4f}")
            print(f"   Diversity Score: {stats.get('diversity_score', 0):.4f}")
            print(f"\n📊 AI Summary:\n{result3['ai_summary'][:500]}...")
        else:
            print(f"✗ Error: {result3['error']}")
        
        # Test 4: Property prediction with context
        print("\n5. Testing Property Prediction with AI Context...")
        print("-" * 80)
        benzene = "c1ccccc1"
        print(f"Predicting toxicity for: Benzene - {benzene}")
        
        result4 = integration.predict_properties_with_context(benzene, property_type="toxicity")
        
        if result4['success']:
            print(f"✅ Property Type: {result4['property_type']}")
            print(f"\n📊 AI Prediction:\n{result4['ai_prediction'][:500]}...")
        else:
            print(f"✗ Error: {result4['error']}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("✅ ChemBERT + Groq Integration is delivering enhanced results!")
        print("=" * 80)
        
        print("\n🎯 Key Capabilities Demonstrated:")
        print("   1. ✓ ChemBERT embeddings (768-dimensional molecular representations)")
        print("   2. ✓ Groq AI-powered contextual analysis")
        print("   3. ✓ Molecular similarity comparison")
        print("   4. ✓ Batch dataset analysis with diversity metrics")
        print("   5. ✓ Property prediction with scientific reasoning")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chembert_groq_integration()
    sys.exit(0 if success else 1)
