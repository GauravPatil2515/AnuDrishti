# 🚀 Quick Reference - Enhanced Features

## ✅ **Status: ALL FEATURES WORKING**

```
✅ RDKit Integration      - 200+ molecular descriptors
✅ SMILES Validation      - Full canonicalization  
✅ 12 Toxicity Endpoints  - Comprehensive analysis
✅ API Rate Limiting      - Production-ready
```

---

## 🔥 **Quick Commands**

### Start Backend

```powershell
cd backend
python app_enhanced.py
```

### Test All Features

```powershell
powershell -ExecutionPolicy Bypass -File test_api.ps1
```

### Individual Tests

```powershell
# Health check
Invoke-RestMethod http://localhost:5000/api/health

# Validate SMILES
$body = @{smiles="CCO"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/validate/smiles -Method Post -ContentType "application/json" -Body $body

# Predict toxicity
$body = @{smiles="CCO"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/predict -Method Post -ContentType "application/json" -Body $body
```

---

## 📊 **12 Toxicity Endpoints**

### Nuclear Receptors (7)

1. NR-AR - Androgen Receptor
2. NR-AR-LBD - Androgen Receptor LBD
3. NR-AhR - Aryl Hydrocarbon Receptor
4. NR-ER - Estrogen Receptor
5. NR-ER-LBD - Estrogen Receptor LBD
6. NR-PPAR-gamma - PPAR-gamma
7. NR-Aromatase - Aromatase

### Stress Response (5)

8. SR-MMP - Mitochondrial Membrane Potential
9. SR-ARE - Antioxidant Response Element
10. SR-ATAD5 - DNA Damage Response
11. SR-HSE - Heat Shock Response
12. SR-p53 - p53 Pathway

---

## 🔒 **Rate Limits**

| Tier | Limit | Endpoints |
|------|-------|-----------|
| default | 60/min | Health, info |
| prediction | 30/min | Predictions |
| batch | 10/min | Batch processing |
| ai | 20/min | AI analysis |

---

## 📁 **Key Files**

### Backend

- `app_enhanced.py` - Enhanced Flask API
- `models/rdkit_predictor.py` - RDKit predictor
- `utils/rate_limiter.py` - Rate limiting
- `test_api.ps1` - PowerShell test script

### Documentation

- `ENHANCED_FEATURES_GUIDE.md` - Complete guide
- `VERIFICATION_REPORT.md` - Test results
- `TESTING_GUIDE.md` - Quick tests
- `VISUAL_OVERVIEW.md` - Architecture diagrams

---

## 🎯 **API Endpoints**

```
GET  /api/health                   - System status
GET  /api/endpoints                - List all 12 endpoints
POST /api/validate/smiles          - Validate SMILES
POST /api/predict                  - Predict toxicity
GET  /api/rate-limit/status        - Rate limit info
```

---

## 💡 **Quick Tips**

1. **RDKit is working** - Check `rdkit_enabled: true` in health
2. **12 endpoints active** - Check `total_endpoints: 12`
3. **Rate limiting active** - Limits enforced automatically
4. **SMILES validation** - Always validates before prediction
5. **PowerShell testing** - Use `test_api.ps1` script

---

## 🐛 **Troubleshooting**

### Backend not starting?

```powershell
cd backend
python app_enhanced.py
```

### Rate limit hit?

Wait 60 seconds or check status:

```powershell
Invoke-RestMethod http://localhost:5000/api/rate-limit/status
```

### Need help?

Check `ENHANCED_FEATURES_GUIDE.md` for detailed docs

---

**Last Updated**: Dec 4, 2025 00:21 IST  
**Status**: ✅ All features operational
