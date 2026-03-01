# Local Development Setup

This guide helps you set up Saarthi.AI for local development.

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:4000
```

For local development, you can use a local API server or point to a deployed API Gateway.

### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Backend Setup

### Option A: Local Lambda Testing with SAM

1. Install AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

2. Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  RagQueryFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/lambdas/rag_query/
      Handler: handler.handler
      Runtime: python3.12
      Environment:
        Variables:
          AWS_REGION: us-east-1
          # Add other env vars
```

3. Test locally:

```bash
sam local start-api
```

### Option B: Direct Python Testing

1. Install dependencies for each Lambda:

```bash
cd backend/lambdas/rag_query
pip install -r requirements.txt
```

2. Create a test script:

```python
# test_handler.py
import json
from handler import handler

event = {
    "body": json.dumps({
        "query": "What is PMAY?",
        "language": "en"
    })
}

response = handler(event, None)
print(json.dumps(response, indent=2))
```

3. Run test:

```bash
python test_handler.py
```

**Note**: You'll need AWS credentials configured for Bedrock, S3, etc.

## Mock Services for Local Development

For local development without AWS services, you can create mock implementations:

### Mock Bedrock Client

```python
# backend/utils/mock_bedrock.py
def get_embedding(text: str) -> List[float]:
    # Return mock embedding
    return [0.1] * 1536  # Titan embedding dimension

def invoke_claude(prompt: str, **kwargs) -> str:
    # Return mock response
    return "This is a mock response. In production, this would use Claude."
```

### Mock OpenSearch Client

```python
# backend/utils/mock_opensearch.py
def vector_search(query_vector, top_k=5):
    # Return mock results
    return [
        {
            "text": "Sample document text",
            "source": "mock-source.pdf",
            "page": 1,
            "score": 0.85
        }
    ]
```

## Testing

### Frontend Tests

```bash
cd frontend
npm run test  # If tests are set up
npm run lint
npm run type-check
```

### Backend Tests

```bash
cd backend
# Install pytest
pip install pytest pytest-mock

# Run tests
pytest tests/
```

## Development Workflow

1. **Frontend Changes**: 
   - Make changes in `frontend/`
   - See changes instantly with hot reload
   - Test API integration with mock or real backend

2. **Backend Changes**:
   - Make changes in `backend/lambdas/`
   - Test locally with SAM or direct invocation
   - Deploy to AWS for integration testing

3. **Infrastructure Changes**:
   - Update `infra/cdk-stack.ts`
   - Run `cdk diff` to see changes
   - Deploy with `cdk deploy`

## Common Issues

### Module Import Errors

If you see import errors in Lambda handlers:

```python
# Add to handler.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
```

### AWS Credentials

Ensure AWS credentials are configured:

```bash
aws configure list
```

### Python Version Mismatch

Use Python 3.12 for Lambda:

```bash
python3.12 --version
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- TypeScript and JavaScript
- AWS Toolkit
- Tailwind CSS IntelliSense

### Settings

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "python3.12",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

## Next Steps

- Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Check [API documentation](./openapi.yaml) for endpoint details
- Review [README.md](../README.md) for architecture overview
