# DeNovo Deployment Guide

This guide covers deploying the DeNovo Drug Discovery Platform to various cloud platforms.

---

## 🚀 Option 1: Deploy to Render (Recommended - Free)

### Step 1: Push to GitHub

Ensure your code is pushed to GitHub:

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 3: Deploy Backend

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `denovo-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**:

     ```
     pip install --upgrade pip && pip install torch==2.0.1+cpu torchvision==0.15.2+cpu --index-url https://download.pytorch.org/whl/cpu && pip install torch-geometric && pip install -r requirements.txt
     ```

   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --timeout 300`
4. Add Environment Variable:
   - `GROQ_API_KEY` = your_groq_api_key (get from [console.groq.com](https://console.groq.com))
5. Click **Create Web Service**

### Step 4: Deploy Frontend (Optional)

1. Click **New** → **Static Site**
2. Configure:
   - **Name**: `denovo-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
3. Add Environment Variable:
   - `REACT_APP_API_URL` = `https://denovo-api.onrender.com`

### Step 5: Verify

- Backend: `https://denovo-api.onrender.com/api/health`
- Frontend: `https://denovo-frontend.onrender.com`

---

## 🐳 Option 2: Deploy with Docker

### Local Docker Run

```bash
# Build the image
docker build -t denovo .

# Run with environment variables
docker run -p 5000:5000 \
  -e GROQ_API_KEY=your_key_here \
  denovo
```

### Deploy to Any Docker Host

```bash
# Tag for registry
docker tag denovo your-registry/denovo:latest

# Push to registry
docker push your-registry/denovo:latest
```

---

## ☁️ Option 3: Deploy to Railway

### Quick Deploy

1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repository
4. Railway auto-detects Python and deploys
5. Add `GROQ_API_KEY` in Variables

---

## ☁️ Option 4: Deploy to Hugging Face Spaces

### Create Gradio Interface

1. Create a file `app_gradio.py`:

```python
import gradio as gr
from backend.models.unified_predictor import UnifiedADMETPredictor

predictor = UnifiedADMETPredictor()

def predict(smiles):
    result = predictor.predict(smiles)
    return result.get('summary', {}).get('overall_assessment', 'Error')

demo = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(label="SMILES"),
    outputs=gr.Textbox(label="Prediction"),
    title="DeNovo Drug Discovery"
)

demo.launch()
```

1. Push to Hugging Face Spaces

---

## 🔑 Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for AI chat) | Get from [console.groq.com](https://console.groq.com) |
| `FLASK_ENV` | No | `production` for deployment |
| `CORS_ORIGINS` | No | Allowed origins for CORS |

---

## ⚠️ Important Notes

### Free Tier Limitations (Render)

- **Cold starts**: First request may take 30-60 seconds
- **Memory**: 512MB limit (sufficient for 1 worker)
- **Spin down**: Service sleeps after 15 min inactivity

### Model Loading

- Models are ~10MB each and loaded on startup
- First prediction takes longer (model loading)
- Subsequent predictions are fast (~50-200ms)

### Scaling Recommendations

For production with higher traffic:

1. Upgrade to paid plan
2. Increase workers: `--workers 4`
3. Add Redis caching
4. Use model serving (TorchServe)

---

## 🧪 Testing Deployment

After deployment, test with:

```bash
# Health Check
curl https://your-app.onrender.com/api/health

# Prediction Test
curl -X POST https://your-app.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles": "CCO"}'
```

Expected response:

```json
{
  "success": true,
  "predictions": {
    "toxicity": {"assessment": "VERY LOW TOXICITY ✅"}
  }
}
```

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails on PyTorch | Use CPU-only PyTorch with explicit `--index-url` |
| Memory error | Reduce workers to 1, add `--preload` flag |
| Timeout on first request | Normal cold start behavior, retry after 60s |
| GROQ API not working | Verify API key is set in environment variables |

---

## 🔗 Quick Links

- **Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)
- **Groq Console**: [console.groq.com](https://console.groq.com)
- **GitHub Repository**: [Your Repo](https://github.com/GauravPatil2515/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction)
