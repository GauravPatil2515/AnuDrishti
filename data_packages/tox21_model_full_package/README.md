# ADMET Prediction Model Package

## Model Information
- **Task**: Tox21
- **Model Type**: GIN
- **Task Type**: classification
- **Number of Tasks**: 12

## Usage
See `inference.py` for CLI usage. Typical command:
```
python inference.py --model_path model.pth --data_path your_data.csv --task_name tox21 --config config_finetune.yaml
```

## Files Included
- model.pth: Trained model weights
- config_finetune.yaml: Model configuration (task settings)
- README.md: This file

