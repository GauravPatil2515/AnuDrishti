# API Endpoints

## PharmaGuard Blueprint (`/api/`)

### Core Prediction
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict` | POST | Single molecule toxicity prediction |
| `/api/analyze/single` | POST | Full PharmaGuard analysis (predictions + OOD + triage + explanation) |
| `/api/analyze/batch` | POST | Batch analysis (ThreadPoolExecutor, 4 workers) |

### Visualization
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/visualize/attention-heatmap` | POST | 2D SVG with GNN atom attention colors (blue→red) |

### Counterfactual / What-If
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/whatif/optimize` | POST | Generate counterfactual molecules (QED > 0.4, SA < 6.0) |

### Utility
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/lookup/smiles` | POST | PubChem name → SMILES lookup |
| `/api/report/export` | POST | Export analysis as text report |

### Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System status, cache stats, model load status |

### Demo
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/demo` | GET/POST | Demo molecule (paracetamol) without triggering live system |

## Request/Response Examples

### `/api/visualize/attention-heatmap`
```json
POST {"smiles": "CC(=O)NC1=CC=C(C=C1)O"}
```
```json
{
  "success": true,
  "smiles": "CC(=O)NC1=CC=C(C=C1)O",
  "attention": [0.0047, 0.1010, 0.0037, 0.1242, ...],
  "attention_source": "gnn_attention",
  "svg": "<svg>...</svg>"
}
```

### `/api/predict`
```json
POST {"smiles": "CC(=O)NC1=CC=C(C=C1)O"}
```
```json
{
  "smiles": "CC(=O)NC1=CC=C(C=C1)O",
  "predictions": {
    "NR-AR": {"probability": 0.12, "prediction": "Non-toxic", "confidence": "High", "source": "Attention-GIN (Tox21)"},
    ...
  },
  "summary": {
    "average_toxicity_probability": 0.23,
    "toxicity_ci_low": 0.18,
    "toxicity_ci_high": 0.28,
    "overall_assessment": "LOW TOXICITY 🟢"
  }
}
```

## Key Implementation Details
- **SMILES Validation**: All endpoints use `_validate_smiles()` with RDKit (returns 400 with clear error messages)
- **Batch Processing**: ThreadPoolExecutor (4 workers) prevents Flask thread blocking
- **LLM Timeout**: 30-second threading guard on Groq calls with deterministic fallback
- **Caching**: LRU cache with TTL (3600s default)