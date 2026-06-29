# DeNovo Quick Start Guide

Get the DeNovo AI drug discovery platform up and running in minutes.

## 🚀 5-Minute Setup

### 1. Prerequisites
- Python 3.10+
- Git
- (Optional) Docker for containerized deployment

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/GauravPatil2515/DeNovo.git
cd DeNovo-main

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key
Get a free API key from [Groq Console](https://console.groq.com) and set it:
```bash
# Linux/Mac
echo "GROQ_API_KEY=your_key_here" >> backend/.env
# Windows (PowerShell)
Add-Content -Path "backend\.env" -Value "GROQ_API_KEY=your_key_here"
```

### 4. Start the Service
```bash
cd backend
python app.py
```
API available at: http://localhost:5000

### 5. Test It Out
```bash
# Health check
curl http://localhost:5000/api/health

# Make a prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CC(=O)OC1=CC=CC=C1C(=O)O"}'
```

## 📦 Deployment Options

### Docker (Recommended for Production)
```bash
# Build image
docker build -t denovo .

# Run container
docker run -p 5000:5000 -e GROQ_API_KEY=your_key denovo
```

### Cloud Deployment (Render.com)
1. Fork the repository
2. Sign up at [render.com](https://render.com)
3. Create new Web Service → Connect your repo
4. Set `GROQ_API_KEY` in environment variables
5. Deploy! (Auto-detects `render.yaml`)

## 🧪 Quick Validation
Run the built-in test suite:
```bash
python validate_models.py               # Deep validation with known molecules
python scripts/validate_all_models.py   # Check model loading
python scripts/test_api.py              # Test endpoints
```

## 📚 Next Steps
- Explore the interactive API docs at http://localhost:5000/api/docs
- Try the frontend (if built): http://localhost:3000
- Run faithfulness experiments: `python experiments/run_faithful_eval.py`
- Read the research paper: `overleaf/main.tex`

## 💡 Tips
- First prediction may be slower (model loading)
- Use batch prediction for multiple molecules
- Check `backend/.env.example` for all configuration options
- Models are stored in `results/trained_models/`

## 🆘 Troubleshooting
- **Module not found**: Ensure virtual environment is activated
- **Port already in use**: Change port in `app.py` or stop conflicting service
- **Groq API errors**: Verify your API key is correct and has credits
- **Memory issues**: Reduce workers with `gunicorn -w 1` for low-memory environments

## 📞 Support
- Documentation: `docs/` folder
- Issues: GitHub Issues
- Email: gauravppaiml123@gst.sies.edu.in

---

*Ready to discover safer drugs? Start predicting molecular properties today!*