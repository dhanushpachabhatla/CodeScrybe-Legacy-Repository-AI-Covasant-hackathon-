# 🚀 GCP Deployment Guide – CodeScrybe

This document explains how to deploy both the **FastAPI backend** and **React frontend** of the CodeScrybe application to **Google Cloud Platform (GCP)** using **Docker + Cloud Build + Cloud Run**.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Initial GCP Setup](#initial-gcp-setup)
- [MongoDB Atlas Setup](#mongodb-atlas-setup)
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
- **MongoDB Atlas** account (free tier available)
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

### 2. Create .dockerignore (in root directory)

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

## 🍃 MongoDB Atlas Setup

### Step 1: Create MongoDB Atlas Account and Cluster

1. **Sign up for MongoDB Atlas**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a free account or sign in
   - Create a new project (e.g., "CodeScrybe")

2. **Create a Free Cluster**
   - Choose "M0 Sandbox" (free tier)
   - Select a cloud provider and region closest to your GCP region
   - Name your cluster (e.g., "codescrybe-cluster")
   - Click "Create Cluster"

3. **Create Database User**
   - Go to "Database Access" in the left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `codescrybe-user` (or your preferred username)
   - Generate a secure password and save it
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

### Step 2: Initial Network Access Configuration

1. **Add Your Current IP (for initial setup)**
   - Go to "Network Access" in the left sidebar
   - Click "Add IP Address"
   - Click "Add Current IP Address"
   - Add description: "Development IP"
   - Click "Confirm"

### Step 3: Get Connection String

1. **Get MongoDB Connection String**
   - Go to "Clusters" in the left sidebar
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Select "Python" and version "3.12 or later"
   - Copy the connection string (format: `mongodb+srv://username:<password>@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority`)
   - Replace `<password>` with your actual database user password

2. **Create Database and Collections (Optional)**
   - You can use MongoDB Compass or the web interface
   - Create database: `codescrybe`
   - Collections will be created automatically by your application

### Step 4: Configure for Cloud Run (Production)

After deploying to Cloud Run, you'll need to whitelist Cloud Run's IP addresses:

1. **Option 1: Allow All IPs (Less Secure)**
   - In "Network Access", click "Add IP Address"
   - Enter `0.0.0.0/0` to allow all IPs
   - Add description: "Cloud Run - All IPs"
   - **Note**: This is less secure but simpler for Cloud Run

2. **Option 2: Use MongoDB Atlas VPC Peering (More Secure)**
   - For production environments, consider VPC peering
   - Requires MongoDB Atlas paid tier
   - Follow [MongoDB Atlas VPC Peering Guide](https://docs.atlas.mongodb.com/security-vpc-peering/)

### Step 5: Environment Variables for MongoDB

Add these to your environment variables:

```bash
# MongoDB Atlas Configuration
MONGODB_URI="mongodb+srv://codescrybe-user:<password>@cluster.xxxxx.mongodb.net/codescrybe?retryWrites=true&w=majority"
DATABASE_NAME="codescrybe"
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
MONGODB_URI="mongodb+srv://codescrybe-user:<password>@cluster.xxxxx.mongodb.net/codescrybe?retryWrites=true&w=majority"
DATABASE_NAME="codescrybe"
```

### Step 2: Update Backend Code for MongoDB

Ensure your FastAPI backend can connect to MongoDB Atlas:

**Example MongoDB connection in your FastAPI app:**

```python
# In Server/backend/app.py or database configuration
from pymongo import MongoClient
import os

# MongoDB Atlas connection
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "codescrybe")

# Create MongoDB client
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client[MONGODB_DB_NAME]

# Test connection
try:
    mongo_client.admin.command('ping')
    print("MongoDB Atlas connection successful!")
except Exception as e:
    print(f"MongoDB Atlas connection failed: {e}")
```

### Step 3: Build and Deploy Backend (From Root Directory)

```bash
# Ensure you're in the root directory of your project
cd /path/to/repository

# Build the Docker image using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-backend .

# Deploy to Cloud Run with environment variables
gcloud run deploy codescrybe-backend \
  --image gcr.io/$PROJECT_ID/codescrybe-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "NEO4J_URI=$NEO4J_URI,NEO4J_USERNAME=$NEO4J_USERNAME,NEO4J_PASSWORD=$NEO4J_PASSWORD,GEMINI_API_KEY=$GEMINI_API_KEY,MONGODB_URI=$MONGODB_URI,MONGODB_DB_NAME=$MONGODB_DB_NAME"
```

### Step 4: Get Backend URL

```bash
# Get the deployed backend URL
gcloud run services describe codescrybe-backend --region=$REGION --format="value(status.url)"
```

### Step 5: Update MongoDB Atlas Network Access for Production

After deployment, you need to allow Cloud Run to access MongoDB Atlas:

1. **Get Cloud Run Outbound IP Ranges**
   - Cloud Run uses dynamic IPs from Google's IP ranges
   - You'll need to allow Google Cloud IP ranges

2. **Option 1: Allow All IPs (Simplest)**
   - In MongoDB Atlas "Network Access"
   - Add IP Address: `0.0.0.0/0`
   - Description: "Cloud Run Production"

3. **Option 2: Allow Google Cloud IP Ranges (More Secure)**
   - Get Google Cloud IP ranges from: https://www.gstatic.com/ipranges/cloud.json
   - Add relevant IP ranges for your region
   - This requires multiple entries but is more secure

4. **Test MongoDB Connection**
   ```bash
   # Check backend logs to verify MongoDB connection
   gcloud run services logs codescrybe-backend --region=$REGION --limit=10
   ```

## 🎨 Frontend Deployment (React)

### Step 1: Navigate to Client Directory

```bash
# Change to the Client directory
cd Client
```

### Step 2: Update API Configuration

Before building, update your React app to use the deployed backend URL:

**Create/Update `Client/src/contants.js`:**

```javascript
// src/constants.ts
export const apiUrl =  'https://codescrybe-backend-xxxxx-as.a.run.app',
```

### Step 3: Build and Deploy Frontend

```bash
# Ensure you're in the Client directory
pwd  # Should show .../CodeScrybe-Legacy-Repository-AI/Client

# Build the Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe .

# Deploy to Cloud Run
gcloud run deploy codescrybe \
  --image gcr.io/$PROJECT_ID/codescrybe \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
```

### Step 4: Get Frontend URL

```bash
# Get the deployed frontend URL
gcloud run services describe codescrybe --region=$REGION --format="value(status.url)"
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
        "https://codescrybe-xxxxx-as.a.run.app",  # Production frontend
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

### 2. Test Database Connections

```bash
# Check backend logs for database connections
gcloud run services logs codescrybe-backend --region=$REGION --limit=20

# Look for MongoDB and Neo4j connection messages
```

### 3. Test Frontend Application

```bash
# Visit your frontend URL
# https://codescrybe-xxxxx-as.a.run.app
```

### 4. Test Full Integration

1. Open your frontend URL in a browser
2. Navigate to the dashboard
3. Try adding a repository
4. Verify the frontend can communicate with the backend
5. Check that data is being stored in MongoDB Atlas

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. MongoDB Connection Issues**

```bash
# Check MongoDB Atlas network access
# Ensure 0.0.0.0/0 is added to IP whitelist

# Check connection string format
# Ensure password is URL encoded if it contains special characters

# Test connection from Cloud Run logs
gcloud run services logs codescrybe-backend --region=$REGION --limit=50 | grep -i mongodb
```

**2. Build Failures**

```bash
# Check build logs
gcloud builds list --limit=5

# Get detailed logs for a specific build
gcloud builds log BUILD_ID
```

**3. Service Not Starting**

```bash
# Check service logs
gcloud run services logs codescrybe-backend --region=$REGION --limit=50
gcloud run services logs codescrybe --region=$REGION --limit=50
```

**4. Database Authentication Issues**

```bash
# Verify MongoDB Atlas user credentials
# Check that user has proper permissions
# Ensure connection string matches Atlas cluster

# Check environment variables
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

### Database Optimization

- **MongoDB Atlas**: Use M0 free tier for development
- **Neo4j Aura**: Use free tier for development
- Monitor database usage and upgrade only when necessary

## 📊 Final Deployment URLs

After successful deployment, you'll have:

| Component | URL Format | Purpose |
|-----------|------------|---------|
| Backend API | `https://codescrybe-backend-xxxxx-as.a.run.app` | FastAPI server with endpoints |
| Frontend UI | `https://codescrybe-xxxxx-as.a.run.app` | React web application |
| API Docs | `https://codescrybe-backend-xxxxx-as.a.run.app/docs` | Interactive API documentation |
| MongoDB Atlas | `cluster.xxxxx.mongodb.net` | Database cluster |

## 📝 Quick Reference Commands

```bash
# Deploy backend from root directory
cd /path/to/CodeScrybe-Legacy-Repository-AI
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe-backend .
gcloud run deploy codescrybe-backend --image gcr.io/$PROJECT_ID/codescrybe-backend --region=$REGION --allow-unauthenticated

# Deploy frontend from Client directory
cd Client
gcloud builds submit --tag gcr.io/$PROJECT_ID/codescrybe .
gcloud run deploy codescrybe --image gcr.io/$PROJECT_ID/codescrybe --region=$REGION --allow-unauthenticated

# Check service status
gcloud run services list --region=$REGION

# View logs
gcloud run services logs codescrybe-backend --region=$REGION
gcloud run services logs codescrybe --region=$REGION

# Test database connections
gcloud run services logs codescrybe-backend --region=$REGION | grep -i "mongodb\|neo4j"
```

## 🎉 Success!

Your CodeScrybe application is now deployed on GCP with MongoDB Atlas! 

- **Backend API**: Handles repository analysis and provides GraphRAG capabilities
- **Frontend UI**: Provides user-friendly interface for code exploration
- **MongoDB Atlas**: Cloud-hosted MongoDB for data storage
- **Neo4j Aura**: Graph database for relationships
- **Scalable**: Cloud Run automatically scales based on demand
- **Secure**: Environment variables and database access properly configured

## 📋 Post-Deployment Checklist

- [ ] MongoDB Atlas cluster created and configured
- [ ] Database user created with proper permissions
- [ ] Network access configured (0.0.0.0/0 for Cloud Run)
- [ ] Connection string tested and added to environment variables
- [ ] Backend deployed with all environment variables
- [ ] Frontend deployed and configured
- [ ] Database connections verified in logs
- [ ] End-to-end functionality tested

For ongoing maintenance, monitor your services through the [GCP Console](https://console.cloud.google.com/run) and [MongoDB Atlas Dashboard](https://cloud.mongodb.com/).

---

**Need Help?** Check the [GCP Cloud Run documentation](https://cloud.google.com/run/docs), [MongoDB Atlas documentation](https://docs.atlas.mongodb.com/), or refer to the individual README files in the `Server/` and `Client/` directories.