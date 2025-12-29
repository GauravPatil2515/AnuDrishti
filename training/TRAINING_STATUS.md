# ADMET Model Training Status

**Last Updated**: December 23, 2025

---

## 📊 Dataset Status

| Model | Dataset | Samples | Train | Valid | Test | Status |
|-------|---------|---------|-------|-------|------|--------|
| **Tox21** | tox21.csv | ~7,800 | ✅ | ✅ | ✅ | ✅ Ready (TRAINED) |
| **BBBP** | BBBP.csv | 2,051 | 1,640 | 205 | 206 | ✅ Ready |
| **ClinTox** | clintox.csv | 1,491 | 1,192 | 149 | 150 | ✅ Ready |
| **Caco2** | - | - | - | - | - | ❌ No data |
| **Clearance** | - | - | - | - | - | ❌ No data |
| **HLM_CLint** | - | - | - | - | - | ❌ No data |

---

## 🏋️ Model Training Status

| Model | Trained | ROC-AUC / RMSE | Weight File |
|-------|---------|----------------|-------------|
| **Tox21 (Attention-GIN)** | ✅ Yes | 0.8368 | `results/trained_models/attention_gin_model.pth` |
| **BBBP** | ❌ No | - | - |
| **ClinTox** | ❌ No | - | - |
| **Caco2** | ❌ No | - | - |
| **Clearance** | ❌ No | - | - |
| **HLM_CLint** | ❌ No | - | - |

---

## 📁 Directory Structure

```
DeNovo-main/
├── MODELS/
│   ├── tox21_model_full_package/
│   │   └── data/tox21/tox21.csv ✅
│   ├── bbbp_model_full_package/
│   │   └── data/bbbp/
│   │       ├── bbbp.csv ✅
│   │       ├── train.csv ✅
│   │       ├── valid.csv ✅
│   │       └── test.csv ✅
│   ├── clintox_model_package/
│   │   └── data/clintox/
│   │       ├── clintox.csv ✅
│   │       ├── train.csv ✅
│   │       ├── valid.csv ✅
│   │       └── test.csv ✅
│   ├── caco2_model_full_package/ ⚠️ (no data)
│   ├── clearance_model_full_package/ ⚠️ (no data)
│   └── hlm_clint_model_full_package/ ⚠️ (no data)
│
├── results/trained_models/
│   └── attention_gin_model.pth ✅ (Tox21)
│
├── training/
│   ├── train_all_models.py
│   ├── download_datasets.py
│   └── training_config.yaml
│
└── docs/
    └── MODEL_TRAINING.md
```

---

## 🚀 Next Steps

### Immediate (Ready to Train)

1. **Train BBBP Model** - Blood-Brain Barrier Penetration

   ```powershell
   cd MODELS\bbbp_model_full_package
   python finetune.py --task bbbp --epochs 100
   ```

2. **Train ClinTox Model** - Clinical Toxicity

   ```powershell
   cd MODELS\clintox_model_package
   python finetune.py --task clintox --epochs 100
   ```

### Future (Need Data)

3. **Caco2** - Requires proprietary intestinal permeability data
2. **Clearance** - Requires proprietary metabolic data
3. **HLM_CLint** - Requires proprietary hepatic clearance data

---

## 🔗 Data Sources

For missing datasets, consider:

- [MoleculeNet](https://moleculenet.org/) - Open datasets
- [ChEMBL](https://www.ebi.ac.uk/chembl/) - Bioactivity database
- [ToxCast/Tox21](https://comptox.epa.gov/) - EPA toxicity data
- [ADME@NCATS](https://opendata.ncats.nih.gov/) - NCATS ADME data
