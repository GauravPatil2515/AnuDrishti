# Selected Case Studies for Paper

## Case Study 1: High-Confidence Faithful Explanation
**SMILES**: `F[Sn](c1ccccc1)(c1ccccc1)c1ccccc1`
**Predicted Toxicity**: 0.779
**Faithfulness Score**: 0.794

### Generated Explanation:
**Summary**: The molecule F[Sn](c1ccccc1)(c1ccccc1)c1ccccc1 has a predicted toxicity of 77.9%. No high-attention substructures were identified, indicating that the model did not highlight any specific toxicophores. The toxicity risk is likely due to the overall molecular structure rather than a specific functional group.

**Mechanism**: The molecule's toxicity is predicted to be 77.9%, but the exact mechanism cannot be determined due to the absence of high-attention substructures. The model's prediction is based on the overall molecular structure, but no specific toxicophores or features were identified with an attention score above the threshold. Further analysis would be required to determine the underlying causes of the predicted toxicity.

**Identified Toxicophores**:

---

## Case Study 2: Explanation Rejection Analysis
This case illustrates the system's ability to reject unfaithful explanations.

**SMILES**: `CN(C)c1ccc(N)cc1`
**Predicted Toxicity**: 0.497
**Status**: Failed faithfulness validation after multiple attempts
**Attempts**: The system tried 3 times to generate a grounded explanation but failed.
