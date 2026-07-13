# DrugTox-AI Dashboard API Documentation

## Overview

The DrugTox-AI Dashboard provides a REST API for molecular toxicity prediction. The API accepts SMILES strings and returns toxicity predictions across 12 different endpoints.

## Base URL

```text
http://localhost:5000/api
```

## Authentication

Currently, no authentication is required for the API endpoints.

## Endpoints

### POST /api/predict

Predict toxicity for a single molecule.

**Request Body:**

```json
{
    "name": "Aspirin",
    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
}
```

**Response:**

```json
{
    "success": true,
    "result": {
        "compound_name": "Aspirin",
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "predictions": {
            "NR-AR-LBD": {
                "probability": 0.342,
                "prediction": "Non-toxic",
                "confidence": "Medium"
            },
            "NR-AR": {
                "probability": 0.156,
                "prediction": "Non-toxic",
                "confidence": "High"
            }
            // ... more endpoints
        },
        "timestamp": "2025-09-25T20:54:00",
        "prediction_id": "abc123"
    }
}
```

### POST /api/batch_predict

Predict toxicity for multiple molecules via file upload.

**Request:** Form-data with file upload

- `file`: CSV/TXT file containing molecules

**Response:** Same format as single prediction, but for multiple compounds.

### GET /api/stats

Get system statistics and performance metrics.

**Response:**

```json
{
    "total_predictions": 1250,
    "success_rate": 0.95,
    "average_processing_time": 1.2,
    "active_endpoints": 12
}
```

### GET /api/export_results

Export prediction results as CSV.

**Query Parameters:**

- `id`: Specific prediction ID (optional)
- `format`: Export format (default: csv)

## Error Handling

All endpoints return errors in the following format:

```json
{
    "success": false,
    "error": "Error description",
    "code": "ERROR_CODE"
}
```

## Rate Limiting

Currently, no rate limiting is implemented.

## Data Formats

### Input Formats

- SMILES strings (standard molecular notation)
- CSV files with columns: name, smiles
- TXT files with one SMILES per line

### Output Formats

- JSON responses for API calls
- CSV exports for result downloads

## Toxicity Endpoints

The system predicts toxicity across 12 nuclear receptor and stress response pathways:

1. NR-AR-LBD (Androgen Receptor Ligand Binding Domain)
2. NR-AR (Androgen Receptor)
3. NR-AhR (Aryl Hydrocarbon Receptor)
4. NR-Aromatase (Aromatase)
5. NR-ER-LBD (Estrogen Receptor Ligand Binding Domain)
6. NR-ER (Estrogen Receptor)
7. NR-PPAR-gamma (Peroxisome Proliferator-Activated Receptor Gamma)
8. SR-ARE (Antioxidant Response Element)
9. SR-ATAD5 (ATAD5)
10. SR-HSE (Heat Shock Element)
11. SR-MMP (MMP)
12. SR-p53 (p53)

## Confidence Levels

Predictions include confidence indicators:

- **High**: Probability > 0.8 or < 0.2
- **Medium**: Probability 0.4-0.6
- **Low**: Probability 0.2-0.4 or 0.6-0.8
