# 🧬 MedToXAi Enhanced Backend

## 📊 Features

### Modern Web Interface

- **Professional Dashboard** - Inspired by modern marketplace interfaces
- **Real-time Predictions** - Single molecule and batch processing
- **Interactive Results** - Detailed toxicity analysis with confidence levels
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Dark/Light Theme** - Automatic theme detection (future enhancement)

### Core Functionality

- **12 Toxicity Endpoints** - Nuclear Receptor and Stress Response pathways
- **SMILES Input** - Standard molecular notation support
- **Batch Processing** - Upload CSV files with multiple molecules
- **Result History** - Track all predictions with filtering and search
- **Export Options** - Download results as CSV files
- **Real-time Stats** - System performance and usage metrics

### Technical Features

- **Flask Backend** - Python web framework with REST API
- **Model Integration** - Connects to existing DrugTox-AI models
- **Mock Mode** - Works without RDKit for testing
- **File Upload** - Drag-and-drop interface for batch files
- **Progress Tracking** - Real-time progress indicators
- **Error Handling** - Comprehensive error messages and recovery

## 🚀 Quick Start

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials
# Required: GROQ_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY
notepad .env  # Windows
nano .env     # Linux/Mac

# Validate environment setup
python validate_env.py
```

### 2. Installation

#### Windows (Recommended)
```bash
# Double-click run_dashboard.bat
# or from command line:
run_dashboard.bat
```

#### Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python app.py
```

### Access Dashboard

Open your browser to: [http://localhost:5000](http://localhost:5000)

## 📁 Dashboard Structure

```text
dashboard/
├── app.py                 # Main Flask application
├── models.py             # Model integration and prediction logic
├── requirements.txt      # Python dependencies
├── run_dashboard.bat     # Windows launcher script
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── dashboard.html   # Main dashboard page
│   ├── predict.html     # Prediction interface
│   └── results.html     # Results history
├── static/              # Static assets
│   ├── css/
│   │   └── style.css    # Modern dashboard styling
│   └── js/
│       └── main.js      # Dashboard JavaScript
└── uploads/             # Temporary file uploads (auto-created)
```

## 🎯 Dashboard Pages

### 1. Main Dashboard (`/`)

- **System Statistics** - Total predictions, success rate, response time
- **Quick Prediction** - Single molecule input form
- **Recent Results** - Last 5 predictions with details
- **System Status** - Model status and health indicators
- **Endpoint Overview** - Available toxicity pathways

### 2. Prediction Interface (`/predict`)

- **Single Prediction** - Individual molecule analysis
- **Batch Processing** - CSV/TXT file upload (up to 100 molecules)
- **Example Molecules** - Pre-loaded SMILES for testing
- **Endpoint Information** - Details about each toxicity pathway
- **Real-time Results** - Immediate prediction display

### 3. Results History (`/results`)

- **Prediction History** - All previous results with pagination
- **Advanced Filtering** - Search by name, risk level, date range
- **Detailed View** - Expandable prediction details
- **Export Options** - Individual or bulk result downloads
- **Result Management** - Copy SMILES, view summaries

## 🔗 API Endpoints

### Core Prediction API

```bash
# Single molecule prediction
POST /api/predict
{
    "name": "Aspirin",
    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
}

# Batch file upload
POST /api/batch_predict
Form-data: file=molecules.csv

# System statistics
GET /api/stats

# Endpoint statistics
GET /api/endpoint_stats

# Export results
GET /api/export_results
```

### API Response Format

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
            }
        },
        "timestamp": "2025-09-25T20:54:00",
        "prediction_id": "abc123"
    }
}
```

## 🎨 UI Components

### Design System

- **Color Scheme** - Professional green/blue palette
- **Typography** - Inter font family for readability
- **Icons** - Font Awesome icons throughout
- **Animations** - Smooth transitions and loading states
- **Responsive** - Mobile-first responsive design

### Interactive Elements

- **Stat Cards** - Animated counters with trend indicators
- **Progress Bars** - Visual probability representations
- **Loading States** - Spinners and progress indicators
- **Notifications** - Toast messages for user feedback
- **Modal Dialogs** - Filtering and confirmation dialogs

## 🔧 Configuration

### Environment Variables (Optional)

```bash
FLASK_ENV=development        # or production
FLASK_DEBUG=True            # Enable debug mode
MAX_CONTENT_LENGTH=16MB     # File upload limit
UPLOAD_FOLDER=uploads       # Upload directory
```

### Model Configuration

- Models loaded from `../models/optimized/` or `../models/baseline_final/`
- Automatic fallback to mock predictions if models unavailable
- RDKit optional for molecular feature extraction

## 📊 Dashboard Screenshots

The dashboard features a modern, professional interface with:

- **Header Navigation** - Logo, menu items, system status
- **Statistics Grid** - Key performance metrics
- **Quick Actions** - Immediate prediction capability
- **Recent Activity** - Latest prediction results
- **Responsive Layout** - Adapts to all screen sizes

## 🎯 Use Cases

### Research Applications

- **Drug Discovery** - Screen new compounds for toxicity
- **Lead Optimization** - Compare toxicity profiles
- **Literature Validation** - Predict known compounds
- **Batch Screening** - Process multiple molecules efficiently

### Educational Use

- **Teaching Tool** - Demonstrate QSAR modeling
- **Student Projects** - Hands-on molecular toxicology
- **Interactive Learning** - Real-time prediction examples

### Production Use

- **API Integration** - REST endpoints for external systems
- **Batch Processing** - High-throughput screening
- **Result Management** - Track and export predictions
- **Performance Monitoring** - System statistics and health

## 🚀 Deployment Options

### Development Server

```bash
python app.py  # Flask development server
```

### Production Server

```bash
# Using Gunicorn (Linux/Mac)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Waitress (Windows)
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### Docker Deployment (Future)

```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🎉 Success Metrics

The dashboard provides a complete, production-ready web interface for DrugTox-AI with:

- ✅ **Professional UI** - Modern, responsive design
- ✅ **Full Functionality** - Single and batch predictions
- ✅ **Model Integration** - Connects to existing trained models
- ✅ **Result Management** - History, filtering, and export
- ✅ **API Ready** - REST endpoints for integration
- ✅ **Error Handling** - Robust error management
- ✅ **Documentation** - Complete setup and usage guides

Ready for immediate use in research, education, and production environments! 🧬

