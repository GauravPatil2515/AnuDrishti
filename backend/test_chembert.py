"""
Simple test script to load and verify ChemBERT model
"""
import sys
import torch
from transformers import AutoTokenizer, AutoModel

def test_chembert():
    print("=" * 60)
    print("ChemBERT Model Loading Test")
    print("=" * 60)
    
    try:
        # Check if required packages are installed
        print("\n1. Checking dependencies...")
        print(f"   ✓ PyTorch version: {torch.__version__}")
        print(f"   ✓ CUDA available: {torch.cuda.is_available()}")
        
        # Load ChemBERTa model
        print("\n2. Loading ChemBERTa tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("seyonec/ChemBERTa-zinc-base-v1")
        print("   ✓ Tokenizer loaded successfully")
        
        print("\n3. Loading ChemBERTa model...")
        model = AutoModel.from_pretrained("seyonec/ChemBERTa-zinc-base-v1")
        print("   ✓ Model loaded successfully")
        
        # Test with sample SMILES strings
        print("\n4. Testing with sample SMILES strings...")
        test_smiles = [
            "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"  # Caffeine
        ]
        
        for idx, smiles in enumerate(test_smiles, 1):
            print(f"\n   Test {idx}: {smiles}")
            
            # Tokenize
            inputs = tokenizer(smiles, return_tensors="pt", padding=True, truncation=True)
            print(f"   ✓ Tokenized (input shape: {inputs['input_ids'].shape})")
            
            # Get embeddings
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Get the [CLS] token embedding (sentence/molecule representation)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            print(f"   ✓ Generated embeddings (shape: {cls_embedding.shape})")
            print(f"   ✓ Embedding sample: {cls_embedding[0][:5].tolist()}")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("✓ ChemBERT is ready to be integrated into the project")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install transformers torch")
        return False
        
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chembert()
    sys.exit(0 if success else 1)
