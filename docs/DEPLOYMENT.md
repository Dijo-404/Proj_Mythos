# Lendora AI - Deployment Guide

Complete guide for deploying Lendora AI to various platforms.

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Vercel Deployment](#vercel-deployment)
3. [GitHub Actions CI/CD](#github-actions-cicd)
4. [Environment Variables](#environment-variables)
5. [Production Checklist](#production-checklist)

---

## Docker Deployment

### Quick Start

```bash
# Build and run full stack
docker-compose up -d

# Or use production compose
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Build Individual Services

```bash
# Backend only
docker build -f Dockerfile.backend -t lendora-backend:latest .

# Frontend only
docker build -f Dockerfile.frontend -t lendora-frontend:latest .

# Full stack (single container)
docker build -f Dockerfile -t lendora-full:latest .
```

### Run Individual Containers

```bash
# Backend
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  -e SOLANA_NETWORK=mainnet-beta \
  -e HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY \
  lendora-backend:latest

# Frontend
docker run -d \
  -p 80:80 \
  lendora-frontend:latest
```

---

## Vercel Deployment

### Frontend Deployment

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy Frontend:**
   ```bash
   cd frontend/Dashboard
   vercel
   ```

3. **Set Environment Variables:**
   ```bash
   vercel env add VITE_API_URL
   vercel env add VITE_WS_URL
   ```

4. **Configure `vercel.json`:**
   - Update `your-backend-url.vercel.app` with your actual backend URL
   - Set up API proxy routes

### Backend Deployment (Serverless)

**IMPORTANT:** Vercel has a 250MB unzipped size limit for serverless functions. The full backend with AI dependencies (CrewAI, LangChain, etc.) exceeds this limit.

**Recommended Approach:**
- **Deploy frontend to Vercel** (works perfectly)
- **Deploy backend to Railway/Render** (supports full AI features)

**If deploying backend to Vercel (minimal mode only):**

1. **Deploy Backend:**
   ```bash
   vercel --prod --local-config vercel-backend.json
   ```

2. **Note:** 
   - Only basic API endpoints available (no AI features)
   - Heavy dependencies excluded via `.vercelignore`
   - Ollama cannot run on Vercel (serverless limitation)
   - Use external Ollama service or disable AI agents
   - External RPC provider must be configured (Helius)

3. **For full AI features, use Railway or Render instead:**
   ```bash
   # Railway (recommended)
   railway login
   railway init
   railway up
   
   # Or Render
   # Connect GitHub repo and select docker-compose.yml
   ```

---

## GitHub Actions CI/CD

### Setup

1. **Enable GitHub Actions** in your repository settings

2. **Set Secrets** (Settings > Secrets and variables > Actions):
   - `GITHUB_TOKEN` (automatically available)
   - Add any required API keys

3. **Workflow runs automatically** on push to main/master

### Manual Deployment

```bash
# Push to trigger deployment
git push origin main
```

### View Deployment Status

- Go to Actions tab in GitHub
- View workflow runs and logs

---

## Environment Variables

### Required for Backend

```env
PORT=8000
HOST=0.0.0.0
OLLAMA_BASE_URL=http://localhost:11434
SOLANA_NETWORK=mainnet-beta
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY
```

### Optional (Advanced Features)

```env
# Credit Oracle
CREDIT_ORACLE_URL=https://api.oracle.com
CREDIT_ORACLE_API_KEY=your_api_key
```

### Frontend

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Production Checklist

### Before Deployment

- [ ] Set all environment variables
- [ ] Configure CORS for your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Test all endpoints
- [ ] Verify WebSocket connections
- [ ] Test wallet connections
- [ ] Verify AI agent functionality
- [ ] Set up backup strategy

### Security

- [ ] Use strong API keys
- [ ] Enable HTTPS only
- [ ] Configure rate limiting
- [ ] Set up DDoS protection
- [ ] Review CORS settings
- [ ] Secure environment variables
- [ ] Enable security headers

### Performance

- [ ] Enable gzip compression
- [ ] Configure CDN for static assets
- [ ] Set up caching headers
- [ ] Optimize Docker images
- [ ] Configure resource limits
- [ ] Set up load balancing (if needed)

---

## Platform-Specific Notes

### Vercel

**Limitations:**
- **250MB unzipped size limit** for serverless functions (backend with AI dependencies exceeds this)
- No persistent storage (use external database)
- Ollama cannot run (use external service)
- WebSocket support is limited (consider alternatives)
- 10-second function timeout (too short for AI negotiations)

**Recommendations:**
- **Deploy frontend to Vercel** (works perfectly, no size issues)
- **Deploy backend to Railway, Render, or Fly.io** (supports full AI features)
- Use external Ollama service
- For minimal API (no AI), backend can work on Vercel with reduced dependencies

**Size Optimization:**
- Use `.vercelignore` to exclude large files
- Minimal `api/requirements.txt` excludes heavy AI packages
- Backend falls back to minimal mode if dependencies too large

### Railway

**Recommended for:**
- Full-stack deployment
- Persistent storage
- WebSocket support

**Deployment:**
```bash
railway login
railway init
railway up
```

### Render

**Recommended for:**
- Docker deployments
- Auto-scaling
- WebSocket support

**Deployment:**
- Connect GitHub repository
- Select docker-compose.yml
- Configure environment variables

### Fly.io

**Recommended for:**
- Global distribution
- Low latency
- Docker support

**Deployment:**
```bash
flyctl launch
flyctl deploy
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Check health
curl http://localhost:8000/health

# Verify environment variables
docker-compose exec backend env
```

### Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs frontend

# Verify build
docker-compose exec frontend ls -la /usr/share/nginx/html

# Check API connection
curl http://localhost/api/health
```

### WebSocket Issues

- Verify WebSocket URL is correct
- Check CORS settings
- Verify proxy configuration
- Test WebSocket connection directly

---

## Monitoring

### Health Checks

- Backend: `GET /health`
- Frontend: `GET /` (should return index.html)

### Logs

```bash
# Docker
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Metrics

- Monitor API response times
- Track WebSocket connections
- Monitor agent execution times
- Track error rates

---

## Support

For deployment issues, check:
- [GitHub Issues](https://github.com/your-repo/Lendora-AI/issues)
- [Documentation](./README.md)
- [Advanced Features](./ADVANCED_FEATURES.md)

