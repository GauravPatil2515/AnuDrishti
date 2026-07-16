# Architecture Design: 4-Branch Multimodal Encoder

## High-Level Flow

```
Molecule (SMILES) 
      │
      ├── Graph Branch (GPS/Graphormer)
      │   Input: Atom features (119-dim) + Edge features (bond type)
      │   Output: Graph embedding (256-dim)
      │
      ├── SMILES Branch (ChemBERTa-2)
      │   Input: SMILES tokenized (max_len=128)
      │   Output: Language embedding (768-dim)
      │
      ├── 3D Conformer Branch (SchNet)
      │   Input: Distance matrix (optional, fallback to MMFF if no conformers)
      │   Output: 3D embedding (128-dim)
      │
      └── Descriptor Branch (RDKit)
          Input: 200 physicochemical descriptors
          Output: Descriptor embedding (64-dim)
      
      │
      ▼
Cross-Attention Fusion Layer
      │
      ├── Query: [CLS] token from SMILES
      ├── Keys/Values: concatenated embeddings
      └── Output: fused embedding (768-dim)
      │
      ▼
Mixture of Experts (4-8 experts, sparse gating)
      │
      ▼
Multi-task Output Heads
      ├── BBBP (1 task)
      ├── Tox21 (12 tasks)
      ├── ClinTox (2 tasks)
      ├── BACE (1 task)
      └── SIDER (27 tasks)
```

## Implementation Steps

### Step 1: Graph Branch (GPS)
Replace GIN in `training/train_attention_gin.py`:
- Use GraphormerSelfAttention from torch_geometric.nn.models
- Add 3D positional encoding support

### Step 2: SMILES Branch
- ChemBERTa-2 tokenizer + RoBERTa backbone
- Freeze first 6 layers, fine-tune last 6

### Step 3: 3D Branch
- SchNet encoder: distance-based continuous filter convolutions
- Generate conformers via RDKit ETKDG if not provided

### Step 4: Descriptor Branch
- RDKit descriptors (molecular_weight, logP, TPSA, etc.)
- Normalize to zero mean, unit variance

### Step 5: Fusion
- Cross-attention: query=SMILES [CLS], key/value=other branches
- Concatenate with original inputs (residual)

## Files to Create

- `v2-foundation-arch/architecture_design/multimodal_encoder.py`
- `v2-foundation-arch/architecture_design/graph_branch.py`
- `v2-foundation-arch/architecture_design/smiles_branch.py`
- `v2-foundation-arch/architecture_design/conformer_branch.py`
- `v2-foundation-arch/architecture_design/descriptor_branch.py`
- `v2-foundation-arch/architecture_design/fusion_layer.py`

## Next Action Items

1. [ ] Create `multimodal_encoder.py` stub with input validation
2. [ ] Integrate existing `faithfulness_validator.py` as verification layer
3. [ ] Add MoE layer using `torch.nn.Linear` + learned gating
4. [ ] Run on small MoleculeNet subset to verify shapes