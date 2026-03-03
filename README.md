# Saarthi.AI - AI-Powered Public Service Assistant

A production-ready, full-stack AI application that provides multilingual civic information, government scheme discovery, PDF policy analysis, voice interaction, and community grievance automation.

## 🎯 Features

1. **AI Scheme Q&A (RAG)** - Ask questions in Hindi/English/Marathi with citations and confidence scores
2. **PDF Analyzer** - Upload government policy PDFs and get instant summaries and key insights
3. **Scheme Recommendation** - Get personalized scheme recommendations based on age, income, state, and occupation
4. **Voice Assistant** - Speech-to-text and text-to-speech in multiple languages
5. **Grievance Generator** - Automatically generate formal complaint letters for civic issues
6. **Accessibility Mode** - Text-to-speech, large fonts, high contrast support

## 🏗️ Architecture

```
Frontend (Next.js 14 / Amplify Hosting)
    ↓
API Gateway
    ↓
Lambda Functions:
    - rag_query (RAG-based Q&A)
    - pdf_process (PDF OCR & analysis)
    - recommend_schemes (Scheme matching)
    - stt_handler (Speech-to-text)
    - tts_handler (Text-to-speech)
    - grievance_handler (Complaint generation)
    ↓
AWS Services:
    - Amazon Bedrock (Claude 3 Sonnet + Titan Embeddings)
    - OpenSearch Serverless (Vector DB)
    - S3 (PDFs + embeddings)
    - Textract (PDF OCR)
    - Transcribe (STT)
    - Polly (TTS)
    - CloudWatch (Logging)
```

## 📁 Project Structure

```
.
├── frontend/                 # Next.js 14 frontend
│   ├── app/                 # App Router pages
│   ├── components/         # React components
│   │   ├── features/       # Feature components
│   │   └── ui/             # ShadCN UI components
│   └── lib/                # Utilities & API client
│
├── backend/                 # AWS Lambda functions
│   ├── lambdas/            # Individual Lambda handlers
│   │   ├── rag_query/
│   │   ├── pdf_process/
│   │   ├── recommend_schemes/
│   │   ├── stt_handler/
│   │   ├── tts_handler/
│   │   ├── grievance_handler/
│   │   └── health/
│   └── utils/              # Shared utilities
│       ├── bedrock_client.py
│       ├── opensearch_client.py
│       ├── s3_client.py
│       ├── textract_client.py
│       ├── transcribe_client.py
│       └── polly_client.py
│
├── infra/                   # Infrastructure as Code
│   ├── cdk-stack.ts        # AWS CDK stack
│   └── app.ts              # CDK app entry
│
└── docs/                    # Documentation
    └── openapi.yaml        # OpenAPI specification
```

## 🚀 Quick Start

### Local Development

```bash
# Backend
cd backend/lambdas/rag_query
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

### Deploy to AWS

**Backend:**
```bash
cd infra
npm install
cdk bootstrap  # First time only
cdk deploy
```

**Frontend:**
```bash
# Push to GitHub, then deploy via Amplify Console
# Or use: ./scripts/deploy-frontend.sh
```

📖 **Full deployment guide:** [docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)  
⚡ **Quick deploy:** [docs/QUICK_DEPLOY.md](./docs/QUICK_DEPLOY.md)

## 🚀 Deployment

### Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- AWS CLI configured
- AWS CDK installed (`npm install -g aws-cdk`)
- **⚠️ Bedrock model access requested** (Claude + Titan)

**📖 Quick start:** [START_HERE.md](./START_HERE.md)  
**📚 Complete guide:** [HOW_TO_RUN.md](./HOW_TO_RUN.md)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

### Backend Setup

Each Lambda function has its own `requirements.txt`. To test locally:

```bash
# Install dependencies for a Lambda
cd backend/lambdas/rag_query
pip install -r requirements.txt -t .

# Test the handler
python -m pytest tests/  # If tests exist
```

### Infrastructure Deployment

```bash
# Install CDK dependencies
cd infra
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy stack
cdk deploy
```

After deployment, update `frontend/lib/api.ts` with the API Gateway URL.

## 🔧 Configuration

### Environment Variables

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_API_GATEWAY_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/prod
```

**Backend** (Set in CDK stack):
- `AWS_REGION`
- `PDF_BUCKET`
- `EMBEDDINGS_BUCKET`
- `TEMP_AUDIO_BUCKET`
- `OPENSEARCH_ENDPOINT`
- `OPENSEARCH_INDEX`
- `OPENSEARCH_COLLECTION`

## 📡 API Endpoints

See `docs/openapi.yaml` for complete API documentation.

### Key Endpoints:

- `POST /query` - RAG-based Q&A
- `POST /pdf` - PDF processing
- `POST /recommend` - Scheme recommendations
- `POST /voice/stt` - Speech-to-text
- `POST /voice/tts` - Text-to-speech
- `POST /grievance` - Generate complaint letter
- `GET /health` - Health check

## 🛠️ Development

### Frontend Development

```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # Linting
npm run type-check   # TypeScript checking
```

### Backend Development

Each Lambda can be tested locally using AWS SAM or by invoking the handler directly:

```python
# Example: Test rag_query handler
from handler import handler

event = {
    "body": json.dumps({
        "query": "What is PMAY?",
        "language": "en"
    })
}

response = handler(event, None)
print(response)
```

## 📊 Cost Optimization

- **Lambda**: Use appropriate memory sizes (128MB for health, 512MB-2GB for processing)
- **Bedrock**: Use caching for common queries
- **OpenSearch Serverless**: Pay-per-use pricing
- **S3**: Lifecycle policies for auto-deletion of temp files
- **Textract**: Use async processing for large PDFs

## 🔒 Security

- IAM roles with least privilege
- S3 buckets with encryption
- API Gateway CORS configuration
- Input validation in all handlers
- Error handling without exposing internals

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ for AI for Bharat
