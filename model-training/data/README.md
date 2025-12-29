# 📊 Training Data

This directory contains all training data for molecular toxicity models.

## 📁 Directory Structure

```
data/
├── raw/                    # Raw downloaded data
│   ├── tox21_10k_data_all.sdf
│   ├── toxcast_data.csv
│   └── chembl_subset.csv
│
└── processed/              # Preprocessed data
    ├── tox21_data.csv      # Main training data
    ├── train_set.csv       # Training split
    ├── val_set.csv         # Validation split
    ├── test_set.csv        # Test split
    └── features.pkl        # Extracted features
```

## 📥 Data Sources

### 1. Tox21 Dataset (Primary)

**Download**:

```bash
# Automated download
python ../scripts/download_data.py --dataset tox21

# Manual download
# Visit: https://tripod.nih.gov/tox21/challenge/
# Download: tox21_10k_data_all.sdf
```

**Details**:

- **Size**: ~12,000 compounds
- **Format**: SDF (Structure Data File)
- **Endpoints**: 12 toxicity assays
- **Quality**: Experimentally validated
- **License**: Public domain

**Endpoints**:

1. NR-AR - Androgen Receptor
2. NR-AR-LBD - Androgen Receptor LBD
3. NR-AhR - Aryl Hydrocarbon Receptor
4. NR-ER - Estrogen Receptor
5. NR-ER-LBD - Estrogen Receptor LBD
6. NR-PPAR-gamma - PPAR-gamma
7. NR-Aromatase - Aromatase
8. SR-ARE - Antioxidant Response Element
9. SR-ATAD5 - ATAD5
10. SR-HSE - Heat Shock Response
11. SR-MMP - Mitochondrial Membrane Potential
12. SR-p53 - p53 Pathway

### 2. ToxCast (Secondary)

**Download**:

```bash
python ../scripts/download_data.py --dataset toxcast
```

**Details**:

- **Size**: ~9,000 compounds
- **Format**: CSV
- **Endpoints**: 700+ assays
- **Source**: EPA ToxCast program

### 3. ChEMBL (Augmentation)

**Download**:

```bash
python ../scripts/download_data.py --dataset chembl --filter-toxicity
```

**Details**:

- **Size**: Filtered subset (~50,000 compounds)
- **Format**: CSV
- **Quality**: Curated pharmaceutical data

## 🔄 Data Preprocessing

### Convert SDF to CSV

```bash
python ../scripts/preprocess_data.py \
  --input raw/tox21_10k_data_all.sdf \
  --output processed/tox21_data.csv \
  --format sdf
```

### Clean and Validate

```bash
python ../scripts/preprocess_data.py \
  --input processed/tox21_data.csv \
  --output processed/tox21_data_clean.csv \
  --validate-smiles \
  --remove-duplicates \
  --handle-missing
```

### Create Train/Val/Test Splits

```bash
python ../scripts/preprocess_data.py \
  --input processed/tox21_data_clean.csv \
  --output processed/ \
  --split \
  --train-ratio 0.7 \
  --val-ratio 0.15 \
  --test-ratio 0.15
```

## 📋 Data Format

### CSV Format

```csv
smiles,NR-AR,NR-AR-LBD,NR-AhR,NR-ER-LBD,SR-MMP,NR-ER,NR-PPAR-gamma,SR-ARE,SR-ATAD5,SR-HSE,SR-p53,NR-Aromatase
CCO,0,0,0,0,0,0,0,0,0,0,0,0
CC(=O)Nc1ccc(O)cc1,0,0,1,0,0,0,0,0,0,0,0,0
c1ccccc1,1,1,1,0,0,1,0,0,0,0,0,0
```

**Columns**:

- `smiles`: SMILES string of molecule
- Endpoint columns: Binary labels (0 = non-toxic, 1 = toxic)

### Missing Values

- **Empty cells**: Compound not tested for that endpoint
- **Handling**: Remove rows or impute based on strategy

## 📊 Data Statistics

### Tox21 Dataset

| Endpoint | Total | Positive | Negative | Positive % |
|----------|-------|----------|----------|------------|
| NR-AR | 8,205 | 582 | 7,623 | 7.1% |
| NR-AR-LBD | 7,364 | 319 | 7,045 | 4.3% |
| NR-AhR | 6,819 | 809 | 6,010 | 11.9% |
| NR-ER-LBD | 7,238 | 1,040 | 6,198 | 14.4% |
| SR-MMP | 7,301 | 1,213 | 6,088 | 16.6% |
| NR-ER | 7,070 | 1,002 | 6,068 | 14.2% |
| NR-PPAR-gamma | 6,677 | 168 | 6,509 | 2.5% |
| SR-ARE | 6,466 | 1,544 | 4,922 | 23.9% |
| SR-ATAD5 | 7,413 | 1,827 | 5,586 | 24.6% |
| SR-HSE | 6,551 | 534 | 6,017 | 8.2% |
| SR-p53 | 7,420 | 1,183 | 6,237 | 15.9% |
| NR-Aromatase | 6,143 | 383 | 5,760 | 6.2% |

### Class Imbalance

Most endpoints have **class imbalance** (more negative than positive samples).

**Handling strategies**:

1. Use `scale_pos_weight` in XGBoost
2. SMOTE oversampling
3. Class weights
4. Stratified sampling

## 🔒 Data Privacy

- All data is publicly available
- No proprietary or confidential information
- Complies with data usage policies

## 📝 Citation

If using Tox21 data, please cite:

```
Tox21 Challenge
National Center for Advancing Translational Sciences (NCATS)
https://tripod.nih.gov/tox21/challenge/
```

## 🐛 Troubleshooting

### Issue: Download Fails

```bash
# Manual download from browser
# Visit: https://tripod.nih.gov/tox21/challenge/
# Place files in data/raw/
```

### Issue: SDF Conversion Fails

```bash
# Install RDKit
pip install rdkit-pypi

# Or use conda
conda install -c conda-forge rdkit
```

### Issue: Missing Values

```bash
# Remove rows with missing labels
python ../scripts/preprocess_data.py --remove-missing

# Or impute
python ../scripts/preprocess_data.py --impute-strategy mean
```

## 📚 Additional Resources

- **Tox21**: <https://tripod.nih.gov/tox21/challenge/>
- **ToxCast**: <https://www.epa.gov/chemical-research/toxicity-forecaster-toxcasttm-data>
- **ChEMBL**: <https://www.ebi.ac.uk/chembl/>
- **RDKit**: <https://www.rdkit.org/docs/>

---

**Last Updated**: 2025-12-09  
**Data Version**: 1.0
