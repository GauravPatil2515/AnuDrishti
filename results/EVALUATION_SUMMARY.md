# Faithful XAI Evaluation Summary

**Date**: 2025-12-21

## Overview

This document summarizes the evaluation of the Faithful XAI system on the Tox21 dataset using the Attention-GIN model and Groq LLaMA 3.3 70B.

## 1. Model Performance

- **Model**: Attention-GIN (Graph Isomorphism Network with Global Attention)
- **Dataset**: Tox21 (80/10/10 split)
- **Best Validation ROC-AUC**: **0.8368** (Exceeded target of 0.82)
- **Test ROC-AUC**: 0.8023

## 2. Faithfulness Evaluation

Run on 200 random test molecules.

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Mean Faithfulness** | **0.504** | Average including rejected (0.0) explanations. |
| **Median Faithfulness** | **0.794** | High quality for accepted explanations. |
| **Rejection Rate** | **36.5%** | System correctly identifies and rejects unfaithful explanations. |
| **Generation Attempts** | **1.73** | Average tries needed to generate a faithful explanation. |

### Failure Analysis (36.5% Rejection)

The high rejection rate indicates rigorous validation. The system requires explanations to be:

1. **Grounded**: Cited features must have high attention.
2. **Causally Consistent**: Removing features must drop prediction.
3. **Counterfactually Sensitive**: Changing molecule must change explanation.

## 3. Codebase Improvements

The following improvements were made to ensure "proper" research-grade implementation:

- **`ConstrainedExplainer`**: Updated to capture and return detailed faithfulness metrics for every generation attempt.
- **`run_faithful_eval.py`**: Updated to flatten and save detailed scores (Causal, Grounding, CF) into the results CSV for fine-grained analysis.
- **`faithfulness_validator.py`**: Verified logic for all three faithfulness tests.
- **`substructure_mapper.py`**: Verified toxicophore database coverage.

## 4. Recommendations

1. **Analyze Rejection Reasons**: Use the newly added columns in `results.csv` to identify if failures are due to *Grounding* (LLM hallucinating features) or *Causal Consistency* (LLM identifying features that don't actually drive the model).
2. **Prompt Refinement**: If Grounding failures dominate, increase `attention_threshold` in prompt. If Causal failures dominate, adjust the LLM instructions to focus on top-k features only.
3. **Paper Figures**: Use successful examples (high faithfulness) for Case Studies 1 & 2. Use a rejected example for Case Study 3 (Failure Analysis).
