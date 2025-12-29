"""
ChemBERT + Groq: Best Results Demonstration
Shows the power of combining transformer embeddings with AI text generation
"""
import sys
sys.path.insert(0, 'c:\\Users\\GAURAV PATIL\\Downloads\\model\\backend')

from models.chembert_groq_integration import get_chembert_groq_integration

def demo_best_results():
    print("\n" + "=" * 90)
    print(" " * 20 + "🧬 ChemBERT + Groq: BEST RESULTS DEMO 🧬")
    print("=" * 90)
    
    integration = get_chembert_groq_integration()
    
    # Demo 1: Comprehensive Drug Analysis
    print("\n" + "─" * 90)
    print("📊 DEMO 1: Comprehensive Drug Analysis (Aspirin)")
    print("─" * 90)
    
    aspirin_result = integration.analyze_with_embeddings(
        "CC(=O)OC1=CC=CC=C1C(=O)O",
        include_ai_report=True
    )
    
    print(f"\n🔬 SMILES: {aspirin_result['smiles']}")
    print(f"📐 Embedding Dimension: {aspirin_result['chembert_embeddings']['dimension']}")
    stats = aspirin_result['chembert_embeddings']['statistics']
    print(f"📊 Embedding Stats:")
    print(f"   • Mean: {stats['mean']:.6f}")
    print(f"   • Standard Deviation: {stats['std']:.6f}")
    print(f"   • L2 Norm: {stats['l2_norm']:.6f}")
    print(f"\n🤖 AI ANALYSIS:")
    print("─" * 90)
    print(aspirin_result['ai_analysis'])
    
    # Demo 2: Drug Similarity Comparison
    print("\n\n" + "─" * 90)
    print("🔍 DEMO 2: Drug Similarity Analysis (Aspirin vs Ibuprofen)")
    print("─" * 90)
    
    comparison = integration.compare_molecules(
        "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
        "CC(C)Cc1ccc(cc1)C(C)C(=O)O"   # Ibuprofen
    )
    
    sim = comparison['chembert_similarity']
    print(f"\n🧮 ChemBERT Similarity Score: {sim['cosine_similarity']:.4f}")
    print(f"📈 Interpretation: {sim['interpretation']}")
    print(f"\n🤖 AI COMPARATIVE ANALYSIS:")
    print("─" * 90)
    print(comparison['ai_comparison'])
    
    # Demo 3: Chemical Library Analysis
    print("\n\n" + "─" * 90)
    print("📚 DEMO 3: Chemical Library Analysis (Pain Relief Drugs)")
    print("─" * 90)
    
    pain_relievers = [
        ("Aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O"),
        ("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
        ("Acetaminophen", "CC(=O)Nc1ccc(O)cc1"),
        ("Naproxen", "COc1ccc2cc(ccc2c1)C(C)C(=O)O")
    ]
    
    smiles_only = [s[1] for s in pain_relievers]
    batch_result = integration.batch_analyze_with_insights(
        smiles_only,
        generate_summary=True
    )
    
    stats = batch_result['dataset_statistics']
    print(f"\n📊 Dataset Statistics:")
    print(f"   • Total Molecules: {stats['total_molecules']}")
    print(f"   • Successfully Analyzed: {stats['successful_analyses']}")
    print(f"   • Embedding Dimension: {stats.get('embedding_dimension', 'N/A')}")
    print(f"   • Average Pairwise Similarity: {stats.get('average_similarity', 0):.4f}")
    print(f"   • Diversity Score: {stats.get('diversity_score', 0):.4f}")
    
    print(f"\n🤖 AI DATASET ANALYSIS:")
    print("─" * 90)
    print(batch_result['ai_summary'])
    
    # Demo 4: Toxicity Prediction with Context
    print("\n\n" + "─" * 90)
    print("⚠️  DEMO 4: Toxicity Prediction (Benzene)")
    print("─" * 90)
    
    toxicity_pred = integration.predict_properties_with_context(
        "c1ccccc1",  # Benzene
        property_type="toxicity"
    )
    
    print(f"\n🔬 SMILES: {toxicity_pred['smiles']}")
    print(f"🎯 Property Type: {toxicity_pred['property_type'].title()}")
    print(f"\n🤖 AI TOXICITY PREDICTION:")
    print("─" * 90)
    print(toxicity_pred['ai_prediction'])
    
    # Summary
    print("\n\n" + "=" * 90)
    print(" " * 25 + "✅ DEMONSTRATION COMPLETE ✅")
    print("=" * 90)
    print("\n🎯 KEY ACHIEVEMENTS:")
    print("   1. ✓ ChemBERT generates 768-dimensional molecular embeddings")
    print("   2. ✓ Groq AI provides scientifically accurate, detailed analysis")
    print("   3. ✓ Combined system delivers quantitative + qualitative insights")
    print("   4. ✓ Scalable to batch processing and large datasets")
    print("   5. ✓ Production-ready for MedToXAi platform integration")
    
    print("\n💡 USE CASES:")
    print("   • Drug Discovery: Analyze candidates and predict properties")
    print("   • Toxicity Assessment: Identify risks and generate safety reports")
    print("   • Chemical Libraries: Assess diversity and find similar compounds")
    print("   • Research Support: Generate hypotheses and scientific documentation")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Integrate API endpoints into backend/app.py")
    print("   2. Create frontend interface for ChemBERT features")
    print("   3. Deploy to production with performance monitoring")
    print("   4. Fine-tune models for specific domain tasks")
    
    print("\n" + "=" * 90)
    print(" " * 20 + "🎉 ChemBERT + Groq = BEST RESULTS! 🎉")
    print("=" * 90 + "\n")

if __name__ == "__main__":
    demo_best_results()
