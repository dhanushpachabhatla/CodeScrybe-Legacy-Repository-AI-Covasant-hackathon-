# 🚀 GCP Deployment Guide – CodeScrybe

This document explains how to deploy both the **FastAPI backend** and **React frontend** of the CodeScrybe application to **Google Cloud Platform (GCP)** using **Docker + Cloud Build + Cloud Run**.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Initial GCP Setup](#initial-gcp-setup)
- [Backend Deployment (FastAPI)](#backend-deployment-fastapi)
- [Frontend Deployment (React)](#frontend-deployment-react)
- [Environment Variables & Security](#environment-variables--security)
- [Testing Your Deployment](#testing-your-deployment)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## ✅ Prerequisites

Before starting, ensure you have:

- **GCP Project** with billing enabled
- **gcloud CLI** installed and configured
- **Docker** installed locally
- **GitHub repository** with your CodeScrybe code
- **Neo4j Aura** instance (free tier available)
- **Google Gemini API** key

### Install & Configure gcloud CLI

```bash
# Install gcloud CLI (if not already installed)
# Follow: https://cloud.google.com/sdk/docs/install

# Login to your Google account
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Configure Docker authentication
gcloud auth configure-docker
```

## 🏗️ Project Structure

Your project should have the following structure:

```
CodeScrybe-Legacy-Repository-AI/
├── Server/                     # Backend API (FastAPI)
│   ├── backend/
│   │   ├── agents/
│   │   ├── database/
│   │   ├── app.py
│   │   └── pipeline.py
│   ├── venv410/
│   ├── .env                    # Local environment variables
│   ├── requirements.txt
│   └── README.md
├── Client/                     # Frontend (React.js)
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── Dockerfile              # Frontend Docker config
│   └── README.md
├── Dockerfile                  # Backend Docker config (in root)
├── .dockerignore
├── .gitignore
├── README.md
└── GCP_DEPLOYMENT.md           # This file
```

## 🔧 Initial GCP Setup

### 1. Enable Required Services

```bash
# Enable Cloud Run and Cloud Build APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Verify services are enabled
gcloud services list --enabled | grep -E "(run|cloudbuild|containerregistry)"
```

### 2. Set Environment Variables

```bash
# Replace with your actual GCP project ID
export PROJECT_ID="your-project-id"
export REGION="asia-south1"  # Choose your preferred region

# Verify project ID
echo $PROJECT_ID
```

### 3. Create .dockerignore (in root directory)

```dockerignore
# Backend ignore patterns
Server/venv410/
Server/.env
Server/__pycache__/
Server/**/__pycache__/
Server/**/*.pyc

# Frontend ignore patterns  
Client/node_modules/
Client/build/
Client/.env.local
Client/.env.development.local
Client/.env.test.local
Client/.env.production.local

# General ignore patterns
.git/
.gitignore
*.md
.DS_Store
.vscode/
*.log
```

## 🐳 Backend Deployment (FastAPI)

### Step 1: Prepare Environment Variables

Before deployment, gather your environment variables:

```bash
# Example values - replace with your actual values
NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your-password"
GEMINI_API_KEY="your-gemini-api-key"
```

### Step 2: Build and Deploy Backend (From Root Directory)

```bash
# Ensure you're in the root directory of your project
cd /path/to/CodeScrybe-Legacy-Repository-AI

# Build the Docker image using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-backend .

# Deploy to Cloud Run with environment variables
gcloud run deploy codescrybe-backend \
  --image gcr.io/$PROJECT_ID/codescrybe-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "NEO4J_URI=$NEO4J_URI,NEO4J_USERNAME=$NEO4J_USERNAME,NEO4J_PASSWORD=$NEO4J_PASSWORD,GEMINI_API_KEY=$GEMINI_API_KEY"
```

### Step 3: Get Backend URL

```bash
# Get the deployed backend URL
gcloud run services describe codescrybe-backend --region=$REGION --format="value(status.url)"
```

## 🎨 Frontend Deployment (React)

### Step 1: Navigate to Client Directory

```bash
# Change to the Client directory
cd Client
```

### Step 2: Update API Configuration

Before building, update your React app to use the deployed backend URL:

**Create/Update `Client/src/config.js`:**

```javascript
// src/config.js
const config = {
  // Use environment variable or fallback to deployed backend URL
  API_BASE_URL: process.env.REACT_APP_API_URL || 'https://codescrybe-backend-xxxxx-as.a.run.app',
  
  // Other configuration options
  APP_NAME: 'CodeScrybe',
  VERSION: '1.0.0'
};

export default config;
```

**Update your API calls to use the config:**

```javascript
// Example: In your API service files
import config from './config';

const API_BASE_URL = config.API_BASE_URL;

// Use API_BASE_URL for all API calls
const fetchRepositories = async () => {
  const response = await fetch(`${API_BASE_URL}/repositories`);
  return response.json();
};
```

### Step 3: Build and Deploy Frontend

```bash
# Ensure you're in the Client directory
pwd  # Should show .../CodeScrybe-Legacy-Repository-AI/Client

# Build the Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-client .

# Deploy to Cloud Run
gcloud run deploy codescrybe-client \
  --image gcr.io/$PROJECT_ID/codescrybe-client \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "REACT_APP_API_URL=https://codescrybe-backend-xxxxx-as.a.run.app"
```

### Step 4: Get Frontend URL

```bash
# Get the deployed frontend URL
gcloud run services describe codescrybe-client --region=$REGION --format="value(status.url)"
```

## 🔐 Environment Variables & Security

### Using Secret Manager (Recommended for Production)

```bash
# Create secrets in Secret Manager
gcloud secrets create neo4j-password --data-file=- <<< "your-neo4j-password"
gcloud secrets create gemini-api-key --data-file=- <<< "your-gemini-api-key"

# Deploy backend with secrets
gcloud run deploy codescrybe-backend \
  --image gcr.io/$PROJECT_ID/codescrybe-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "NEO4J_URI=$NEO4J_URI,NEO4J_USERNAME=$NEO4J_USERNAME" \
  --set-secrets "NEO4J_PASSWORD=neo4j-password:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

### CORS Configuration

Ensure your FastAPI backend allows requests from your frontend domain:

```python
# In Server/backend/app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://codescrybe-client-xxxxx-as.a.run.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing Your Deployment

### 1. Test Backend API

```bash
# Test health endpoint
curl https://codescrybe-backend-xxxxx-as.a.run.app/health

# Test API documentation
# Visit: https://codescrybe-backend-xxxxx-as.a.run.app/docs
```

### 2. Test Frontend Application

```bash
# Visit your frontend URL
# https://codescrybe-client-xxxxx-as.a.run.app
```

### 3. Test Full Integration

1. Open your frontend URL in a browser
2. Navigate to the dashboard
3. Try adding a repository
4. Verify the frontend can communicate with the backend

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Build Failures**

```bash
# Check build logs
gcloud builds list --limit=5

# Get detailed logs for a specific build
gcloud builds log BUILD_ID
```

**2. Service Not Starting**

```bash
# Check service logs
gcloud run services logs codescrybe-backend --region=$REGION --limit=50
gcloud run services logs codescrybe-client --region=$REGION --limit=50
```

**3. Connection Issues**

```bash
# Verify service is running
gcloud run services list --region=$REGION

# Check service configuration
gcloud run services describe codescrybe-backend --region=$REGION
```

**4. Environment Variables Not Working**

```bash
# Check if environment variables are set correctly
gcloud run services describe codescrybe-backend --region=$REGION --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

## 💰 Cost Optimization

### Resource Allocation

```bash
# Optimize resource allocation based on usage
gcloud run services update codescrybe-backend \
  --region=$REGION \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=1000 \
  --max-instances=10 \
  --min-instances=0
```

### Monitoring and Alerts

```bash
# Set up monitoring (optional)
gcloud logging sinks create codescrybe-logs \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/codescrybe_logs \
  --log-filter='resource.type="cloud_run_revision"'
```

## 📊 Final Deployment URLs

After successful deployment, you'll have:

| Component | URL Format | Purpose |
|-----------|------------|---------|
| Backend API | `https://codescrybe-backend-xxxxx-as.a.run.app` | FastAPI server with endpoints |
| Frontend UI | `https://codescrybe-client-xxxxx-as.a.run.app` | React web application |
| API Docs | `https://codescrybe-backend-xxxxx-as.a.run.app/docs` | Interactive API documentation |

## 📝 Quick Reference Commands

```bash
# Deploy backend from root directory
cd /path/to/CodeScrybe-Legacy-Repository-AI
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-backend .
gcloud run deploy codescrybe-backend --image gcr.io/$PROJECT_ID/codescrybe-backend --region=$REGION --allow-unauthenticated

# Deploy frontend from Client directory
cd Client
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-client .
gcloud run deploy codescrybe-client --image gcr.io/$PROJECT_ID/codescrybe-client --region=$REGION --allow-unauthenticated

# Check service status
gcloud run services list --region=$REGION

# View logs
gcloud run services logs codescrybe-backend --region=$REGION
gcloud run services logs codescrybe-client --region=$REGION
```

## 🎉 Success!

Your CodeScrybe application is now deployed on GCP! 

- **Backend API**: Handles repository analysis and provides GraphRAG capabilities
- **Frontend UI**: Provides user-friendly interface for code exploration
- **Scalable**: Cloud Run automatically scales based on demand
- **Secure**: Environment variables and secrets properly managed

For ongoing maintenance, monitor your services through the [GCP Console](https://console.cloud.google.com/run) and set up alerts for any issues.

---

**Need Help?** Check the [GCP Cloud Run documentation](https://cloud.google.com/run/docs) or refer to the individual README files in the `Server/` and `Client/` directories.