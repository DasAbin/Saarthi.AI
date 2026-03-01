# Saarthi.AI Architecture

## System Overview

Saarthi.AI is a serverless, AI-powered public service assistant built on AWS. The architecture follows a microservices pattern with Lambda functions handling different capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  Next.js 14 (Amplify/Vercel) - React, TypeScript, Tailwind  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                          │
│  REST API Gateway - Request Routing, CORS, Rate Limiting     │
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
│                    AWS AI Services                           │
│  Bedrock (Claude + Titan) │ Textract │ Transcribe │ Polly   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  OpenSearch Serverless │ S3 (PDFs, Embeddings, Temp Audio)   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (Next.js 14)

**Technology Stack:**
- Next.js 14 with App Router
- TypeScript for type safety
- TailwindCSS for styling
- ShadCN UI components
- React Hooks for state management

**Key Components:**
- `app/page.tsx` - Main dashboard
- `components/features/AskAI.tsx` - RAG query interface
- `components/features/PDFAnalyzer.tsx` - PDF upload and analysis
- `components/features/VoiceAssistant.tsx` - STT/TTS interface
- `components/features/SchemeRecommendation.tsx` - Scheme finder
- `components/features/GrievanceGenerator.tsx` - Complaint generator

**API Communication:**
- All API calls go through `/api` routes (proxied to API Gateway)
- Error handling with toast notifications
- Loading states and optimistic UI updates

### Backend Lambda Functions

#### 1. rag_query

**Purpose:** RAG-based Q&A using vector search and LLM

**Flow:**
1. Receive query + language
2. Generate query embedding (Titan)
3. Search OpenSearch Serverless for relevant chunks
4. Format context with retrieved chunks
5. Generate answer using Claude 3 Sonnet
6. Return answer + sources + confidence score

**Resources:**
- Memory: 1024 MB
- Timeout: 5 minutes
- Dependencies: Bedrock, OpenSearch Serverless

#### 2. pdf_process

**Purpose:** Extract text from PDFs and generate summaries

**Flow:**
1. Receive PDF file (base64 or multipart)
2. Upload to S3
3. Extract text using Textract
4. Generate summary using Claude
5. Extract key points
6. Return extracted text, summary, and points

**Resources:**
- Memory: 2048 MB
- Timeout: 10 minutes
- Dependencies: Textract, S3, Bedrock

#### 3. recommend_schemes

**Purpose:** Match users with relevant government schemes

**Flow:**
1. Receive user profile (age, state, income, occupation)
2. Use Claude to match with scheme database
3. Return top 3 recommendations with eligibility and steps

**Resources:**
- Memory: 512 MB
- Timeout: 5 minutes
- Dependencies: Bedrock

#### 4. stt_handler

**Purpose:** Convert speech to text

**Flow:**
1. Receive audio file
2. Upload to temp S3 bucket
3. Start Transcribe job
4. Poll for completion
5. Return transcript
6. Cleanup temp files

**Resources:**
- Memory: 512 MB
- Timeout: 10 minutes
- Dependencies: Transcribe, S3

#### 5. tts_handler

**Purpose:** Convert text to speech

**Flow:**
1. Receive text + language
2. Synthesize speech using Polly
3. Return base64-encoded MP3

**Resources:**
- Memory: 512 MB
- Timeout: 5 minutes
- Dependencies: Polly

#### 6. grievance_handler

**Purpose:** Generate formal complaint letters

**Flow:**
1. Receive issue type, description, location
2. Generate formal letter using Claude
3. Return formatted complaint letter

**Resources:**
- Memory: 512 MB
- Timeout: 5 minutes
- Dependencies: Bedrock

### Data Layer

#### OpenSearch Serverless

**Purpose:** Vector database for RAG

**Structure:**
- Collection: `saarthi-collection`
- Index: `saarthi-index`
- Vector field: `embedding` (1536 dimensions from Titan)
- Metadata fields: `text`, `source`, `page`, `metadata`

**Indexing Flow:**
1. Process PDFs with Textract
2. Chunk text (512 tokens with overlap)
3. Generate embeddings for each chunk
4. Index in OpenSearch with metadata

**Query Flow:**
1. Generate query embedding
2. KNN search for top-k similar chunks
3. Return chunks with scores

#### S3 Buckets

**saarthi-pdfs:**
- Stores uploaded PDF documents
- Versioned for history
- Lifecycle: Transition to Glacier after 90 days

**saarthi-embeddings:**
- Stores pre-computed embeddings metadata
- Used for caching and backup

**saarthi-temp-audio:**
- Temporary storage for Transcribe jobs
- Lifecycle: Auto-delete after 1 day

## Security

### IAM Roles

**Lambda Execution Role:**
- Least privilege principle
- Specific permissions for:
  - Bedrock: InvokeModel for Claude and Titan
  - OpenSearch: APIAccessAll on collection
  - S3: Read/Write on specific buckets
  - Textract: Document analysis
  - Transcribe: Job management
  - Polly: SynthesizeSpeech

### Data Protection

- S3 buckets encrypted at rest (S3-managed keys)
- API Gateway uses HTTPS
- No sensitive data in logs
- Input validation in all handlers

## Scalability

### Lambda

- Auto-scaling based on request volume
- Concurrent execution limits configurable
- Reserved concurrency for critical functions

### OpenSearch Serverless

- Auto-scaling capacity units
- Pay-per-use pricing
- No infrastructure management

### API Gateway

- Default throttling: 10,000 requests/second
- Burst limit: 5,000 requests
- Configurable per-API limits

## Cost Optimization

### Lambda

- Right-size memory allocation
- Use provisioned concurrency only if needed
- Optimize code for faster execution

### Bedrock

- Cache common queries
- Use appropriate model sizes
- Batch requests when possible

### OpenSearch Serverless

- Monitor capacity units
- Scale down during low-traffic periods
- Use appropriate index settings

### S3

- Lifecycle policies for old data
- Use appropriate storage classes
- Delete temp files promptly

## Monitoring

### CloudWatch Metrics

- Lambda: Invocations, errors, duration, throttles
- API Gateway: Request count, latency, 4xx/5xx errors
- Bedrock: Token usage, API calls
- OpenSearch: Query latency, errors

### CloudWatch Logs

- All Lambda functions log to CloudWatch
- Structured logging with context
- Log retention: 7 days (configurable)

### Alarms

- Lambda error rate > 5%
- API Gateway 5xx errors
- Lambda duration > 80% timeout
- Bedrock throttling

## Disaster Recovery

### Backup Strategy

- S3 versioning enabled
- OpenSearch data can be exported
- Infrastructure as Code (CDK) for recreation

### Recovery Procedures

1. Infrastructure: Redeploy with CDK
2. Data: Restore from S3 versions
3. OpenSearch: Re-index from source PDFs

## Future Enhancements

1. **Caching Layer:** Add ElastiCache for common queries
2. **CDN:** CloudFront for frontend assets
3. **Database:** DynamoDB for user preferences and history
4. **Analytics:** Kinesis for usage analytics
5. **Multi-region:** Deploy to multiple regions for latency
6. **WebSockets:** Real-time updates for long-running tasks
