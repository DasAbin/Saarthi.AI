# Deployment Guide

This guide walks you through deploying Saarthi.AI to AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured (`aws configure`)
3. **Node.js 18+** and npm
4. **Python 3.12+**
5. **AWS CDK** installed globally (`npm install -g aws-cdk`)
6. **Docker** (for Lambda layer builds if needed)

## Step 1: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

## Step 2: Bootstrap CDK (First Time Only)

```bash
cd infra
npm install
cdk bootstrap
```

This creates the necessary S3 bucket and IAM roles for CDK deployments.

## Step 3: Deploy Infrastructure

```bash
cd infra
cdk deploy
```

This will:
- Create S3 buckets for PDFs, embeddings, and temp audio
- Create OpenSearch Serverless collection and index
- Create Lambda functions for all endpoints
- Create API Gateway with all routes
- Set up IAM roles with least privilege permissions

**Note**: OpenSearch Serverless collection creation can take 10-15 minutes.

## Step 4: Update Frontend Configuration

After deployment, CDK will output the API Gateway URL. Update `frontend/lib/api.ts`:

```typescript
const API_BASE_URL = 'https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod';
```

Or set environment variable:

```bash
cd frontend
echo "NEXT_PUBLIC_API_GATEWAY_URL=https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod" > .env.local
```

## Step 5: Deploy Frontend

### Option A: AWS Amplify Hosting (Recommended)

1. Push code to GitHub
2. Go to AWS Amplify Console
3. Connect repository
4. Build settings:
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
     cache:
       paths:
         - frontend/node_modules/**/*
   ```
5. Add environment variable: `NEXT_PUBLIC_API_GATEWAY_URL`

### Option B: Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

### Option C: Static Export + S3

```bash
cd frontend
npm run build
# Upload .next/static to S3 + CloudFront
```

## Step 6: Index Initial Data (Optional)

To populate OpenSearch with government scheme data:

1. Create a script to process PDFs and generate embeddings
2. Use `backend/utils/opensearch_client.py` to index documents
3. Or use the `pdf_process` Lambda to process PDFs, then manually index

## Step 7: Test Deployment

```bash
# Health check
curl https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod/health

# Test query
curl -X POST https://YOUR-API-GATEWAY-ID.execute-api.REGION.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PMAY?", "language": "en"}'
```

## Cost Optimization

### Lambda Configuration

- **rag_query**: 1024 MB memory, 5 min timeout
- **pdf_process**: 2048 MB memory, 10 min timeout
- **recommend_schemes**: 512 MB memory, 5 min timeout
- **stt_handler**: 512 MB memory, 10 min timeout
- **tts_handler**: 512 MB memory, 5 min timeout
- **grievance_handler**: 512 MB memory, 5 min timeout
- **health**: 128 MB memory, 30 sec timeout

### S3 Lifecycle Policies

- Temp audio bucket: Auto-delete after 1 day
- PDF bucket: Transition to Glacier after 90 days
- Embeddings bucket: No lifecycle (permanent storage)

### OpenSearch Serverless

- Use appropriate capacity units based on traffic
- Monitor usage in CloudWatch
- Scale down during low-traffic periods

## Monitoring

### CloudWatch Dashboards

Create dashboards for:
- Lambda invocations and errors
- API Gateway request counts
- Bedrock API calls
- OpenSearch query latency
- S3 storage usage

### Alarms

Set up alarms for:
- Lambda error rate > 5%
- API Gateway 5xx errors
- Lambda duration > 80% of timeout
- Bedrock throttling

## Troubleshooting

### Lambda Timeout Errors

- Increase timeout in CDK stack
- Check CloudWatch logs for bottlenecks
- Optimize Bedrock prompts

### OpenSearch Connection Errors

- Verify IAM permissions
- Check collection status
- Ensure endpoint is correct

### API Gateway CORS Errors

- Verify CORS configuration in CDK stack
- Check preflight OPTIONS requests
- Verify headers in frontend requests

## Rollback

```bash
cd infra
cdk destroy
```

**Warning**: This will delete all resources including S3 buckets (unless RETAIN policy is set).

## Production Checklist

- [ ] Enable CloudWatch Logs retention (7+ days)
- [ ] Set up CloudWatch Alarms
- [ ] Configure API Gateway throttling
- [ ] Enable S3 versioning
- [ ] Set up backup for OpenSearch data
- [ ] Configure custom domain for API Gateway
- [ ] Set up WAF rules for API Gateway
- [ ] Enable AWS Shield for DDoS protection
- [ ] Configure CloudFront for frontend
- [ ] Set up CI/CD pipeline
- [ ] Document runbooks for common issues
