# DeNovo API Reference

## Base URL
```
http://localhost:5000/api
```
(Replace with your deployed URL when applicable)

## Authentication
Some endpoints require the `GROQ_API_KEY` environment variable to be set for LLM-powered features.

## Endpoints

### Health Check
**GET** `/health`

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-25T10:30:00Z",
  "version": "1.0.0"
}
```

### Single Molecule Prediction
**POST** `/predict`

Predict ADMET properties for a single molecule.

**Request Body:**
```json
{
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
}
```

**Response:**
```json
{
  "success": true,
  "predictions": {
    "NR-AR": {
      "probability": 0.15,
      "prediction": "Non-toxic",
      "confidence": "High",
      "source": "Attention-GIN (Tox21)"
    },
    "BBBP": {
      "probability": 0.82,
      "prediction": "Permeable",
      "confidence": "High",
      "source": "Attention-GIN (BBBP)"
    },
    "FDA_APPROVED": {
      "probability": 0.08,
      "prediction": "Approved",
      "confidence": "Very High",
      "source": "Attention-GIN (ClinTox)"
    },
    "CT_TOX": {
      "probability": 0.05,
      "prediction": "Safe in Trials",
      "confidence": "Very High",
      "source": "Attention-GIN (ClinTox)"
    },
    "Clearance": {
      "value": 12.4,
      "unit": "mL/min/kg",
      "interpretation": "Moderate",
      "source": "Attention-GIN (Clearance)"
    }
  },
  "explanation": "The molecule shows low toxicity due to absence of alerting substructures...",
  "faithfulness_score": 0.865
}
```

### Batch Prediction
**POST** `/batch-predict`

Predict ADMET properties for multiple molecules.

**Request Body:**
```json
{
  "smiles_list": [
    "CCO",
    "CC(=O)OC1=CC=CC=C1C(=O)O",
    "c1ccc([N+](=O)[O-])cc1"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "smiles": "CCO",
      "predictions": { /* same structure as single prediction */ },
      "explanation": "...",
      "faithfulness_score": 0.91
    },
    /* ... more results ... */
  ]
}
```

### AI Chat (with Groq)
**POST** `/chat`

Get AI-powered explanations about molecular properties.

**Request Body:**
```json
{
  "message": "Why is nitrobenzene considered toxic?",
  "smiles": "c1ccc([N+](=O)[O-])cc1"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Nitrobenzene contains a nitro group (-NO2) which is a known toxicophore...",
  "sources": ["Tox21 literature", "PubChem"],
  "confidence": 0.92
}
```

### Model Information
**GET** `/model-info`

Retrieve information about loaded models.

**Response:**
```json
{
  "loaded_models": [
    "attention_gin",
    "bbbp",
    "clintox",
    "clearance",
    "xgboost"
  ],
  "model_details": {
    "attention_gin": {
      "type": "Attention-GIN (Tox21)",
      "num_tasks": 12,
      "version": "1.2",
      "loaded_at": "2026-06-25T09:15:00Z"
    },
    "bbbp": {
      "type": "Attention-GIN (BBBP)",
      "num_tasks": 1,
      "version": "1.0",
      "loaded_at": "2026-06-25T09:15:00Z"
    },
    "clintox": {
      "type": "Attention-GIN (ClinTox)",
      "num_tasks": 2,
      "version": "1.0",
      "loaded_at": "2026-06-25T09:15:00Z"
    },
    "clearance": {
      "type": "Attention-GIN (Clearance)",
      "num_tasks": 1,
      "version": "1.0",
      "loaded_at": "2026-06-25T09:15:00Z"
    },
    "xgboost": {
      "type": "XGBoost (5 NR endpoints)",
      "num_tasks": 5,
      "version": "1.0",
      "loaded_at": "2026-06-25T09:15:00Z"
    }
  }
}
```

### Feedback Submission
**POST** `/feedback`

Submit feedback on predictions or explanations.

**Request Body:**
```json
{
  "prediction_id": "abc123",
  "feedback_type": "explanation_quality",
  "rating": 4,
  "comments": "Explanation was clear but missed mentioning the aromatic ring contribution"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Thank you for your feedback!"
}
```

## Error Responses
All endpoints return JSON with the following structure on error:
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "VALIDATION_ERROR|MODEL_ERROR|INTERNAL_ERROR",
  "timestamp": "2026-06-25T10:30:00Z"
}
```

## Rate Limiting
- Default: 100 requests per minute per IP
- Can be configured via `RATE_LIMIT` environment variable

## CORS
Enabled for all origins by default. Configure via `CORS_ORIGINS` environment variable.

## Versioning
Current API version: v1 (implicit in endpoint paths)

## Example Usage (curl)
```bash
# Health check
curl http://localhost:5000/api/health

# Single prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CC(=O)OC1=CC=CC=C1C(=O)O"}'

# Batch prediction
curl -X POST http://localhost:5000/api/batch-predict \
  -H "Content-Type: application/json" \
  -d '{"smiles_list":["CCO","c1ccc([N+](=O)[O-])cc1"]}'

# AI Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain this molecule","smiles":"CC(=O)OC1=CC=CC=C1C(=O)O"}'
```

## SDKs & Clients
- **Python**: Available via `pip install denovo-client` (internal)
- **JavaScript**: Fetch/Axios compatible
- **cURL**: As shown above
- **Postman**: Collection available in `docs/postman_collection.json`

## Changelog
### v1.0.0 (Initial Release)
- Core prediction endpoints
- Batch processing
- AI chat integration
- Feedback system
- Health monitoring

## Contact
For API support, contact: gauravppaiml123@gst.sies.edu.in