# DeNovo Platform - Design Documentation

## 6. Design

### 6.1 UI/UX Design: Screens & Interface

#### **Design Philosophy**
DeNovo employs a modern, dark-themed scientific interface optimized for pharmaceutical researchers with a focus on:
- **Data-Centric Layout**: Molecular structures and predictions take center stage
- **Professional Aesthetic**: Clean design with scientific terminology
- **Responsive Design**: Seamless experience across all devices

#### **Key Screens**

**A. Landing Page**
- Hero section with SMILES input and immediate prediction capability
- Feature highlights (Multi-Model Prediction, Real-time Analysis, 6 ADMET Models)
- Gradient background (black to gray-950) with hover-animated cards

**B. Dashboard**
- Statistics overview (4 metric cards: Total Tests, Active Models, Batch Jobs, Model Accuracy)
- Quick prediction form with SMILES input and model selector
- Recent predictions timeline with status indicators
- System health monitoring panel

**C. Enhanced Predictions Page**
- Three-step workflow: Input → Model Selection → Results
- Multi-select model cards (Tox21, ClinTox, BBBP, Caco-2, Clearance, HLM CLint)
- Results display with:
  - Real-time 2D molecular structure (RDKit)
  - Molecular properties (MW, atoms, bonds, rings)
  - Expandable endpoint predictions with confidence scores
  - Export options (PDF, CSV)

**D. Batch Processing Interface**
- Drag-and-drop CSV/SDF file upload
- Model selection checkboxes
- Real-time progress bar with ETA
- Job history with download links and success/failure statistics

**E. AI Assistant (Chat)**
- Conversational interface with chat bubbles
- Suggested questions for common queries
- Context-aware responses using Groq LLaMA 3.3 70B
- Timestamp and message history

#### **Design System**

**Color Palette:**
- Background: #000000, #0a0a0a (gradient)
- Primary: #06b6d4 (cyan-500)
- Accent: #8b5cf6 (purple-500)
- Success: #10b981 | Warning: #f59e0b | Danger: #ef4444

**Typography:**
- Font: Inter (sans-serif)
- H1: 2.5rem/700, H2: 2rem/600, H3: 1.5rem/600
- Body: 1rem/400

**Components:**
- Buttons: Primary (gradient cyan→teal), Secondary (gray-800), Danger (red-600)
- Cards: Bordered with gradient accent, hover animations
- Inputs: Dark theme with cyan focus rings

### 6.2 Database Design: Schema & Relationships

#### **Entity Relationships**
- **Users** (1:N) → **Predictions**: One user creates many predictions
- **Predictions** (1:N) → **User_Feedback**: One prediction receives multiple feedback entries
- **Molecule_Library**: Independent reference table for known compounds

#### **Database Schema (PostgreSQL/Supabase)**

**Table 1: `predictions`**
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    smiles TEXT NOT NULL,
    molecule_name TEXT,
    endpoints JSONB NOT NULL,
    ai_analysis TEXT,
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT valid_smiles CHECK (length(smiles) > 0)
);

CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_smiles ON predictions(smiles);
```

**Sample Data:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "molecule_name": "Aspirin",
  "endpoints": {
    "tox21": {
      "NR-AR-LBD": {"prediction": 0, "probability": 0.92},
      "NR-AhR": {"prediction": 0, "probability": 0.88},
      "overall": "Non-Toxic"
    },
    "clintox": {
      "FDA_approved": {"prediction": 1, "probability": 0.89},
      "toxicity": {"prediction": 0, "probability": 0.91}
    }
  },
  "ai_analysis": "Aspirin shows low toxicity across...",
  "user_id": "anonymous",
  "created_at": "2025-12-16T10:30:00Z",
  "metadata": {
    "model_versions": {"tox21": "v1.2", "clintox": "v1.0"},
    "processing_time": 1.23
  }
}
```

---

**Table 2: `user_feedback`**
```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    user_id TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_accurate BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

**Table 3: `molecule_library`**
```sql
CREATE TABLE molecule_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    smiles TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT,
    known_properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_molecule_library_category ON molecule_library(category);
