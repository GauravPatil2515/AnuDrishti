# Selected Case Studies for Paper

## Case Study 1: High-Confidence Faithful Explanation
**SMILES**: `CCN(CC)C(=S)SSC(=S)N(CC)CC`
**Predicted Toxicity**: 0.556
**Faithfulness Score**: 1.000

### Generated Explanation:
**Summary**: The prediction is driven by the presence of a thiocarbonyl group.

**Mechanism**: Thiocarbonyls are metabolized to reactive sulfur species that modify cellular proteins.

**Identified Toxicophores**:
- **thiocarbonyl** (Importance: N/A)

---

## Case Study 2: Explanation Rejection Analysis
This case illustrates the system's ability to reject unfaithful explanations.

**SMILES**: `Nc1ccc(C(=O)Nc2ccccc2N)cc1`
**Predicted Toxicity**: 0.500
**Status**: Failed faithfulness validation after max attempts
**Attempts**: The system tried 3 times to generate a grounded explanation but failed.
