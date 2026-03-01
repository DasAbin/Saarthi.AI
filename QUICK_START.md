# 🚀 Quick Start Guide - What to Do Next

Follow these steps to get Saarthi.AI running:

## Step 1: Test Frontend Locally (5 minutes)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:3000` in your browser. You should see the dashboard!

**Note:** The API calls will fail until you deploy the backend, but you can see the UI.

## Step 2: Set Up AWS Account & Credentials

### 2.1 Install AWS CLI
```bash
# Windows (PowerShell)
winget install Amazon.AWSCLI

# Mac
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2.2 Configure AWS Credentials
```bash
aws configure
```

Enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

### 2.3 Verify Setup
```bash
aws sts get-caller-identity
```

You should see your AWS account details.

## Step 3: Install Prerequisites

### 3.1 Install AWS CDK
```bash
npm install -g aws-cdk
cdk --version  # Should show version 2.x
```

### 3.2 Install Python Dependencies (for Lambda)
```bash
# Make sure Python 3.12 is installed
python --version  # Should be 3.12+

# Install pip if needed
python -m ensurepip --upgrade
```

## Step 4: Deploy Backend Infrastructure

### 4.1 Navigate to Infrastructure Folder
```bash
cd infra
```

### 4.2 Install Dependencies
```bash
npm install
```

### 4.3 Bootstrap CDK (First Time Only)
```bash
cdk bootstrap
```

This creates the CDK toolkit stack in your AWS account. Takes ~5 minutes.

### 4.4 Review What Will Be Created
```bash
cdk diff
```

This shows all resources that will be created. Review carefully!

### 4.5 Deploy Stack
```bash
cdk deploy
```

**This will:**
- Create S3 buckets
- Create OpenSearch Serverless collection (takes 10-15 minutes!)
- Create Lambda functions
- Create API Gateway
- Set up IAM roles

**⏱️ Total time: ~20-30 minutes**

### 4.6 Save API Gateway URL

After deployment, CDK will output:
```
Outputs:
SaarthiAiStack.ApiGatewayUrl = https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
```

**Copy this URL!** You'll need it in the next step.

## Step 5: Configure Frontend

### 5.1 Update API URL

Edit `frontend/lib/api.ts`:

```typescript
const API_BASE_URL = 'https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod';
```

Or create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod
```

### 5.2 Restart Frontend Dev Server
```bash
cd frontend
npm run dev
```

## Step 6: Test the Application

### 6.1 Test Health Endpoint
```bash
curl https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod/health
```

Should return: `{"success":true,"data":{"status":"ok"}}`

### 6.2 Test Query Endpoint
```bash
curl -X POST https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PMAY?", "language": "en"}'
```

**Note:** This will work, but may return empty results until you index data in OpenSearch.

### 6.3 Test in Browser

1. Open `http://localhost:3000`
2. Click "Ask AI" card
3. Type a question
4. Click "Ask"

## Step 7: Index Initial Data (Optional but Recommended)

To get meaningful RAG results, you need to index government scheme documents:

### Option A: Use PDF Process Lambda

1. Upload a government scheme PDF through the UI
2. The PDF will be processed and can be indexed

### Option B: Manual Indexing Script

Create `backend/scripts/index_documents.py`:

```python
import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")

from utils.bedrock_client import get_embedding
from utils.opensearch_client import index_document

# Example: Index a document
text = "PMAY is a housing scheme for economically weaker sections..."
embedding = get_embedding(text)
index_document(
    doc_id="pmay-001",
    text=text,
    embedding=embedding,
    metadata={
        "source": "pmay-scheme.pdf",
        "page": 1,
        "scheme_name": "PMAY"
    }
)
```

## Step 8: Deploy Frontend (Choose One)

### Option A: AWS Amplify (Recommended)

1. Push code to GitHub
2. Go to AWS Amplify Console
3. Click "New app" → "Host web app"
4. Connect your GitHub repository
5. Build settings:
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
           - cd frontend
           - npm run build
     artifacts:
       baseDirectory: frontend/.next
       files:
         - '**/*'
   ```
6. Add environment variable: `NEXT_PUBLIC_API_GATEWAY_URL`
7. Deploy!

### Option B: Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

Follow prompts and add environment variable.

### Option C: Static Export + S3

```bash
cd frontend
npm run build
# Upload .next/static to S3 + CloudFront
```

## Step 9: Monitor & Optimize

### 9.1 Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/saarthi-rag-query --follow

# View API Gateway logs
aws logs tail /aws/apigateway/SaarthiApi --follow
```

### 9.2 Set Up CloudWatch Alarms

Go to CloudWatch Console → Alarms → Create alarm for:
- Lambda errors
- API Gateway 5xx errors
- Lambda duration

### 9.3 Monitor Costs

- Check AWS Cost Explorer
- Set up billing alerts
- Review Lambda invocations
- Monitor Bedrock usage

## Troubleshooting

### Issue: CDK Bootstrap Fails

**Solution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Try with specific account/region
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Issue: OpenSearch Collection Creation Times Out

**Solution:**
- OpenSearch Serverless can take 15-20 minutes
- Check CloudWatch logs
- Verify IAM permissions

### Issue: Lambda Function Errors

**Solution:**
```bash
# Check logs
aws logs tail /aws/lambda/saarthi-rag-query --follow

# Common issues:
# - Missing environment variables
# - IAM permissions
# - Bedrock model access (request access in AWS Console)
```

### Issue: API Gateway Returns 502

**Solution:**
- Check Lambda function logs
- Verify Lambda timeout settings
- Check API Gateway integration

### Issue: Frontend Can't Connect to API

**Solution:**
- Verify API Gateway URL is correct
- Check CORS settings in API Gateway
- Check browser console for errors
- Verify API Gateway is deployed

## Next Steps After Setup

1. **Add More Schemes**: Index more government scheme documents
2. **Customize UI**: Update colors, branding in `frontend/app/globals.css`
3. **Add Features**: Extend with new capabilities
4. **Optimize Costs**: Review and adjust Lambda memory/timeout
5. **Set Up Monitoring**: Create CloudWatch dashboards
6. **Add Authentication**: Implement user authentication if needed

## Quick Commands Reference

```bash
# Frontend
cd frontend && npm run dev

# Deploy Infrastructure
cd infra && cdk deploy

# View Infrastructure
cd infra && cdk diff

# Destroy Infrastructure (careful!)
cd infra && cdk destroy

# Check AWS Resources
aws lambda list-functions
aws apigateway get-rest-apis
aws s3 ls
```

## Need Help?

- Check `docs/DEPLOYMENT.md` for detailed deployment guide
- Check `docs/SETUP.md` for local development setup
- Check `docs/ARCHITECTURE.md` for system architecture
- Review CloudWatch logs for errors
- Check AWS Service Health Dashboard

---

**You're all set! 🎉**

Start with Step 1 to see the UI, then proceed with deployment when ready.
