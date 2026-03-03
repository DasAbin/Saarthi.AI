# 🚀 Deployment Guide - Saarthi.AI

Complete deployment instructions for AWS Amplify (Frontend) + Lambda + API Gateway (Backend).

**Quick start:** See [START_HERE.md](../START_HERE.md) for the fastest path to deployment.

## 📋 Prerequisites

- AWS Account with admin access
- AWS CLI installed and configured (`aws configure`)
- Node.js 18+ installed
- Python 3.12+ installed
- AWS CDK installed (`npm install -g aws-cdk`)
- Git repository (GitHub recommended)

## 🏗️ Part 1: Backend Deployment (Lambda + API Gateway)

### Step 1: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: ap-south-1 (or your preferred region)
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 2: Bedrock Model Access

**Update:** Bedrock models are now **automatically enabled** when first invoked!

**What happens:**
- Serverless foundation models (Titan) enable automatically on first invocation
- For Anthropic models (Claude), first-time users may need to submit use case details
- This happens when your Lambda functions first try to use the models

**What to do:**
1. **No manual request needed** - proceed with deployment
2. After deployment, if you see access denied errors:
   - Check CloudWatch logs for specific error
   - Go to AWS Console → Bedrock → Model catalog
   - Try invoking Claude in the playground - submit use case if prompted
   - After first successful invocation, models are enabled account-wide

### Step 3: Deploy Infrastructure with CDK

```bash
# Navigate to infrastructure folder
cd infra

# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Review what will be created
cdk diff

# Deploy stack
cdk deploy
```

**⏱️ Deployment Time:** ~20-30 minutes

**What gets created:**
- API Gateway REST API
- 7 Lambda functions
- DynamoDB table (for vector storage)
- S3 buckets (PDFs, embeddings, temp audio)
- IAM roles with permissions
- CloudWatch log groups

### Step 4: Save API Gateway URL

After deployment, CDK will output:

```
Outputs:
SaarthiAiStack.ApiGatewayUrl = https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
SaarthiAiStack.PdfBucketName = saarthi-pdfs-xxxxx
SaarthiAiStack.OpenSearchCollectionEndpoint = ...
```

**Copy the API Gateway URL!** You'll need it for frontend configuration.

### Step 5: DynamoDB Table (Auto-Created by CDK)

**⚠️ Good News:** CDK automatically creates the DynamoDB table during deployment! No manual step needed.

**If you want to create it manually** (optional, requires `dynamodb:CreateTable` permission):

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

**Note:** If you get `AccessDeniedException`, that's OK - CDK will create it automatically. Just proceed with deployment.

### Step 6: Verify Backend Deployment

```bash
# Test health endpoint
curl https://YOUR-API-GATEWAY-URL/prod/health

# Should return: {"success":true,"data":{"status":"ok"}}
```

## 🎨 Part 2: Frontend Deployment (AWS Amplify)

### Option A: Deploy via Amplify Console (Recommended)

#### Step 1: Prepare Repository

1. Push your code to GitHub:
```bash
git add .
git commit -m "feat: Initial Saarthi.AI deployment"
git push origin main
```

#### Step 2: Connect Repository in Amplify

1. Go to AWS Console → AWS Amplify
2. Click "New app" → "Host web app"
3. Select "GitHub" and authorize
4. Select your repository and branch (`main`)
5. Click "Next"

#### Step 3: Configure Build Settings

**Build specification:**

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

**Environment variables:**
- `NEXT_PUBLIC_API_GATEWAY_URL` = `https://YOUR-API-GATEWAY-URL/prod`

#### Step 4: Review and Deploy

1. Review settings
2. Click "Save and deploy"
3. Wait for deployment (~5-10 minutes)

#### Step 5: Get Amplify URL

After deployment, Amplify provides:
- **App URL**: `https://main.xxxxx.amplifyapp.com`
- **Custom domain**: (optional, configure later)

### Option B: Deploy via Amplify CLI

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure

# Initialize Amplify in project
cd frontend
amplify init

# Add hosting
amplify add hosting

# Deploy
amplify publish
```

## ⚙️ Part 3: Configuration

### Frontend Environment Variables

**In Amplify Console:**
1. Go to your app → Environment variables
2. Add:
   - `NEXT_PUBLIC_API_GATEWAY_URL` = `https://YOUR-API-GATEWAY-URL/prod`

**Or create `frontend/.env.production`:**
```env
NEXT_PUBLIC_API_GATEWAY_URL=https://YOUR-API-GATEWAY-URL/prod
```

### Backend Environment Variables

CDK automatically sets these in Lambda functions:
- `AWS_REGION`
- `PDF_BUCKET`
- `EMBEDDINGS_BUCKET`
- `TEMP_AUDIO_BUCKET`
- `DYNAMODB_TABLE`
- `OPENSEARCH_ENDPOINT` (if using OpenSearch)

## 🧪 Part 4: Testing Deployment

### Test Backend Endpoints

