# HLM_CLint Dataset

This dataset requires proprietary data that cannot be automatically downloaded.

## Options:

1. **Use MoleculeNet version (if available)**
   - Check https://moleculenet.org/datasets-1 for public datasets

2. **Use your own data**
   - Prepare a CSV file with columns: `smiles`, `label`
   - Split into train.csv, valid.csv, test.csv
   - Place in this directory

3. **Contact dataset providers**
   - Some ADMET datasets are available from ChEMBL, PubChem, or pharmaceutical databases

## Expected Format:

```csv
smiles,label
CCO,0.5
c1ccccc1,1.2
...
```
