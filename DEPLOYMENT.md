# Deploying RAG SaaS to Render.com

This guide provides step-by-step instructions for deploying the RAG SaaS application to Render.com.

## Prerequisites

1. A [Render.com](https://render.com) account
2. A [Groq](https://console.groq.com/) API key (free tier available)
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Architecture on Render

The application deploys as three services:

1. **PostgreSQL Database** - Managed database service
2. **Backend API** - Python/FastAPI web service
3. **Frontend** - Static site (React/Vite)

## Deployment Options

### Option 1: Blueprint Deployment (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your repository
5. Render will detect `render.yaml` and create all services
6. Set the required environment variables when prompted:
   - `GROQ_API_KEY`: Your Groq API key
   - `CORS_ORIGINS`: Your frontend URL (e.g., `https://rag-saas-frontend.onrender.com`)
   - `VITE_API_URL`: Your backend URL (e.g., `https://rag-saas-backend.onrender.com`)

### Option 2: Manual Deployment

#### Step 1: Create PostgreSQL Database

1. Go to Render Dashboard → **New** → **PostgreSQL**
2. Configure:
   - **Name**: `rag-saas-db`
   - **Database**: `ragsaas`
   - **User**: `ragsaas`
   - **Region**: Oregon (or your preferred region)
   - **Plan**: Free
3. Click **Create Database**
4. Copy the **Internal Database URL** for the next step

#### Step 2: Deploy Backend

1. Go to **New** → **Web Service**
2. Connect your repository
3. Configure:
   - **Name**: `rag-saas-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python -m app.startup && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. Add Environment Variables:
   ```
   DATABASE_URL = [Paste Internal Database URL from Step 1]
   JWT_SECRET_KEY = [Click "Generate" for a secure value]
   GROQ_API_KEY = [Your Groq API key]
   APP_ENV = production
   USE_LOCAL_EMBEDDINGS = true
   LLM_PROVIDER = groq
   CORS_ORIGINS = https://rag-saas-frontend.onrender.com
   LOG_LEVEL = INFO
   PYTHONUNBUFFERED = 1
   ```

5. Click **Create Web Service**

#### Step 3: Deploy Frontend

1. Go to **New** → **Static Site**
2. Connect your repository
3. Configure:
   - **Name**: `rag-saas-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `dist`

4. Add Environment Variable:
   ```
   VITE_API_URL = https://rag-saas-backend.onrender.com
   ```

5. Add Rewrite Rule:
   - Go to **Redirects/Rewrites**
   - Add: Source `/*` → Destination `/index.html` (Rewrite)

6. Click **Create Static Site**

## Environment Variables Reference

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-set from database service |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Generate a secure random string |
| `GROQ_API_KEY` | Groq API key for LLM | `gsk_xxxxxxxxxxxx` |
| `CORS_ORIGINS` | Allowed frontend origins | `https://rag-saas-frontend.onrender.com` |
| `APP_ENV` | Environment mode | `production` |

### Backend (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_LOCAL_EMBEDDINGS` | Use local sentence-transformers | `true` |
| `LLM_PROVIDER` | LLM provider (groq/openai) | `groq` |
| `OPENAI_API_KEY` | OpenAI key (if using OpenAI) | - |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_FILE_SIZE_MB` | Max upload size | `10` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://rag-saas-backend.onrender.com` |

## Post-Deployment Steps

### 1. Update CORS Origins

After deployment, update the backend's `CORS_ORIGINS` to include your actual frontend URL.

### 2. Test the Application

1. Visit your frontend URL
2. Register a new account
3. Upload a PDF document
4. Try asking questions about the document

### 3. Monitor Logs

Check service logs in Render dashboard for any errors:
- Backend: Click on service → **Logs**
- Check for database connection issues or API errors

## Troubleshooting

### Common Issues

#### 1. "Health check failed"
- Ensure the backend's health endpoint is accessible at `/health`
- Check if database connection is working
- Review startup logs for errors

#### 2. "CORS error"
- Update `CORS_ORIGINS` in backend to include your frontend URL
- Format: `https://your-frontend.onrender.com` (no trailing slash)

#### 3. "Database connection refused"
- Use the **Internal Database URL** (not external)
- Ensure database and backend are in the same region

#### 4. "Module not found" during build
- Check `requirements.txt` has all dependencies
- Ensure build command includes `pip install --upgrade pip`

#### 5. Frontend shows blank page
- Check browser console for errors
- Verify `VITE_API_URL` is set correctly
- Ensure rewrite rule is configured for SPA routing

#### 6. File uploads fail
- Check `MAX_FILE_SIZE_MB` limit
- Render free tier has limited disk space (ephemeral)

### Memory Issues on Free Tier

The free tier has 512MB RAM limit. If you see memory errors:

1. Reduce `FAISS_CACHE_SIZE` to `3`
2. Consider using OpenAI embeddings instead of local (requires API key)
3. Upgrade to a paid tier for production use

## Scaling for Production

For production deployments, consider:

1. **Upgrade Plans**: Use paid tiers for more RAM and persistent disks
2. **Database**: Upgrade PostgreSQL for better performance
3. **Caching**: Add Redis for session/query caching
4. **CDN**: Enable Render's CDN for the frontend
5. **Custom Domain**: Add your own domain name

## Cost Considerations

Render Free Tier includes:
- 750 hours/month of web services
- PostgreSQL with 1GB storage (90 days)
- Static sites are always free

For sustained use, consider the Starter plan (~$7/month per service).
