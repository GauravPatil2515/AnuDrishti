"""
Test ChemBERT Analyzer Integration
"""
import sys
sys.path.insert(0, 'c:\\Users\\GAURAV PATIL\\Downloads\\model\\backend')

from models.chembert_analyzer import get_chembert_analyzer

def test_chembert_analyzer():
    print("=" * 70)
    print("Testing ChemBERT Analyzer Integration")
    print("=" * 70)
    
    try:
        # Initialize analyzer
        print("\n1. Initializing ChemBERT Analyzer...")
        analyzer = get_chembert_analyzer()
        print("✓ Analyzer initialized successfully")
        
        # Test single molecule analysis
        print("\n2. Testing single molecule analysis...")
        aspirin = "CC(=O)OC1=CC=CC=C1C(=O)O"
        result = analyzer.analyze_molecule(aspirin)
        
        if result['success']:
            print(f"✓ Analyzed: {result['smiles']}")
            print(f"  Embedding shape: {result['embedding_shape']}")
            print(f"  Sample embedding values: {result['embedding'][:5]}")
        else:
            print(f"✗ Error: {result['error']}")
            return False
        
        # Test batch analysis
        print("\n3. Testing batch analysis...")
        test_molecules = [
            "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"  # Caffeine
        ]
        
        batch_results = analyzer.batch_analyze(test_molecules)
        print(f"✓ Analyzed {len(batch_results)} molecules")
        for i, res in enumerate(batch_results, 1):
            print(f"  Molecule {i}: {res['smiles'][:30]}... - Embedding shape: {res['embedding_shape']}")
        
        # Test similarity analysis
        print("\n4. Testing molecular similarity analysis...")
        aspirin = "CC(=O)OC1=CC=CC=C1C(=O)O"
        ibuprofen = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
        
        sim_result = analyzer.similarity_analysis(aspirin, ibuprofen)
        print(f"✓ Similarity between Aspirin and Ibuprofen:")
        print(f"  Cosine Similarity: {sim_result['cosine_similarity']:.4f}")
        print(f"  Interpretation: {sim_result['interpretation']}")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("✅ ChemBERT Analyzer is ready for integration into the project")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chembert_analyzer()
    sys.exit(0 if success else 1)
