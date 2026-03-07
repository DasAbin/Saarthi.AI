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
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                         │
│  Next.js 14 - React, TypeScript, TailwindCSS, ShadCN UI    │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                        │
│  REST API Gateway - Request Routing, CORS, Rate Limiting   │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Lambda: RAG  │ │ Lambda: PDF  │ │ Lambda: STT  │
│   Query      │ │   Process    │ │   Handler    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                 │
       ↓                 ↓                 ↓
┌─────────────────────────────────────────────────────────────┐
│                    AWS AI Services                          │
│  Bedrock (Nova Micro + Titan) | Textract | Transcribe | Polly│
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  DynamoDB    │ │     S3       │ │  CloudWatch  │
│  (Vectors +  │ │  (Documents) │ │   (Logs)     │
│   Cache)     │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

**Lambda Functions:**
- `rag_query` - RAG-based Q&A with Bedrock + DynamoDB vector search
- `pdf_process` - Document processing with Textract + Bedrock analysis
- `recommend_schemes` - AI-powered scheme matching
- `stt_handler` - Speech-to-text with Transcribe
- `tts_handler` - Text-to-speech with Polly
- `grievance_handler` - Complaint letter generation
- `upload_url` - S3 presigned URL generation
- `health` - Health check endpoint

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


## 🚀 Deployment

### Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- AWS CLI configured
- AWS CDK installed (`npm install -g aws-cdk`)
- **⚠️ Bedrock model access requested** (Claude + Titan)
- **⚠️ AWS Textract service activated** (for document processing)

### ⚠️ MANUAL STEPS REQUIRED

**Before deploying, you must complete these steps manually:**

#### 1. Verify AWS Textract Service (CRITICAL)
- Go to AWS Console → Amazon Textract
- Region: `ap-south-1` (Mumbai)
- Verify service is available (not "Activating" or "Subscription Required")
- If not activated, contact AWS Support or wait for activation
- **DO NOT DEPLOY until Textract is available**

#### 2. Deploy Infrastructure
```powershell
cd infra
npm install
npx cdk bootstrap  # First time only
npx cdk deploy --require-approval never
```

#### 3. Verify IAM Permissions (After Deployment)
- Go to Lambda Console → `saarthi-document-process` → Configuration → Permissions
- Verify IAM role has `textract:DetectDocumentText` permission
- If missing, check CDK stack output or manually add permission

#### 4. Test Document Processing
- Upload a PDF via frontend Document Analyzer
- Check CloudWatch logs: `/aws/lambda/saarthi-document-process`
- Look for "Textract extraction completed" messages

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

After deployment, update `frontend/lib/utils/constants.ts` with the API Gateway URL.

## 🔧 Configuration

### Environment Variables

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_API_GATEWAY_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/prod
```

**Backend** (Set in CDK stack):
- `AWS_REGION` (default: `ap-south-1`)
- `PDF_BUCKET` (S3 bucket for documents)
- `EMBEDDINGS_BUCKET` (S3 bucket for embeddings)
- `TEMP_AUDIO_BUCKET` (S3 bucket for temporary audio files)
- `DYNAMODB_TABLE` (DynamoDB table for vector storage)
- `QUERY_CACHE_TABLE` (DynamoDB table for query cache)
- `CONVERSATIONS_BUCKET` (S3 bucket for conversation logs)
- `TEXT_MODEL_ID` (Bedrock model, default: `apac.amazon.nova-micro-v1:0`)
- `EMBEDDING_MODEL_ID` (Bedrock model, default: `amazon.titan-embed-text-v1`)

## 📝 Supported Document Formats

**Textract (PDFs & Images):**
- PDF (digital and scanned)
- Images: PNG, JPEG, TIFF

**Generic Extractors (Other Formats):**
- Word: DOCX, DOC
- Excel: XLSX, XLS
- PowerPoint: PPTX, PPT
- Text: TXT, CSV, MD, HTML, RTF
- OpenDocument: ODT
- Images: PNG, JPEG, BMP, TIFF, WebP, GIF, SVG

## 📡 API Endpoints

### Key Endpoints:

- `POST /query` - RAG-based Q&A (supports Hindi/English/Marathi)
- `POST /pdf` - Document processing (PDF, Word, Excel, images, etc.)
- `POST /upload-url` - Generate S3 presigned URL for file uploads
- `POST /recommend` - Scheme recommendations based on user profile
- `POST /voice/stt` - Speech-to-text conversion
- `POST /voice/tts` - Text-to-speech synthesis
- `POST /grievance` - Generate formal complaint letters
- `GET /health` - Health check endpoint

See `docs/openapi.yaml` for complete API documentation.

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
