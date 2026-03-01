# 📋 Immediate Next Steps Checklist

## ✅ Right Now (5 minutes)

- [ ] **Test Frontend Locally**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Open http://localhost:3000 - You should see the dashboard!

## 🔧 Setup (30 minutes)

- [ ] **Install Prerequisites**
  - [ ] Node.js 18+ (`node --version`)
  - [ ] Python 3.12+ (`python --version`)
  - [ ] AWS CLI (`aws --version`)
  - [ ] AWS CDK (`cdk --version`)

- [ ] **Configure AWS**
  ```bash
  aws configure
  aws sts get-caller-identity  # Verify it works
  ```

## 🚀 Deploy (30-45 minutes)

- [ ] **Deploy Backend**
  ```bash
  cd infra
  npm install
  cdk bootstrap    # First time only
  cdk diff         # Review changes
  cdk deploy       # Deploy everything
  ```

- [ ] **Save API Gateway URL** from CDK output

- [ ] **Update Frontend Config**
  - Edit `frontend/lib/api.ts` OR
  - Create `frontend/.env.local` with API Gateway URL

- [ ] **Test API**
  ```bash
  curl https://YOUR-API-GATEWAY-URL/prod/health
  ```

## 🎨 Deploy Frontend (Choose One)

- [ ] **Option A: AWS Amplify** (Easiest)
  - Push to GitHub
  - Connect in Amplify Console
  - Deploy!

- [ ] **Option B: Vercel**
  ```bash
  cd frontend
  vercel
  ```

- [ ] **Option C: Keep Local** (For testing)
  - Just use `npm run dev`

## 📊 After Deployment

- [ ] **Test All Features**
  - [ ] Ask AI query
  - [ ] PDF upload
  - [ ] Voice recording
  - [ ] Scheme recommendation
  - [ ] Grievance generation

- [ ] **Monitor**
  - [ ] Check CloudWatch logs
  - [ ] Verify Lambda invocations
  - [ ] Check API Gateway metrics

- [ ] **Index Data** (For RAG to work properly)
  - Upload government scheme PDFs
  - Or run indexing script

## 🎯 Priority Order

1. **Test Frontend** (5 min) - See if UI works
2. **Setup AWS** (10 min) - Get credentials ready
3. **Deploy Backend** (30 min) - Get API running
4. **Test API** (5 min) - Verify endpoints work
5. **Deploy Frontend** (15 min) - Make it live
6. **Index Data** (30 min) - Make RAG useful

## ⚠️ Important Notes

1. **Bedrock Access**: You may need to request access to Claude/Titan models in AWS Console
2. **OpenSearch**: Collection creation takes 10-15 minutes
3. **Costs**: Monitor AWS costs, especially Bedrock usage
4. **Region**: Use same region for all services (recommended: us-east-1)

## 🆘 If Something Fails

1. **Check Logs**: `aws logs tail /aws/lambda/saarthi-rag-query --follow`
2. **Verify Credentials**: `aws sts get-caller-identity`
3. **Check Permissions**: Ensure IAM user has necessary permissions
4. **Review CDK Output**: Look for error messages
5. **Check CloudWatch**: Look for Lambda errors

---

**Start here:** `cd frontend && npm install && npm run dev`

Then follow the checklist above! ✅
