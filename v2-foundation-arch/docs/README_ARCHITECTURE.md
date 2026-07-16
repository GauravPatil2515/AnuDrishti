# Architecture Documentation

## 4-Branch Multimodal Encoder

### Branches
1. **Graph Branch**: Graphormer-style transformer with attention pooling
2. **SMILES Branch**: ChemBERTa-2 language model (77M params, frozen)
3. **3D Conformer Branch**: SchNet distance-based encoding
4. **Descriptor Branch**: RDKit 200-feature projection

### Fusion
Cross-attention between branches → Mixture-of-Experts (4 experts) → Multi-task output (12 tasks)

### Faithfulness Layer
Post-processing verification using counterfactual intervention and attention-grounded LLM prompting.