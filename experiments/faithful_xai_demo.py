#!/usr/bin/env python3
"""
Faithful XAI Complete Integration Example
==========================================
Demonstrates the complete pipeline for faithful explanation generation.

Usage:
    python faithful_xai_demo.py --smiles "c1ccc([N+](=O)[O-])cc1"

Author: DeNovo-XAI Research Team
"""

import sys
import argparse
import numpy as np
from pathlib import Path

# Add paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR / 'models'))
sys.path.insert(0, str(BACKEND_DIR / 'utils'))

print("=" * 70)
print("FAITHFUL XAI DEMO: Causally-Constrained Molecular Explanations")
print("=" * 70)


def run_faithful_explanation_pipeline(smiles: str, use_mock_llm: bool = True):
    """
    Run the complete faithful explanation pipeline.
    
    Args:
        smiles: SMILES string to analyze
        use_mock_llm: Use mock LLM (True) or real Groq (False)
    """
    print(f"\n📋 Analyzing molecule: {smiles}")
    print("-" * 70)
    
    # Step 1: Load Model
    print("\n[1/6] Loading Attention-GIN model...")
    try:
        from attention_ginet import AttentionGINet
        import torch
        
        model = AttentionGINet(num_tasks=12)
        model.eval()
        print("✅ Model loaded (untrained demo version)")
        
        # For demo, we'll use the model architecture
        # In production, load trained weights:
        # model.load_state_dict(torch.load('path/to/trained_model.pth'))
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Step 2: Initialize Components
    print("\n[2/6] Initializing components...")
    
    try:
        from substructure_mapper import SubstructureMapper
        from counterfactual_generator import CounterfactualGenerator
        from faithfulness_validator import FaithfulnessValidator
        
        substructure_mapper = SubstructureMapper()
        counterfactual_generator = CounterfactualGenerator()
        faithfulness_validator = FaithfulnessValidator(
            model=model,
            counterfactual_generator=counterfactual_generator
        )
        
        print("✅ SubstructureMapper initialized (30+ toxicophores)")
        print("✅ CounterfactualGenerator initialized")
        print("✅ FaithfulnessValidator initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return
    
    # Step 3: Initialize LLM
    print("\n[3/6] Initializing LLM...")
    
    try:
        if use_mock_llm:
            from reasoner import MockLLMProvider
            llm = MockLLMProvider()
            print("✅ Mock LLM initialized (for demo)")
        else:
            from reasoner import GroqLLMProvider
            llm = GroqLLMProvider()
            if llm.is_available():
                print("✅ Groq LLM initialized (LLaMA 3.3 70B)")
            else:
                print("⚠️ Groq API key not found, using mock")
                llm = MockLLMProvider()
    except Exception as e:
        print(f"⚠️ LLM initialization issue: {e}, using mock")
        from reasoner import MockLLMProvider
        llm = MockLLMProvider()
    
    # Step 4: Initialize Constrained Explainer
    print("\n[4/6] Initializing Constrained Explainer...")
    
    try:
        from constrained_explainer import ConstrainedExplainer
        
        explainer = ConstrainedExplainer(
            model=model,
            llm_provider=llm,
            substructure_mapper=substructure_mapper,
            faithfulness_validator=faithfulness_validator,
            max_generation_attempts=3
        )
        
        print("✅ Constrained Explainer initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize explainer: {e}")
        return
    
    # Step 5: Run Prediction
    print("\n[5/6] Running prediction with attention...")
    
    try:
        # Convert SMILES to graph
        from rdkit import Chem
        import torch
        from torch_geometric.data import Data
        
        # For demo, create mock data
        # In production, use proper SMILES → graph conversion
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"❌ Invalid SMILES: {smiles}")
            return
        
        mol = Chem.AddHs(mol)
        n_atoms = mol.GetNumAtoms()
        
        # Create dummy graph data for demo
        x = torch.randint(0, 119, (n_atoms, 2))
        edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
        edge_attr = torch.randint(0, 5, (2, 2))
        batch = torch.zeros(n_atoms, dtype=torch.long)
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, batch=batch)
        
        # Forward pass
        with torch.no_grad():
            features, predictions, attention_info = model(data, return_attention=True)
        
        # Get results
        prediction = torch.sigmoid(predictions).mean().item()
        attention_weights = attention_info['attention_weights'].numpy()
        
        print(f"✅ Prediction: {prediction:.1%} toxic")
        print(f"   Attention range: {attention_weights.min():.3f} - {attention_weights.max():.3f}")
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        # Use mock data for demo
        prediction = 0.85
        attention_weights = np.random.dirichlet(np.ones(n_atoms))
        attention_weights[0:3] *= 3  # Boost first 3 atoms
        attention_weights /= attention_weights.sum()
        print(f"⚠️ Using mock prediction: {prediction:.1%}")
    
    # Step 6: Generate Faithful Explanation
    print("\n[6/6] Generating faithful explanation...")
    print("-" * 70)
    
    try:
        explanation = explainer.explain(
            smiles=smiles,
            prediction=prediction,
            attention_weights=attention_weights,
            validate=True
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("FAITHFUL EXPLANATION RESULT")
        print("=" * 70)
        
        if explanation.validation_passed:
            print(f"\n✅ EXPLANATION ACCEPTED")
            print(f"   Faithfulness Score: {explanation.faithfulness_score:.3f}")
            print(f"   Generation Attempts: {explanation.generation_attempts}")
        else:
            print(f"\n❌ EXPLANATION REJECTED")
            print(f"   Reason: {explanation.rejection_reason}")
            print(f"   Attempts: {explanation.generation_attempts}")
        
        print(f"\n📊 Prediction: {explanation.prediction:.1%} toxic")
        
        print(f"\n📝 Executive Summary:")
        print(f"   {explanation.executive_summary}")
        
        if explanation.identified_toxicophores:
            print(f"\n🔬 Identified Toxicophores:")
            for tox in explanation.identified_toxicophores:
                print(f"   • {tox.get('name', 'Unknown')}")
                print(f"     Attention: {tox.get('attention_score', 0):.1%}")
                print(f"     Mechanism: {tox.get('mechanism', 'N/A')[:80]}...")
        
        if explanation.mechanism:
            print(f"\n⚗️ Mechanism:")
            print(f"   {explanation.mechanism}")
        
        print("\n" + "=" * 70)
        
        # Show rejection statistics
        rejection_rate = explainer.get_rejection_rate()
        print(f"\n📈 Explainer Statistics:")
        print(f"   Rejection Rate: {rejection_rate:.1%}")
        
    except Exception as e:
        print(f"❌ Explanation generation failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Faithful XAI Demo: Generate causally-constrained explanations'
    )
    parser.add_argument(
        '--smiles',
        type=str,
        default='c1ccc([N+](=O)[O-])cc1',
        help='SMILES string to analyze (default: nitrobenzene)'
    )
    parser.add_argument(
        '--use-groq',
        action='store_true',
        help='Use real Groq LLM (requires API key)'
    )
    
    args = parser.parse_args()
    
    run_faithful_explanation_pipeline(
        smiles=args.smiles,
        use_mock_llm=not args.use_groq
    )
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