```bash
# Set your API Gateway URL
export API_URL="https://YOUR-API-GATEWAY-URL/prod"

# Health check
curl $API_URL/health

# Test RAG query
curl -X POST $API_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PMAY?", "language": "en"}'

# Test scheme recommendation
curl -X POST $API_URL/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "state": "Maharashtra",
    "income": 200000,
    "occupation": "Farmer"
  }'
```

### Test Frontend

1. Visit your Amplify URL
2. Test each feature:
   - Chat/RAG query
   - PDF upload
   - Voice recording
   - Scheme recommendation
   - Grievance generation

## 📊 Part 5: Monitoring & Logs

### View Lambda Logs

```bash
# View logs for a specific Lambda
aws logs tail /aws/lambda/saarthi-rag-query --follow

# View all Lambda logs
aws logs tail /aws/lambda --follow
```

### View API Gateway Logs

```bash
aws logs tail /aws/apigateway/SaarthiApi --follow
```

### CloudWatch Dashboards

1. Go to CloudWatch → Dashboards
2. Create dashboard with:
   - Lambda invocations
   - Lambda errors
   - API Gateway 4xx/5xx errors
   - Lambda duration
   - Bedrock API calls

## 🔧 Troubleshooting

### Issue: Bedrock Access Denied

**Two types of access denied errors:**

1. **`ListFoundationModels` Access Denied** (when verifying models):
   - This is **OK** - this permission is not required for the app to work
   - Your Lambda functions have `bedrock:InvokeModel` permission, which is what matters
   - You can skip the verification step and proceed with deployment

2. **`InvokeModel` Access Denied** (when actually using models):
   - Models auto-enable on first invocation
   - For Claude, you may need to submit use case details:
     - Go to AWS Console → Bedrock → Model catalog
     - Open Claude 3 Sonnet in playground
     - Submit use case details if prompted
   - After first successful invocation, models are enabled account-wide
   - Check CloudWatch logs for specific error messages

### Issue: Lambda Timeout

**Solution:**
- Increase timeout in `infra/cdk-stack.ts`:
```typescript
timeout: cdk.Duration.minutes(10)  // Increase from 5
```

### Issue: API Gateway CORS Errors

**Solution:**
- CORS is already configured in CDK stack
- Verify headers in browser DevTools
- Check API Gateway CORS settings

### Issue: Frontend Can't Connect to API

**Solution:**
1. Verify `NEXT_PUBLIC_API_GATEWAY_URL` is set correctly
2. Check API Gateway is deployed
3. Verify API Gateway URL in browser network tab
4. Check CORS headers in response

### Issue: DynamoDB Table Not Found

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

### Issue: S3 Bucket Access Denied

**Solution:**
- Check IAM role permissions in CDK stack
- Verify bucket names match environment variables
- Check bucket policies

## 🔄 Updating Deployment

### Update Backend

```bash
cd infra
cdk deploy
```

### Update Frontend

**Via Amplify Console:**
- Push to GitHub → Auto-deploys

**Via CLI:**
```bash
cd frontend
amplify publish
```

## 💰 Cost Optimization

### Lambda Configuration

- **rag_query**: 1024 MB, 5 min timeout
- **pdf_process**: 2048 MB, 10 min timeout
- **recommend_schemes**: 512 MB, 5 min timeout
- **stt_handler**: 512 MB, 10 min timeout
- **tts_handler**: 512 MB, 5 min timeout
- **grievance_handler**: 512 MB, 5 min timeout

### S3 Lifecycle Policies

Already configured in CDK:
- Temp audio: Auto-delete after 1 day
- PDFs: Transition to Glacier after 90 days

### Monitoring Costs

```bash
# Check Lambda costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

## ✅ Post-Deployment Checklist

- [ ] Backend deployed successfully
- [ ] API Gateway URL saved
- [ ] Frontend deployed to Amplify
- [ ] Environment variables configured
- [ ] Health endpoint working
- [ ] All 5 features tested
- [ ] CloudWatch logs accessible
- [ ] Bedrock model access granted
- [ ] DynamoDB table created
- [ ] S3 buckets accessible
- [ ] CORS working correctly
- [ ] Custom domain configured (optional)

## 🎯 Quick Reference

### Backend URLs
- API Gateway: `https://YOUR-API-GATEWAY-URL/prod`
- Health: `https://YOUR-API-GATEWAY-URL/prod/health`

### Frontend URLs
- Amplify: `https://main.xxxxx.amplifyapp.com`
- Custom Domain: (if configured)

### Useful Commands

```bash
# Deploy backend
cd infra && cdk deploy

# View logs
aws logs tail /aws/lambda/saarthi-rag-query --follow

# Test API
curl https://YOUR-API-GATEWAY-URL/prod/health

# Update frontend
cd frontend && git push origin main
```

## 📞 Support

For issues:
1. Check CloudWatch logs
2. Verify IAM permissions
3. Check Bedrock model access
4. Review API Gateway logs
5. Check Amplify build logs

---

**Deployment Complete! 🎉**

Your Saarthi.AI application is now live on AWS!