CREATE INDEX idx_molecule_library_smiles ON molecule_library(smiles);
```

**Sample Data:**
```json
{
  "name": "Aspirin",
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "category": "analgesic",
  "description": "Nonsteroidal anti-inflammatory drug",
  "known_properties": {
    "molecular_weight": 180.16,
    "melting_point": "135°C",
    "therapeutic_class": "NSAID"
  }
}
```

---

#### **6.2.3 Database Functions**

**Function: Get User Statistics**
```sql
CREATE OR REPLACE FUNCTION get_user_stats(user_id_param TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_predictions', COUNT(*),
        'toxic_predictions', COUNT(*) FILTER (
            WHERE endpoints->>'overall' = 'Toxic'
        ),
        'safe_predictions', COUNT(*) FILTER (
            WHERE endpoints->>'overall' = 'Safe'
        ),
        'last_prediction', MAX(created_at)
    ) INTO result
    FROM predictions
    WHERE user_id = user_id_param;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

---

### 6.3 API / Integration Design: Endpoints & Data Flow

#### **RESTful API Endpoints**

**Base URL:** `http://localhost:5000/api` (Development) | Production: `https://denovo-api.onrender.com/api`

**Core Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health & cache statistics |
| `GET` | `/config/status` | API configuration status |
| `GET` | `/models/status` | Model loading status |
| `POST` | `/predict` | Single molecule prediction |
| `POST` | `/batch/process` | Batch CSV/SDF processing |
| `GET` | `/batch/results/:job_id` | Retrieve batch results |
| `POST` | `/chat/ask` | AI assistant queries |
| `POST` | `/ai/analyze` | AI analysis of molecule |
| `GET` | `/database/predictions` | Prediction history |
| `GET` | `/database/molecules` | Molecule library |

**Example Request/Response:**

```json
POST /api/predict
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "models": ["tox21", "clintox"]
}

Response:properties": {
    "molecular_weight": 180.16,
    "num_atoms": 21,
    "num_bonds": 21,
    "num_rings": 2
  },
  "structure_image": "data:image/png;base64,iVBORw0KG...",
  "processing_time": 1.23
}
```

---

**2. Batch Processing**
```http
POST /api/batch/process
Content-Type: multipart/form-data

{
  "file": <CSV file with SMILES column>,
  "models": ["clintox", "bbbp"]
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "batch_20251216_103045",
  "total_molecules": 1250,
  "status": "processing",
  "estimated_time": 480
}
```

---
#### **Data Flow Architecture**

**System Flow:**
React Frontend (Port 3000) → Flask Backend (Port 5000) → [GIN Models | RDKit | Groq AI | Cache | Database]

**Prediction Pipeline:**
1. User submits SMILES → Frontend validation
2. POST /api/predict → Backend processing:
   - Cache check (1-hour TTL, 70% hit rate)
   - If miss: SMILES→Graph conversion → Parallel model inference (6 models)
   - RDKit generates 2D structure + properties
   - Results aggregation + confidence scores
   - Cache storage + optional database save
3. API returns JSON (predictions + molecular properties + structure image)
4. Frontend renders results with export options

**Batch Processing:**
CSV upload → File validation → Job creation → Background processing (10 molecules/batch) → Results storage → Download link generation

**AI Chat:**
User question → Context building (system prompt + domain knowledge) → Groq API (LLaMA 3.3 70B) → Response formatting → Chat display

#### **External Integrations**

- **Groq API**: AI assistant (LLaMA 3.3 70B) at console.groq.com
- **Supabase**: PostgreSQL database with real-time sync
- **RDKit**: Local library for molecular visualization and chemical descriptors

#### **Security & Performance**

**Security:**
- CORS configuration, API key protection (env variables), input validation, rate limiting ready

**Performance:**
- LRU cache (10,000 entries, 1-hour TTL, 70% hit rate)
- Pre-loaded models in memory
- Response times: <100ms (cached), <1s (new), 2-5s/molecule (batch)## Summary

**Technology Stack:** React.js + Tailwind CSS (Frontend) | Python Flask + PyTorch (Backend) | PostgreSQL/Supabase (Database) | Groq LLaMA 3.3 70B (AI) | RDKit (Visualization)

**Key Design Principles:** Professional dark-themed UI optimized for researchers | Scalable PostgreSQL schema with JSONB flexibility | RESTful API with 10+ endpoints | High-performance caching (70% hit rate) | Modular architecture for extensibility

---

*Document Version: 1.0 | December 16, 2025 | DeNovo Platform