# 🚀 Deployment Guide for Render.com

## Overview

This guide will help you deploy MedToXAi platform on Render with both backend (Flask API) and frontend (React SPA).

## Prerequisites

- GitHub account with this repository
- Render account (free tier works)
- Groq API key
- Supabase account (optional but recommended)

## Step 1: Prepare Your Repository

1. **Push to GitHub** (if not already done):

```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/GauravPatil2515/medtox-scan-ai.git
git push -u origin main
```

1. **Ensure all deployment files are present**:

- ✅ `render.yaml` (root directory)
- ✅ `backend/requirements.txt` (with gunicorn)
- ✅ `backend/gunicorn.conf.py`
- ✅ `backend/Procfile`
- ✅ `backend/runtime.txt`
- ✅ `frontend/.env.production`

## Step 2: Deploy Backend on Render

### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New" → "Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Set environment variables in Render dashboard:
   - `GROQ_API_KEY`: Your Groq API key
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Your Supabase anonymous key
6. Click **"Apply"**

### Option B: Manual Setup

1. Go to Render Dashboard
2. Click **"New" → "Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `medtoxai-backend`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`
   - **Plan**: Free

5. **Add Environment Variables**:

```
GROQ_API_KEY=your-groq-api-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=https://medtoxai-frontend.onrender.com
AI_MODEL=llama-3.3-70b-versatile
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1024
PYTHON_VERSION=3.11.0
```

1. Click **"Create Web Service"**

## Step 3: Deploy Frontend on Render

### Option A: Using render.yaml (Already included)

The frontend will be deployed automatically with the blueprint.

### Option B: Manual Setup

1. Click **"New" → "Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `medtoxai-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Plan**: Free

4. **Add Environment Variable**:

```
REACT_APP_API_URL=https://medtoxai-backend.onrender.com
```

1. Click **"Create Static Site"**

## Step 4: Update CORS Settings

After backend is deployed:

1. Note your backend URL (e.g., `https://medtoxai-backend.onrender.com`)
2. Update `CORS_ORIGINS` in backend environment variables:

```
CORS_ORIGINS=https://your-frontend-url.onrender.com,https://medtoxai-frontend.onrender.com
```

## Step 5: Configure Custom Domain (Optional)

### Backend Domain

1. Go to backend service settings
2. Click **"Custom Domains"**
3. Add: `api.medtoxai.com`
4. Follow DNS configuration instructions

### Frontend Domain

1. Go to frontend service settings
2. Click **"Custom Domains"**
3. Add: `www.medtoxai.com` or `medtoxai.com`
4. Follow DNS configuration instructions

## Step 6: Setup Database (Supabase)

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Create new project or use existing
3. Go to **SQL Editor**
4. Copy contents from `database/schema.sql`
5. Execute the SQL to create tables
6. Copy project URL and anon key to Render environment variables

## Step 7: Test Your Deployment

1. **Test Backend**:

```bash
curl https://medtoxai-backend.onrender.com/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T...",
  "predictor_loaded": true
}
```

1. **Test Frontend**:

- Open `https://medtoxai-frontend.onrender.com`
- Navigate to Dashboard
- Try a prediction with SMILES: `CCO`
- Check if API calls work

1. **Test Prediction API**:

```bash
curl -X POST https://medtoxai-backend.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles": "CCO", "molecule_name": "Ethanol"}'
```

## Troubleshooting

### Backend Issues

**Problem**: Models not loading

- **Solution**: Check if `best_optimized_models.pkl` is in `backend/models/` directory
- Ensure git LFS is configured for large files

**Problem**: 503 Service Unavailable

- **Solution**: Check Render logs for errors
- Increase worker timeout in `gunicorn.conf.py`

**Problem**: Database connection failed

- **Solution**: Verify Supabase credentials
- Check if database tables are created

### Frontend Issues

**Problem**: API calls failing (CORS errors)

- **Solution**: Add frontend URL to backend `CORS_ORIGINS`
- Verify `REACT_APP_API_URL` is correct

**Problem**: Blank page after deployment

- **Solution**: Check browser console for errors
- Verify build completed successfully
- Check React Router configuration

**Problem**: 404 on refresh

- **Solution**: Already configured in `render.yaml` with rewrite rules

## Performance Optimization

### Free Tier Limitations

- **Sleep after 15min inactivity**: First request will be slow
- **750 hours/month limit**: Enough for moderate usage
- **512MB RAM**: Sufficient for the ML models

### Recommendations

1. **Upgrade to Starter ($7/month)** for:
   - No sleep
   - 1GB RAM
   - Better performance

2. **Use CDN** for faster frontend delivery:
   - Cloudflare (free)
   - Render's built-in CDN

3. **Optimize models**:
   - Consider model compression
   - Use caching for frequent predictions

## Monitoring

### Render Dashboard

- View logs in real-time
- Monitor CPU/RAM usage
- Track request metrics

### Setup Alerts

1. Go to service settings
2. Enable **"Notification Settings"**
3. Add email for deploy notifications

## Updating Deployment

### Auto-Deploy (Recommended)

- Push to `main` branch
- Render will automatically rebuild and deploy

### Manual Deploy

1. Go to service in Render dashboard
2. Click **"Manual Deploy"**
3. Select branch
4. Click **"Deploy"**

## Environment Variables Reference

### Backend (.env)

```properties
GROQ_API_KEY=your_groq_api_key_here
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=https://medtoxai-frontend.onrender.com
AI_MODEL=llama-3.3-70b-versatile
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1024
```

### Frontend (.env.production)

```properties
REACT_APP_API_URL=https://medtoxai-backend.onrender.com
REACT_APP_ENV=production
GENERATE_SOURCEMAP=false
```

## Cost Estimate

### Free Tier (Both Services)

- **Cost**: $0/month
- **Features**: 750 hours, sleep after 15min
- **Best for**: Development, testing, portfolio

### Paid Tier

- **Backend Starter**: $7/month
- **Frontend**: Free (static site)
- **Total**: $7/month
- **Best for**: Production use

## Security Checklist

- ✅ Environment variables are secret (not in code)
- ✅ CORS properly configured
- ✅ HTTPS enabled (automatic on Render)
- ✅ API keys secured in Render dashboard
- ✅ Database credentials protected
- ✅ Input validation enabled
- ✅ Rate limiting (add if needed)

## Support

**Issues with deployment?**

- Check Render logs first
- Review this guide
- Check [Render Documentation](https://render.com/docs)
- Open issue on GitHub

## Success! 🎉

Your MedToXAi platform is now live!

**Share your deployment:**

- Backend API: `https://medtoxai-backend.onrender.com`
- Frontend App: `https://medtoxai-frontend.onrender.com`

**Next Steps:**

1. Add custom domain
2. Setup monitoring
3. Add analytics
4. Share with users!
