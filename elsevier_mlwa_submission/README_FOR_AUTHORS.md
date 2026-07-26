# Guide for Submitting to Elsevier: *Machine Learning with Applications* (MLWA)

This folder (`elsevier_mlwa_submission/`) contains everything required to submit your manuscript to Elsevier's Editorial Manager (EM) portal for *Machine Learning with Applications*.

---

## 1. File-by-File Upload Guide for Editorial Manager

When you click **Submit New Manuscript** in the Elsevier Editorial Manager portal, you will be prompted to select item types and upload files. Match them as follows:

| # | File in This Folder | Editorial Manager Item Type | Notes / Compliance Check |
|---|---|---|---|
| 1 | `01_Cover_Letter.md` | **Cover Letter** | Addressed to EIC, highlights methodological novelty & negative empirical findings. |
| 2 | `02_Highlights.md` | **Highlights** | Exactly 5 bullet points; **all under 85 characters** (including spaces/bullets). |
| 3 | `03_Manuscript.pdf` | **Manuscript** (or **Review PDF**) | Cleanly compiled 6-page paper with 0 overfull table boxes and 0 citation warnings. |
| 4 | `04_Graphical_Abstract.png` | **Graphical Abstract** | Visual summary of the counterfactual evaluation pipeline & findings. |
| 5 | `05_Declaration_of_Competing_Interest.md` | **Declaration of Interest Statement** | Mandatory Elsevier disclosure statement ("no known competing financial interests"). |
| 6 | `06_CRediT_Author_Statement.md` | **CRediT Author Statement** | Role taxonomy breakdown for Gaurav Patil and Parth Parmar. |
| 7 | `07_Code_and_Data_Availability.md` | **Data/Code Availability Statement** | Direct links to public MIT-licensed GitHub repository & reproducible logs. |
| 8 | `LaTeX_Source_Files/` | **LaTeX Source Files** (Optional / Accepted) | Contains `main.tex`, `references.bib`, and `figures/` if EM requests LaTeX source. |

---

## 2. Key Journal Metadata to Copy-Paste During Submission

- **Article Title**: 
  > Counterfactual Evaluation of Causal Faithfulness in GINE Explanations for Molecular Toxicity Prediction

- **Section/Category**: 
  > Explainability / Interpretable Machine Learning / Applications in Chemistry & Biomedicine

- **Abstract** (Copy-paste into portal abstract box):
  > We present a scaffold-split evaluation of a GINE-based architecture (RealGraphBranch) on BBBP, BACE, and TOX21, together with a verification methodology that tests, via counterfactual generation, whether removing a molecule's toxicophore lowers the predicted toxicity. We report this as a Counterfactual Consistency Score (CCS)---a counterfactual-sufficiency test that is a necessary-but-not-sufficient proxy for formal causal faithfulness. Across five random seeds (42--46), we evaluate whether natural training aligns attribution masks with model reasoning. We report three primary findings: (1) True causal faithfulness is near zero across datasets (mean CCS: BBBP 0.134, BACE 0.128, TOX21 0.138); removing an attributed toxicophore usually increases rather than decreases predicted toxicity. (2) While our GINE architecture is competitive with ChemProp D-MPNN on single seeds (beating it on BACE 0.921 vs 0.883 and TOX21 0.808 vs 0.793), five-seed bootstrap confidence intervals show that single-seed peaks overestimate generalizable performance (BBBP 95% CI [0.831, 0.868] stays below ChemProp's 0.891). (3) Adding a margin-based causal regularizer fails to consistently improve faithfulness (BACE 0.117 vs 0.128 baseline) and degrades AU-ROC. Our results demonstrate that standard empirical risk minimization does not induce causally consistent attribution in GNNs, providing benchmark evidence that explainability in molecular AI requires objective-level causal alignment rather than post-hoc attribution.

- **Keywords**:
  > Explainable AI (XAI); Graph Neural Networks (GNN); Molecular Toxicity Prediction; Causal Faithfulness; Counterfactual Evaluation; AI in Drug Discovery

---

## 3. Pre-Submission Verification Summary
- **LaTeX Compilation**: Verified with 0 errors, 0 BibTeX warnings, 0 undefined citations, and 0 overfull table boxes.
- **Highlights Length**: All 5 bullet points verified strictly under 85 characters.
- **Reproducibility**: All 5-seed logs and checkpoints publicly verifiable via GitHub and `benchmark_results/`.
