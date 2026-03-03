# 🚀 How to Run Saarthi.AI - Complete Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Manual AWS Setup (REQUIRED)](#manual-aws-setup-required)
3. [Local Development](#local-development)
4. [Deploy to AWS](#deploy-to-aws)
5. [Run After Deployment](#run-after-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Required Software

**Windows:**
```powershell
# Install Node.js 18+ from https://nodejs.org/
node --version  # Should show v18 or higher

# Install Python 3.12+ from https://www.python.org/
python --version  # Should show 3.12 or higher

# Install Git from https://git-scm.com/
git --version
```

**Mac/Linux:**
```bash
# Install Node.js
brew install node@18  # or use nvm

# Install Python
brew install python@3.12  # or apt-get install python3.12

# Git usually pre-installed
git --version
```

### 2. Install AWS Tools

```bash
# Install AWS CLI
# Windows: Download from https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: sudo apt-get install awscli

aws --version  # Verify installation

# Install AWS CDK
npm install -g aws-cdk
cdk --version  # Verify installation
```

### 3. Configure AWS CLI

```bash
aws configure
```

**Enter:**
- AWS Access Key ID: `[Your Access Key]`
- AWS Secret Access Key: `[Your Secret Key]`
- Default region: `ap-south-1` (or your preferred region)
- Default output format: `json`

**Get AWS Credentials:**
1. Go to AWS Console → IAM → Users
2. Click your user → Security credentials
3. Create access key → Download CSV

---

## Manual AWS Setup (REQUIRED)

### ⚠️ These steps MUST be done manually before deployment:

### Step 1: Bedrock Model Access

**Update:** Bedrock models are now **automatically enabled** when first invoked! No manual request needed.

**What happens:**
- Serverless foundation models (including Titan) are automatically enabled across all AWS commercial regions when first invoked
- For Anthropic models (Claude), first-time users may need to submit use case details when first invoking
- This happens automatically when your Lambda functions try to use the models

**What to do:**
1. **No manual request needed** - models enable automatically
2. When you deploy and test, if you see access denied errors:
   - Check CloudWatch logs for the specific error
   - Go to AWS Console → Bedrock → Model catalog
   - Try invoking Claude in the playground - you may be prompted for use case details
   - Fill out use case (e.g., "AI-powered public service assistant")
   - After first successful invocation, models are enabled account-wide

**Verify models are available (Optional):**

**PowerShell:**
```powershell
aws bedrock list-foundation-models --region ap-south-1 | Select-String -Pattern "claude" -CaseSensitive:$false
aws bedrock list-foundation-models --region ap-south-1 | Select-String -Pattern "titan" -CaseSensitive:$false
```

**Mac/Linux:**
```bash
aws bedrock list-foundation-models --region ap-south-1 | grep -i claude
aws bedrock list-foundation-models --region ap-south-1 | grep -i titan
```

**⚠️ Important Notes:**
- If you get `AccessDeniedException` for `ListFoundationModels`, that's **OK** - this permission is not required for the app to work
- The `ListFoundationModels` permission is separate from actually using the models
- Models will auto-enable when your Lambda functions invoke them (they have `bedrock:InvokeModel` permission)
- If you get access denied errors when actually using the models (during deployment/testing), check CloudWatch logs - you may need to submit use case details via AWS Console → Bedrock → Model catalog → Playground

### Step 2: Create DynamoDB Table (Optional)

**⚠️ Important:** CDK will create the DynamoDB table automatically during deployment! You can skip this step and proceed directly to deployment.

**If you want to create it manually** (requires `dynamodb:CreateTable` permission):

**Option A: Via AWS Console**
1. Go to DynamoDB → Tables → Create table
2. Table name: `saarthi-vectors`
3. Partition key: `chunk_id` (String)
4. Settings: Use default settings
5. Click "Create table"

**Option B: Via AWS CLI**

**PowerShell:**
```powershell
aws dynamodb create-table `
  --table-name saarthi-vectors `
  --attribute-definitions AttributeName=chunk_id,AttributeType=S `
  --key-schema AttributeName=chunk_id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region ap-south-1
```

**Mac/Linux:**
```bash
aws dynamodb create-table \
  --table-name saarthi-vectors \
  --attribute-definitions AttributeName=chunk_id,AttributeType=S \
  --key-schema AttributeName=chunk_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**Note:** If you get `AccessDeniedException`, that's OK - CDK will create it automatically during deployment. Just proceed to Step 3.

### Step 2: Create DynamoDB Table (Manual)

**Option A: Via AWS Console**
1. Go to DynamoDB → Tables → Create table
2. Table name: `saarthi-vectors`
3. Partition key: `chunk_id` (String)
4. Settings: Use default settings
5. Click "Create table"

**Option B: Via AWS CLI**
```bash
aws dynamodb create-table \
  --table-name saarthi-vectors \
  --attribute-definitions AttributeName=chunk_id,AttributeType=S \
  --key-schema AttributeName=chunk_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

### Step 3: Verify AWS Account Permissions

Make sure your AWS user has these permissions:
- Lambda (create, update, delete)
- API Gateway (create, deploy)
- S3 (create buckets, read/write)
- DynamoDB (create tables, read/write)
- Bedrock (invoke models)
- Textract, Transcribe, Polly (full access)
- CloudWatch (create log groups)
- IAM (create roles - for CDK)

**Or use AdministratorAccess for testing** (not recommended for production)

---

## Local Development

### Step 1: Clone and Setup

```bash
# Clone repository (if not already done)
git clone <your-repo-url>
cd aiforbharat_final

# Or if already cloned, navigate to project
cd aiforbharat_final
```

### Step 2: Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
# Windows PowerShell:
New-Item -Path .env.local -ItemType File
# Mac/Linux:
touch .env.local

# Add to .env.local:
# NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:3000/api
```

**Edit `frontend/.env.local`:**
```env
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:3000/api
```

### Step 3: Run Frontend Locally

```bash
# Still in frontend directory
npm run dev
```

**Frontend will run on:** `http://localhost:3000`

### Step 4: Setup Backend (Local Testing)

**For each Lambda function:**

```bash
# Example: RAG Query Lambda
cd backend/lambdas/rag_query

# Install Python dependencies
pip install -r requirements.txt

# Test locally (optional)
python -c "
import json
from handler import handler
event = {'body': json.dumps({'query': 'What is PMAY?', 'language': 'en'})}
result = handler(event, None)
print(json.dumps(result, indent=2))
"
```

**Note:** Local Lambda testing requires AWS credentials configured and may call real AWS services.

### Step 5: Test Frontend Locally

1. Open browser: `http://localhost:3000`
2. Test each feature:
   - Chat/RAG query
   - PDF upload
   - Voice recording
   - Scheme recommendation
   - Grievance generator

**Note:** Frontend API routes (`/api/*`) will need backend deployed to work fully.

---

## Deploy to AWS

### Part 1: Deploy Backend

#### Step 1: Navigate to Infrastructure Folder

```bash
cd infra
```

#### Step 2: Install Dependencies

```bash
npm install
```

#### Step 3: Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

**This creates CDK resources in your AWS account (one-time setup).**

#### Step 4: Review What Will Be Created

```bash
cdk diff
```

**Review the changes before deploying.**

#### Step 5: Deploy Stack

```bash
cdk deploy
```

**⏱️ This takes 20-30 minutes**

**What happens:**
- Creates API Gateway
- Creates 7 Lambda functions
- Creates S3 buckets
- Creates IAM roles
- Sets up CloudWatch logs

#### Step 6: Save API Gateway URL

**After deployment, CDK outputs:**
```
Outputs:
SaarthiAiStack.ApiGatewayUrl = https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
```

**⚠️ COPY THIS URL!** You'll need it for frontend.

### Part 2: Deploy Frontend

#### Option A: Deploy via Amplify Console (Recommended)

**Step 1: Push Code to GitHub**

```bash
# If not already pushed
git add .
git commit -m "feat: Ready for deployment"
git push origin main
```

**Step 2: Create Amplify App**

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify)
2. Click "New app" → "Host web app"
3. Select "GitHub" → Authorize
4. Select repository: `your-username/saarthi-ai`
5. Select branch: `main`
6. Click "Next"

**Step 3: Configure Build**

**Build settings:**
- App name: `saarthi-ai` (or your choice)
- Environment: `Production`
- Build specification: Use `amplify.yml` from repo (or paste):

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - cd frontend
        - npm run build
  artifacts:
    baseDirectory: frontend/.next
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
      - frontend/.next/cache/**/*
```

**Step 4: Add Environment Variable**

Click "Advanced settings" → "Environment variables" → Add:
- **Key:** `NEXT_PUBLIC_API_GATEWAY_URL`
- **Value:** `https://xxxxx.execute-api.us-east-1.amazonaws.com/prod` (from backend deployment)

**Step 5: Deploy**

1. Click "Save and deploy"
2. Wait for build (~5-10 minutes)
3. Get your app URL: `https://main.xxxxx.amplifyapp.com`

#### Option B: Deploy via Amplify CLI

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure
amplify configure

# Initialize (in frontend directory)
cd frontend
amplify init

# Add hosting
amplify add hosting

# Set environment variable
amplify env add
# When prompted, add: NEXT_PUBLIC_API_GATEWAY_URL=https://your-api-url/prod

# Deploy
amplify publish
```

---

## Run After Deployment

### Step 1: Test Backend Endpoints

```bash
# Set your API Gateway URL
$env:API_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"  # PowerShell
# export API_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"  # Mac/Linux

# Test health
curl $API_URL/health

# Test query
curl -X POST $API_URL/query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What is PMAY?\", \"language\": \"en\"}'
```

### Step 2: Test Frontend

1. Visit your Amplify URL: `https://main.xxxxx.amplifyapp.com`
2. Test each feature:
   - ✅ Chat/RAG query
   - ✅ PDF upload
   - ✅ Voice recording
   - ✅ Scheme recommendation
   - ✅ Grievance generator

### Step 3: Monitor Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/saarthi-rag-query --follow

# View API Gateway logs
aws logs tail /aws/apigateway/SaarthiApi --follow
```

---

## Complete Manual Checklist

### ✅ Before You Start

- [ ] Node.js 18+ installed
- [ ] Python 3.12+ installed
- [ ] AWS CLI installed and configured
- [ ] AWS CDK installed
- [ ] Git installed
- [ ] AWS account created
- [ ] AWS credentials configured (`aws configure`)

### ✅ Manual AWS Setup (MUST DO)

- [ ] Requested Bedrock Claude 3 Sonnet access
- [ ] Requested Bedrock Titan Embeddings access
- [ ] Verified Bedrock access granted
- [ ] Created DynamoDB table `saarthi-vectors`
- [ ] Verified AWS account has required permissions

### ✅ Backend Deployment

- [ ] Navigated to `infra` folder
- [ ] Ran `npm install`
- [ ] Ran `cdk bootstrap` (first time)
- [ ] Ran `cdk diff` (reviewed changes)
- [ ] Ran `cdk deploy`
- [ ] Saved API Gateway URL from output

### ✅ Frontend Deployment

- [ ] Pushed code to GitHub
- [ ] Created Amplify app
- [ ] Connected repository
- [ ] Configured build settings
- [ ] Set `NEXT_PUBLIC_API_GATEWAY_URL` environment variable
- [ ] Deployed successfully
- [ ] Saved Amplify app URL

### ✅ Testing

- [ ] Backend health endpoint works
- [ ] Frontend loads correctly
- [ ] All 5 features work:
  - [ ] Chat/RAG query
  - [ ] PDF upload
  - [ ] Voice recording
  - [ ] Scheme recommendation
  - [ ] Grievance generator
- [ ] No console errors
- [ ] Mobile responsive

---

## Troubleshooting

### Problem: "Bedrock Access Denied"

**Two scenarios:**

1. **`ListFoundationModels` Access Denied** (during verification):
   - This is **OK** - skip verification and proceed with deployment
   - Your Lambda functions have `bedrock:InvokeModel` permission, which is what matters
   - Models will work when invoked by Lambda functions

2. **`InvokeModel` Access Denied** (when using the app):
   - Models auto-enable on first invocation
   - For Claude, you may need to submit use case details:
     - Go to AWS Console → Bedrock → Model catalog
     - Open Claude 3 Sonnet in playground
     - Submit use case details if prompted
   - After first successful invocation, models are enabled account-wide
   - Check CloudWatch logs for specific error messages
   - Verify region matches (ap-south-1 or your configured region)

### Problem: "CDK Bootstrap Failed"

**Solution:**
```bash
# Specify account and region explicitly
cdk bootstrap aws://ACCOUNT-ID/us-east-1

# Get account ID
aws sts get-caller-identity --query Account --output text
```

### Problem: "Lambda Timeout"

**Solution:**
1. Edit `infra/cdk-stack.ts`
2. Increase timeout: `timeout: cdk.Duration.minutes(10)`
3. Redeploy: `cdk deploy`

### Problem: "Frontend Can't Connect to API"

**Solution:**
1. Verify `NEXT_PUBLIC_API_GATEWAY_URL` is set in Amplify
2. Check API Gateway URL is correct
3. Test API Gateway URL directly: `curl https://your-api-url/prod/health`
4. Check browser console for CORS errors

### Problem: "DynamoDB Table Not Found"

**Solution:**
1. **CDK should create it automatically** - check CloudFormation stack status
2. If missing after deployment, verify CDK stack completed successfully
3. If you need to create manually (requires `dynamodb:CreateTable` permission):

**PowerShell:**
```powershell
aws dynamodb create-table `
  --table-name saarthi-vectors `
  --attribute-definitions AttributeName=chunk_id,AttributeType=S `
  --key-schema AttributeName=chunk_id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region ap-south-1
```

**Mac/Linux:**
```bash
aws dynamodb create-table \
  --table-name saarthi-vectors \
  --attribute-definitions AttributeName=chunk_id,AttributeType=S \
  --key-schema AttributeName=chunk_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**Note:** If you get `AccessDeniedException`, ask your AWS admin to add `dynamodb:CreateTable` permission, or let CDK create it automatically.

### Problem: "Build Fails in Amplify"

**Solution:**
1. Check build logs in Amplify Console
2. Verify `amplify.yml` is correct
3. Check Node.js version (should be 18+)
4. Verify all dependencies in `package.json`

---

## Quick Reference Commands

### Local Development

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend (test Lambda locally)
cd backend/lambdas/rag_query
pip install -r requirements.txt
python handler.py
```

### Deployment

```bash
# Backend
cd infra
npm install
cdk bootstrap  # First time only
cdk deploy

# Frontend (after pushing to GitHub)
# Use Amplify Console or CLI
```

### Testing

```bash
# Test API
curl https://your-api-url/prod/health

# View logs
aws logs tail /aws/lambda/saarthi-rag-query --follow
```

---

## Need Help?

1. Check CloudWatch logs for errors
2. Verify IAM permissions
3. Check Bedrock model access
4. Review API Gateway logs
5. Check Amplify build logs

**Common Issues:**
- Bedrock access not granted → Request access
- Lambda timeout → Increase timeout
- CORS errors → Already configured in CDK
- Frontend build fails → Check Node.js version

---

**You're all set! 🎉**

Follow the checklist above step-by-step, and you'll have Saarthi.AI running in no time!
