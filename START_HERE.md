# 🚀 START HERE - Quick Run Guide

**Note:** Commands are shown for both PowerShell (Windows) and Bash (Mac/Linux). Use the appropriate one for your system.

## What You Need to Do (In Order)

### 1️⃣ Install Software (One-Time)

```bash
# Check if installed
node --version    # Need 18+
python --version  # Need 3.12+
aws --version     # Need AWS CLI
cdk --version     # Need AWS CDK
```

**If missing:**
- Node.js: https://nodejs.org/
- Python: https://www.python.org/
- AWS CLI: https://aws.amazon.com/cli/
- AWS CDK: `npm install -g aws-cdk`

### 2️⃣ Configure AWS (One-Time)

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Region: ap-south-1
# Output: json
```

**Get credentials:** AWS Console → IAM → Users → Your User → Security credentials → Create access key

### 3️⃣ Bedrock Model Access ⚠️ IMPORTANT

**Good news:** Bedrock models are now **automatically enabled** when first invoked! No manual request needed.

**However, for Anthropic models (Claude):**
- First-time users may need to submit use case details when first invoking the model
- This happens automatically when your Lambda tries to use Claude for the first time
- You may see a prompt in the AWS Console asking for use case details

**What to do:**
1. Models will be enabled automatically when your Lambda functions invoke them
2. If you see a prompt for use case details, fill it out (usually just "AI application development" or similar)
3. After first invocation, models are enabled account-wide

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

**⚠️ Note:** 
- If you get `AccessDeniedException` for `ListFoundationModels`, that's **OK** - this permission is not required for the app to work
- Models will still auto-enable when your Lambda functions invoke them
- If you get access denied errors when actually using the models, check CloudWatch logs - you may need to submit use case details via AWS Console → Bedrock → Model catalog → Playground

### 4️⃣ Create DynamoDB Table (Optional)

**⚠️ Good News:** CDK will create the DynamoDB table automatically during deployment! You can skip this step.

**If you want to create it manually** (requires `dynamodb:CreateTable` permission):

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

**Note:** If you get `AccessDeniedException`, that's OK - CDK will create it automatically. Just proceed to the next step.

### 5️⃣ Deploy Backend

```bash
cd infra
npm install
cdk bootstrap  # First time only
cdk deploy
```

**⏱️ Takes 20-30 minutes**

**Save the API Gateway URL from output!**

### 6️⃣ Deploy Frontend

**Option A: Amplify Console (Easiest)**

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. Go to: https://console.aws.amazon.com/amplify/
3. Click "New app" → "Host web app"
4. Connect GitHub repository
5. Build settings: Use `amplify.yml` from repo
6. Add environment variable:
   - Key: `NEXT_PUBLIC_API_GATEWAY_URL`
   - Value: `https://your-api-gateway-url/prod` (from step 5)
7. Click "Save and deploy"

**⏱️ Takes 5-10 minutes**

### 7️⃣ Test

1. Visit your Amplify URL
2. Test all features:
   - Chat query
   - PDF upload
   - Voice recording
   - Scheme recommendation
   - Grievance generator

---

## 🐛 Common Issues

**"Bedrock Access Denied"**
→ Models auto-enable, but first-time Claude users may need to submit use case details via AWS Console → Bedrock → Model catalog → Playground

**"Lambda Timeout"**
→ Increase timeout in `infra/cdk-stack.ts`, then `cdk deploy`

**"Frontend can't connect"**
→ Check `NEXT_PUBLIC_API_GATEWAY_URL` is set correctly in Amplify

**"DynamoDB table not found"**
→ Create manually (step 4)

---

## 📚 More Help

- **🧪 Local testing:** [LOCAL_TESTING.md](./LOCAL_TESTING.md) - Test frontend only
- **📦 Full project guide:** [HOW_TO_RUN.md](./HOW_TO_RUN.md) - Complete step-by-step instructions
- **🚀 Deployment guide:** [docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) - Amplify + Lambda + API Gateway

---

## ✅ Quick Checklist

- [ ] Software installed (Node, Python, AWS CLI, CDK)
- [ ] AWS configured (`aws configure`)
- [ ] Bedrock models will auto-enable (may need use case submission for Claude)
- [ ] DynamoDB table created
- [ ] Backend deployed (`cdk deploy`)
- [ ] API Gateway URL saved
- [ ] Code pushed to GitHub
- [ ] Amplify app created
- [ ] Environment variable set
- [ ] Frontend deployed
- [ ] All features tested

---

**That's it! Follow these steps in order and you'll be running in ~1 hour! 🎉**
