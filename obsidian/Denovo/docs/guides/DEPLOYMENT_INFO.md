# Deployment Information

## Services Status (As of 2025-12-23)

### 1. Backend Server

- **URL**: [http://localhost:5000](http://localhost:5000)
- **Status**: ✅ Running
- **Models Loaded**:
  - Tox21 (Attention-GIN): 12 Endpoints
  - BBBP (Simplified-GIN): Blood-Brain Barrier Penetration
  - ClinTox (Simplified-GIN): FDA Approval, Clinical Toxicity
  - Clearance (Simplified-GIN): Intrinsic Clearance (Regression)
  - XGBoost: Fallback models
- **Command to Restart**: `python backend/app.py`

### 2. Frontend Application

- **URL**: [http://localhost:3000](http://localhost:3000)
- **Status**: ✅ Running
- **Command to Restart**: `cd frontend && npm start`

## Updates Implemented

- **New Models**: BBBP, ClinTox, Clearance integrated.
- **Unified Predictor**: Updated to handle multiple GIN models.
- **Frontend**: Enhanced predictions table for dynamic model support.
- **API Fix**: `/api/visualize/molecule` endpoint verified.
