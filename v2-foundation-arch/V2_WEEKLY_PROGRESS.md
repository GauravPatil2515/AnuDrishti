# v2-foundation-arch - Week 1-12 Progress

## Week 1-2: Complete
- [x] Literature spreadsheet with SOTA baselines
- [x] 4-branch architecture skeleton (all smoke tests passed)
- [x] MultimodalMoleculeEncoder with cross-attention fusion
- [x] GraphTransformerBranch, SMILESBranch, ConformerBranch, DescriptorBranch

## Week 3-5: Complete  
- [x] GraphMAE pretraining module
- [x] Asymmetric/UW loss functions for class imbalance
- [x] Training pipeline framework

## Week 6-7: Complete
- [x] Pretrained weight integration framework
- [x] Optuna hyperparameter search connected to model

## Week 8-9: Complete
- [x] Optuna integration (5-trial test passed)
- [x] Ensemble with faithfulness verification layer

## Week 11-12: In Progress
- [x] Ablation study framework with expected metrics
- [x] v2 metrics macros for paper
- [ ] Need actual training runs on MoleculeNet to fill final numbers

## Week 12 Deliverables
- Title: "Multimodal Molecular Foundation Model with Faithful Causal Explanation"
- v1 contribution preserved as unique novelty (faithfulness verification)
- Target SOTA: TOX21=0.918, BBBP=0.924, ClinTox=0.931