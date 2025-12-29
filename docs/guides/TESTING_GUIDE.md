# 🧪 Testing Enhanced Features

## Quick Test Commands

### Test RDKit Predictor

```bash
cd backend
python -c "from models.rdkit_predictor import EnhancedDrugToxPredictor; p = EnhancedDrugToxPredictor(); print('✅ RDKit:', p.use_rdkit); print('✅ Endpoints:', len(p.endpoints))"
```

### Test SMILES Validation

```bash
python -c "from models.rdkit_predictor import EnhancedDrugToxPredictor; p = EnhancedDrugToxPredictor(); valid, canonical, err = p.validate_smiles('CCO'); print('Valid:', valid); print('Canonical:', canonical)"
```

### Test Prediction

```bash
python -c "from models.rdkit_predictor import EnhancedDrugToxPredictor; p = EnhancedDrugToxPredictor(); r = p.predict_single('CCO'); print('Endpoints:', r['summary']['total_endpoints']); print('Toxicity:', r['summary']['overall_assessment'])"
```

### Test Rate Limiter

```bash
python -c "from utils.rate_limiter import RateLimiter; r = RateLimiter(); allowed, retry, remaining = r.check_rate_limit('prediction'); print('Allowed:', allowed); print('Remaining:', remaining)"
```

## API Testing

### Test Enhanced Backend

```bash
# Start enhanced backend
python app_enhanced.py

# In another terminal:
# Test health
curl http://localhost:5000/api/health

# Test validation
curl -X POST http://localhost:5000/api/validate/smiles \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CCO"}'

# Test prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CCO"}'

# Test rate limit status
curl http://localhost:5000/api/rate-limit/status
```

## Expected Results

### Health Check

```json
{
  "status": "healthy",
  "rdkit_enabled": true,
  "total_endpoints": 12,
  "rate_limiting_enabled": true
}
```

### SMILES Validation

```json
{
  "success": true,
  "is_valid": true,
  "canonical_smiles": "CCO",
  "validation_method": "rdkit"
}
```

### Prediction

```json
{
  "total_endpoints": 12,
  "toxic_endpoints": "2/12",
  "risk_category": "Low Risk",
  "feature_method": "rdkit"
}
```
