# Additional Deployment Options - HygiaAI

Complete guide covering all deployment alternatives beyond the standard Railway/Vercel setup.

---

## 📋 Table of Contents

1. [Frontend Deployment Alternatives](#frontend-deployment-alternatives)
2. [Backend Deployment Alternatives](#backend-deployment-alternatives)
3. [Database Deployment Alternatives](#database-deployment-alternatives)
4. [Full-Stack Deployment Platforms](#full-stack-deployment-platforms)
5. [Container Orchestration](#container-orchestration)
6. [Self-Hosting Options](#self-hosting-options)
7. [Comparison Matrix](#comparison-matrix)

---

## 🎨 Frontend Deployment Alternatives

### Option 1: Netlify

**Best for:** Static sites, CI/CD integration, edge functions

**Setup:**

1. **Via Dashboard:**
   ```bash
   # Push code to GitHub first
   git push origin main
   ```
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect GitHub repository
   - Configure:
     - **Base directory:** `frontend`
     - **Build command:** `npm run build`
     - **Publish directory:** `frontend/dist`
   - Add environment variables:
     ```
     VITE_API_BASE_URL=https://your-backend.railway.app
     ```

2. **Via CLI:**
   ```bash
   npm install -g netlify-cli
   cd frontend
   netlify login
   netlify init
   netlify deploy --prod
   ```

**Pros:**
- ✅ Free tier with generous limits
- ✅ Automatic HTTPS
- ✅ Edge functions support
- ✅ Form handling
- ✅ Split testing

**Cons:**
- ❌ Less optimized for React than Vercel
- ❌ Build times can be slower

---

### Option 2: Cloudflare Pages

**Best for:** Global CDN, edge computing, free tier

**Setup:**

1. **Via Dashboard:**
   - Go to [Cloudflare Pages](https://pages.cloudflare.com)
   - Connect GitHub repository
   - Configure:
     - **Framework preset:** Vite
     - **Build command:** `npm run build`
     - **Build output directory:** `dist`
     - **Root directory:** `frontend`
   - Add environment variables in dashboard

2. **Via Wrangler CLI:**
   ```bash
   npm install -g wrangler
   cd frontend
   wrangler pages project create hygiaai-frontend
   wrangler pages deploy dist
   ```

**Pros:**
- ✅ Unlimited bandwidth (free tier)
- ✅ Global edge network
- ✅ DDoS protection included
- ✅ Workers integration
- ✅ Very fast CDN

**Cons:**
- ❌ Less developer-friendly than Vercel
- ❌ Fewer integrations

---

### Option 3: AWS Amplify

**Best for:** AWS ecosystem integration, CI/CD

**Setup:**

1. **Via Console:**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
   - Click "New app" → "Host web app"
   - Connect GitHub repository
   - Configure:
     - **App name:** `hygiaai-frontend`
     - **Branch:** `main`
     - **Build settings:** Auto-detect or use:
       ```yaml
       version: 1
       frontend:
         phases:
           preBuild:
             commands:
               - cd frontend
               - npm install
           build:
             commands:
               - npm run build
         artifacts:
           baseDirectory: frontend/dist
           files:
             - '**/*'
         cache:
           paths:
             - frontend/node_modules/**/*
       ```
   - Add environment variables

2. **Via CLI:**
   ```bash
   npm install -g @aws-amplify/cli
   amplify init
   amplify add hosting
   amplify publish
   ```

**Pros:**
- ✅ Full AWS integration
- ✅ Custom domains easy
- ✅ CI/CD built-in
- ✅ Preview deployments

**Cons:**
- ❌ More complex setup
- ❌ AWS account required
- ❌ Can be expensive

---

### Option 4: GitHub Pages

**Best for:** Free static hosting, simple projects

**Setup:**

1. **Configure GitHub Actions:**
   Create `.github/workflows/deploy.yml`:
   ```yaml
   name: Deploy to GitHub Pages
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-node@v3
           with:
             node-version: '20'
         - run: |
             cd frontend
             npm install
             npm run build
         - uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./frontend/dist
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: GitHub Actions

**Pros:**
- ✅ Completely free
- ✅ Integrated with GitHub
- ✅ Custom domains supported

**Cons:**
- ❌ No server-side features
- ❌ Requires GitHub Actions setup
- ❌ Slower than CDN

---

### Option 5: Firebase Hosting

**Best for:** Google ecosystem, real-time features

**Setup:**

1. **Install Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   firebase login
   ```

2. **Initialize Firebase:**
   ```bash
   cd frontend
   firebase init hosting
   # Select: Use existing project or create new
   # Public directory: dist
   # Single-page app: Yes
   # Overwrite index.html: No
   ```

3. **Configure `firebase.json`:**
   ```json
   {
     "hosting": {
       "public": "dist",
       "ignore": [
         "firebase.json",
         "**/.*",
         "**/node_modules/**"
       ],
       "rewrites": [
         {
           "source": "**",
           "destination": "/index.html"
         }
       ]
     }
   }
   ```

4. **Deploy:**
   ```bash
   npm run build
   firebase deploy --only hosting
   ```

**Pros:**
- ✅ Free tier available
- ✅ Fast CDN
- ✅ Easy custom domains
- ✅ Integrates with Firebase services

**Cons:**
- ❌ Google account required
- ❌ Less flexible than Vercel

---

### Option 6: Surge.sh

**Best for:** Quick deployments, CLI-based

**Setup:**

```bash
npm install -g surge
cd frontend
npm run build
surge dist/ your-app-name.surge.sh
```

**Pros:**
- ✅ Very simple
- ✅ Free tier
- ✅ Fast deployment

**Cons:**
- ❌ Basic features only
- ❌ No CI/CD integration

---

## ⚙️ Backend Deployment Alternatives

### Option 1: AWS Lambda + API Gateway

**Best for:** Serverless, pay-per-use, auto-scaling

**Setup:**

1. **Install Serverless Framework:**
   ```bash
   npm install -g serverless
   npm install --save-dev serverless-wsgi serverless-python-requirements
   ```

2. **Create `serverless.yml`:**
   ```yaml
   service: hygiaai-backend
   
   provider:
     name: aws
     runtime: python3.11
     region: us-east-1
     environment:
       DEEPGRAM_API_KEY: ${env:DEEPGRAM_API_KEY}
       QDRANT_HOST: ${env:QDRANT_HOST}
       QDRANT_API_KEY: ${env:QDRANT_API_KEY}
   
   functions:
     api:
       handler: wsgi.handler
       events:
         - http:
             path: /{proxy+}
             method: ANY
             cors: true
         - http:
             path: /
             method: ANY
             cors: true
   
   plugins:
     - serverless-wsgi
     - serverless-python-requirements
   
   custom:
     wsgi:
       app: src.api.main:app
     pythonRequirements:
       dockerizePip: non-linux
   ```

3. **Deploy:**
   ```bash
   serverless deploy
   ```

**Pros:**
- ✅ Pay only for usage
- ✅ Auto-scaling
- ✅ No server management
- ✅ High availability

**Cons:**
- ❌ Cold starts
- ❌ 15-minute timeout limit
- ❌ More complex setup
- ❌ Can be expensive at scale

---

### Option 2: Google Cloud Run

**Best for:** Container-based, auto-scaling, pay-per-use

**Setup:**

1. **Build and push Docker image:**
   ```bash
   # Set project
   gcloud config set project YOUR_PROJECT_ID
   
   # Build image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/hygiaai-backend
   
   # Deploy
   gcloud run deploy hygiaai-backend \
     --image gcr.io/YOUR_PROJECT_ID/hygiaai-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DEEPGRAM_API_KEY=your_key,QDRANT_HOST=your_host
   ```

2. **Or use Cloud Build:**
   Create `cloudbuild.yaml`:
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/hygiaai-backend', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/hygiaai-backend']
     - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
       entrypoint: gcloud
       args:
         - 'run'
         - 'deploy'
         - 'hygiaai-backend'
         - '--image'
         - 'gcr.io/$PROJECT_ID/hygiaai-backend'
         - '--region'
         - 'us-central1'
         - '--platform'
         - 'managed'
   ```

**Pros:**
- ✅ Pay only for requests
- ✅ Auto-scaling to zero
- ✅ Container-based
- ✅ Generous free tier

**Cons:**
- ❌ Cold starts
- ❌ Google Cloud account required
- ❌ More complex than Railway

---

### Option 3: Azure App Service

**Best for:** Microsoft ecosystem, enterprise features

**Setup:**

1. **Install Azure CLI:**
   ```bash
   # Windows
   winget install -e --id Microsoft.AzureCLI
   
   # Mac/Linux
   brew install azure-cli
   ```

2. **Create and deploy:**
   ```bash
   az login
   az group create --name hygiaai-rg --location eastus
   az appservice plan create --name hygiaai-plan --resource-group hygiaai-rg --sku B1 --is-linux
   az webapp create --resource-group hygiaai-rg --plan hygiaai-plan --name hygiaai-backend --runtime "PYTHON:3.11"
   
   # Configure environment variables
   az webapp config appsettings set --resource-group hygiaai-rg --name hygiaai-backend --settings \
     DEEPGRAM_API_KEY=your_key \
     QDRANT_HOST=your_host
   
   # Deploy from local Git
   az webapp up --resource-group hygiaai-rg --name hygiaai-backend --runtime "PYTHON:3.11"
   ```

**Pros:**
- ✅ Enterprise features
- ✅ Good integration with Azure services
- ✅ Custom domains easy

**Cons:**
- ❌ More expensive
- ❌ Complex setup
- ❌ Azure account required

---

### Option 3: DigitalOcean App Platform

**Best for:** Simple pricing, Docker support

**Setup:**

1. **Via Dashboard:**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Connect GitHub repository
   - Configure:
     - **Type:** Web Service
     - **Source:** GitHub repo
     - **Dockerfile:** Use existing Dockerfile
     - **Port:** 8000
   - Add environment variables
   - Select plan ($5/month minimum)

2. **Via doctl CLI:**
   ```bash
   doctl apps create --spec app.yaml
   ```

**Pros:**
- ✅ Simple pricing
- ✅ Good documentation
- ✅ Docker support

**Cons:**
- ❌ Paid only (no free tier)
- ❌ Less features than AWS/GCP

---

### Option 4: Heroku

**Best for:** Simple deployment, add-ons ecosystem

**Note:** Heroku removed free tier, but still available for paid plans.

**Setup:**

1. **Install Heroku CLI:**
   ```bash
   # Windows
   winget install Heroku.CLI
   
   # Mac
   brew tap heroku/brew && brew install heroku
   ```

2. **Deploy:**
   ```bash
   heroku login
   heroku create hygiaai-backend
   heroku config:set DEEPGRAM_API_KEY=your_key
   heroku config:set QDRANT_HOST=your_host
   git push heroku main
   ```

3. **Create `Procfile`:**
   ```
   web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

**Pros:**
- ✅ Very simple deployment
- ✅ Great add-ons ecosystem
- ✅ Good documentation

**Cons:**
- ❌ No free tier anymore
- ❌ Can be expensive
- ❌ Dyno sleeping issues

---

### Option 5: Cloudflare Workers

**Best for:** Edge computing, low latency, serverless

**Note:** Requires adapting FastAPI to Cloudflare Workers format (using Workers for Python or converting to JavaScript).

**Setup:**

1. **Install Wrangler:**
   ```bash
   npm install -g wrangler
   ```

2. **Create `wrangler.toml`:**
   ```toml
   name = "hygiaai-backend"
   main = "src/worker.py"
   compatibility_date = "2024-01-01"
   
   [vars]
   DEEPGRAM_API_KEY = "your_key"
   QDRANT_HOST = "your_host"
   ```

**Pros:**
- ✅ Edge computing
- ✅ Very low latency
- ✅ Generous free tier
- ✅ DDoS protection

**Cons:**
- ❌ Requires code adaptation
- ❌ Python support is limited
- ❌ Different runtime environment

---

### Option 6: Back4App

**Best for:** Backend-as-a-Service, quick setup

**Setup:**

1. Go to [Back4App](https://www.back4app.com)
2. Create new app
3. Connect GitHub repository
4. Configure environment variables
5. Deploy

**Pros:**
- ✅ Simple setup
- ✅ Free tier available
- ✅ Good for prototypes

**Cons:**
- ❌ Less control
- ❌ Vendor lock-in

---

## 🗄️ Database Deployment Alternatives

### Option 1: AWS EC2/ECS with Qdrant

**Best for:** Full control, production workloads

**Setup:**

1. **EC2 Instance:**
   ```bash
   # Launch EC2 instance (Ubuntu 22.04)
   # SSH into instance
   ssh -i key.pem ubuntu@your-instance-ip
   
   # Install Docker
   sudo apt update
   sudo apt install docker.io -y
   sudo systemctl start docker
   sudo usermod -aG docker ubuntu
   
   # Run Qdrant
   docker run -d \
     -p 6333:6333 \
     -p 6334:6334 \
     -v qdrant_storage:/qdrant/storage \
     --name qdrant \
     qdrant/qdrant
   ```

2. **ECS Fargate:**
   ```bash
   # Create ECS cluster
   aws ecs create-cluster --cluster-name hygiaai-qdrant
   
   # Create task definition (task-definition.json)
   # Deploy using ECS console or CLI
   ```

**Pros:**
- ✅ Full control
- ✅ Scalable
- ✅ Production-ready

**Cons:**
- ❌ Requires AWS knowledge
- ❌ More expensive
- ❌ Manual management

---

### Option 2: Google Cloud Run with Qdrant

**Best for:** Serverless containers, auto-scaling

**Setup:**

```bash
# Build Qdrant image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/qdrant

# Deploy to Cloud Run
gcloud run deploy hygiaai-qdrant \
  --image qdrant/qdrant:latest \
  --platform managed \
  --region us-central1 \
  --port 6333 \
  --memory 2Gi \
  --cpu 2
```

**Pros:**
- ✅ Auto-scaling
- ✅ Pay-per-use
- ✅ Managed service

**Cons:**
- ❌ Cold starts possible
- ❌ GCP account required

---

### Option 3: DigitalOcean Droplet

**Best for:** Simple VPS, affordable pricing

**Setup:**

1. **Create Droplet:**
   - Go to DigitalOcean → Create Droplet
   - Choose Ubuntu 22.04
   - Select plan ($6/month minimum)
   - Add SSH key

2. **Install Qdrant:**
   ```bash
   ssh root@your-droplet-ip
   docker run -d \
     -p 6333:6333 \
     -p 6334:6334 \
     -v qdrant_storage:/qdrant/storage \
     --restart unless-stopped \
     qdrant/qdrant
   ```

**Pros:**
- ✅ Simple and affordable
- ✅ Full control
- ✅ Predictable pricing

**Cons:**
- ❌ Manual management
- ❌ No auto-scaling
- ❌ Need to handle backups

---

### Option 4: Linode

**Best for:** Alternative to DigitalOcean, competitive pricing

**Setup:** Similar to DigitalOcean Droplet

**Pros:**
- ✅ Competitive pricing
- ✅ Good performance
- ✅ Simple interface

**Cons:**
- ❌ Manual management
- ❌ Less features than AWS/GCP

---

### Option 5: Vultr

**Best for:** Global distribution, competitive pricing

**Setup:** Similar to DigitalOcean

**Pros:**
- ✅ Global locations
- ✅ Competitive pricing
- ✅ Good performance

**Cons:**
- ❌ Manual management
- ❌ Smaller ecosystem

---

## 🚀 Full-Stack Deployment Platforms

### Option 1: AWS Amplify (Full Stack)

**Best for:** Complete AWS integration

**Setup:**
- Frontend: AWS Amplify Hosting (see Frontend section)
- Backend: AWS Lambda + API Gateway (see Backend section)
- Database: AWS RDS or DynamoDB (or Qdrant on EC2)

**Pros:**
- ✅ Unified platform
- ✅ Good integration
- ✅ Enterprise features

**Cons:**
- ❌ Complex setup
- ❌ Can be expensive
- ❌ AWS knowledge required

---

### Option 2: Firebase (Full Stack)

**Best for:** Google ecosystem, real-time features

**Setup:**
- Frontend: Firebase Hosting (see Frontend section)
- Backend: Cloud Functions or Cloud Run
- Database: Firestore (or Qdrant on Cloud Run)

**Pros:**
- ✅ Unified platform
- ✅ Real-time features
- ✅ Good free tier

**Cons:**
- ❌ Vendor lock-in
- ❌ Less flexible

---

### Option 3: Supabase

**Best for:** Open-source Firebase alternative

**Setup:**

1. **Self-hosted:**
   ```bash
   git clone https://github.com/supabase/supabase
   cd supabase/docker
   cp .env.example .env
   docker-compose up -d
   ```

2. **Cloud:**
   - Go to [Supabase](https://supabase.com)
   - Create project
   - Use PostgreSQL (can adapt Qdrant separately)

**Pros:**
- ✅ Open-source
- ✅ Good free tier
- ✅ PostgreSQL included

**Cons:**
- ❌ Need to adapt for Qdrant
- ❌ Less mature than Firebase

---

### Option 4: DigitalOcean App Platform (Full Stack)

**Best for:** Simple full-stack deployment

**Setup:**
- Deploy frontend and backend as separate services
- Add Qdrant as third service (Docker)

**Pros:**
- ✅ Simple pricing
- ✅ Unified dashboard
- ✅ Good documentation

**Cons:**
- ❌ Paid only
- ❌ Less features than AWS/GCP

---

## 🐳 Container Orchestration

### Option 1: Kubernetes (GKE/EKS/AKS)

**Best for:** Production, scalability, microservices

**Setup:**

1. **Create `k8s/deployment.yaml`:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: hygiaai-backend
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: hygiaai-backend
     template:
       metadata:
         labels:
           app: hygiaai-backend
       spec:
         containers:
         - name: backend
           image: your-registry/hygiaai-backend:latest
           ports:
           - containerPort: 8000
           env:
           - name: DEEPGRAM_API_KEY
             valueFrom:
               secretKeyRef:
                 name: hygiaai-secrets
                 key: deepgram-key
   ```

2. **Deploy:**
   ```bash
   # GKE
   gcloud container clusters create hygiaai-cluster
   kubectl apply -f k8s/
   
   # EKS
   eksctl create cluster --name hygiaai-cluster
   kubectl apply -f k8s/
   
   # AKS
   az aks create --resource-group hygiaai-rg --name hygiaai-cluster
   kubectl apply -f k8s/
   ```

**Pros:**
- ✅ Highly scalable
- ✅ Production-ready
- ✅ Auto-scaling
- ✅ Self-healing

**Cons:**
- ❌ Complex setup
- ❌ Requires expertise
- ❌ More expensive

---

### Option 2: Docker Compose on VPS

**Best for:** Simple multi-container deployment

**Setup:**

1. **Create `docker-compose.prod.yml`:**
   ```yaml
   version: '3.8'
   
   services:
     backend:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
         - QDRANT_HOST=qdrant
       depends_on:
         - qdrant
     
     qdrant:
       image: qdrant/qdrant:latest
       ports:
         - "6333:6333"
       volumes:
         - qdrant_data:/qdrant/storage
   
   volumes:
     qdrant_data:
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Pros:**
- ✅ Simple
- ✅ Good for small deployments
- ✅ Easy to manage

**Cons:**
- ❌ No auto-scaling
- ❌ Single server
- ❌ Manual management

---

### Option 3: Portainer

**Best for:** Docker GUI management

**Setup:**

```bash
docker volume create portainer_data
docker run -d -p 9000:9000 --name=portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce
```

Then use Portainer UI to deploy containers.

**Pros:**
- ✅ GUI for Docker
- ✅ Easy management
- ✅ Good for teams

**Cons:**
- ❌ Additional service to manage
- ❌ Security considerations

---

## 🏠 Self-Hosting Options

### Option 1: Raspberry Pi

**Best for:** Local demos, low power, portable

**Setup:**

1. **Install Raspberry Pi OS**
2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

**Pros:**
- ✅ Portable
- ✅ Low power
- ✅ Good for demos

**Cons:**
- ❌ Limited performance
- ❌ ARM architecture considerations

---

### Option 2: Home Server/NAS

**Best for:** Personal use, data control

**Setup:** Similar to VPS, but on local hardware

**Pros:**
- ✅ Full control
- ✅ No cloud costs
- ✅ Data privacy

**Cons:**
- ❌ Requires hardware
- ❌ Network setup needed
- ❌ Maintenance required

---

## 📊 Comparison Matrix

| Platform | Type | Free Tier | Cost (Paid) | Difficulty | Best For |
|----------|------|-----------|-------------|------------|----------|
| **Vercel** | Frontend | ✅ Yes | $20/mo | ⭐ Easy | React apps |
| **Netlify** | Frontend | ✅ Yes | $19/mo | ⭐ Easy | Static sites |
| **Cloudflare Pages** | Frontend | ✅ Yes | Free | ⭐ Easy | Global CDN |
| **AWS Amplify** | Frontend | ✅ Yes | Pay-per-use | ⭐⭐ Medium | AWS ecosystem |
| **Railway** | Backend | ✅ $5 credit | $5+/mo | ⭐ Easy | Simple deployment |
| **Render** | Backend | ✅ 750hrs | $7+/mo | ⭐ Easy | Alternative to Railway |
| **Fly.io** | Backend | ✅ 3 VMs | $1.94+/mo | ⭐⭐ Medium | Global distribution |
| **AWS Lambda** | Backend | ✅ 1M requests | Pay-per-use | ⭐⭐⭐ Hard | Serverless |
| **Cloud Run** | Backend | ✅ 2M requests | Pay-per-use | ⭐⭐ Medium | Containers |
| **Qdrant Cloud** | Database | ✅ 1GB | $25+/mo | ⭐ Easy | Managed service |
| **DigitalOcean** | VPS | ❌ No | $6+/mo | ⭐⭐ Medium | Simple VPS |
| **Kubernetes** | Orchestration | ❌ No | Varies | ⭐⭐⭐⭐ Hard | Production scale |

---

## 🎯 Recommendations by Use Case

### For Quick Demo:
1. **Frontend:** Vercel or Netlify
2. **Backend:** Railway or Render
3. **Database:** Qdrant Cloud or Railway Docker

### For Production:
1. **Frontend:** Cloudflare Pages or Vercel
2. **Backend:** AWS Lambda or Cloud Run
3. **Database:** Qdrant Cloud or self-hosted on VPS

### For Cost Optimization:
1. **Frontend:** Cloudflare Pages (unlimited bandwidth)
2. **Backend:** Fly.io or Render free tier
3. **Database:** Railway Docker or self-hosted

### For Enterprise:
1. **Frontend:** AWS Amplify or Azure Static Web Apps
2. **Backend:** Kubernetes (GKE/EKS/AKS)
3. **Database:** Self-hosted Qdrant on managed infrastructure

### For Offline/Rural:
1. **All:** Self-hosted on local server/VPS
2. **Database:** Local Qdrant Docker container
3. **See:** `OFFLINE_RURAL_DEMO_GUIDE.md`

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Netlify Documentation](https://docs.netlify.com)
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages)
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [Docker Compose Docs](https://docs.docker.com/compose)

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0



