# 🧪 Local Testing Guide - Saarthi.AI

Test the application locally without deploying to AWS.

## 📋 Prerequisites

- Node.js 18+ installed
- Python 3.12+ installed
- Git installed

**No AWS account needed for basic local testing!**

---

## 🚀 Quick Start - Frontend Only

### Step 1: Install Frontend Dependencies

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

### Step 2: Run Frontend Locally

```powershell
# Start development server
npm run dev
```

**Frontend will run on:** `http://localhost:3000`

### Step 3: Test Frontend UI

1. Open browser: `http://localhost:3000`
2. Navigate through pages:
   - Home/Dashboard
   - Chat page
   - PDF Analyzer page
   - Voice Assistant page
   - Scheme Recommendation page
   - Grievance Generator page

**Note:** API calls will fail without backend, but you can test:
- ✅ UI components render correctly
- ✅ Navigation works
- ✅ Forms display properly
- ✅ Responsive design
- ✅ Language switching (UI only)

---

## 🔧 Backend Testing (Without AWS)

### Option 1: Mock Backend Responses

Create a simple mock server to test frontend integration:

**Create `frontend/mock-server.js`:**

```javascript
const express = require('express');
const app = express();
app.use(express.json());

// Mock endpoints
app.post('/api/query', (req, res) => {
  res.json({
    success: true,
    data: {
      answer: "This is a mock response for testing.",
      sources: ["Mock Source 1", "Mock Source 2"],
      confidence: 0.85
    }
  });
});

app.post('/api/pdf', (req, res) => {
  res.json({
    success: true,
    data: {
      extracted_text: "Mock PDF text content...",
      summary: "This is a mock summary of the PDF.",
      key_points: ["Point 1", "Point 2", "Point 3"]
    }
  });
});

app.post('/api/recommend', (req, res) => {
  res.json({
    success: true,
    data: {
      schemes: [
        {
          name: "Mock Scheme 1",
          description: "Mock description",
          eligibility: "Mock eligibility criteria",
          apply_steps: ["Step 1", "Step 2"]
        }
      ]
    }
  });
});

app.post('/api/grievance', (req, res) => {
  res.json({
    success: true,
    data: {
      complaint_letter: "Mock complaint letter content..."
    }
  });
});

app.get('/api/health', (req, res) => {
  res.json({ success: true, data: { status: "ok" } });
});

app.listen(3001, () => {
  console.log('Mock server running on http://localhost:3001');
});
```

**Run mock server:**

```powershell
# Install express
npm install express --save-dev

# Run mock server
node mock-server.js
```

**Update frontend to use mock server:**

Edit `frontend/lib/api/client.ts` temporarily:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:3001';
```

### Option 2: Test Lambda Functions Locally

**Install dependencies for a Lambda:**

```powershell
cd backend/lambdas/rag_query
pip install -r requirements.txt
```

**Test Lambda handler directly:**

```powershell
# Create test_event.json
@'
{
  "body": "{\"query\": \"What is PMAY?\", \"language\": \"en\"}"
}
'@ | Out-File -FilePath test_event.json -Encoding utf8

# Test handler (requires AWS credentials configured)
python -c "
import json
from handler import handler
with open('test_event.json') as f:
    event = json.load(f)
result = handler(event, None)
print(json.dumps(result, indent=2))
"
```

**⚠️ Note:** This requires AWS credentials and may call real AWS services (Bedrock, DynamoDB, etc.)

---

## 🎯 What You Can Test Locally

### ✅ Frontend (No Backend Needed)

- [ ] UI components render correctly
- [ ] Navigation between pages works
- [ ] Forms display and validate input
- [ ] Language selector works (UI only)
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Loading states display
- [ ] Error messages display
- [ ] Accessibility features (if implemented)

### ✅ Frontend + Mock Backend

- [ ] API calls succeed
- [ ] Data displays correctly
- [ ] Error handling works
- [ ] Loading states during API calls
- [ ] Form submissions work

### ⚠️ Requires AWS (Not Fully Local)

- [ ] Actual RAG queries (needs Bedrock)
- [ ] PDF processing (needs Textract)
- [ ] Voice STT/TTS (needs Transcribe/Polly)
- [ ] Real scheme recommendations (needs Bedrock)
- [ ] Grievance generation (needs Bedrock)

---

## 🧪 Testing Checklist

### Frontend UI Testing

```powershell
# 1. Start frontend
cd frontend
npm run dev

# 2. Open browser
# Visit: http://localhost:3000

# 3. Test each page:
# - Home page loads
# - Chat page loads
# - PDF page loads
# - Voice page loads
# - Recommend page loads
# - Grievance page loads
```

### Component Testing (If Tests Exist)

```powershell
# Run tests (if configured)
npm test

# Or run specific test
npm test -- ChatInterface.test.tsx
```

### Build Testing

```powershell
# Test production build
npm run build

# Test production server
npm start
```

---

## 🐛 Common Local Testing Issues

### Issue: "Module not found"

**Solution:**
```powershell
# Reinstall dependencies
rm -r node_modules
npm install
```

### Issue: "Port 3000 already in use"

**Solution:**
```powershell
# Use different port
npm run dev -- -p 3001
```

### Issue: "TypeScript errors"

**Solution:**
```powershell
# Check types
npm run type-check

# Fix auto-fixable issues
npm run lint -- --fix
```

### Issue: "API calls fail"

**Solution:**
- This is expected without backend
- Use mock server (see Option 1 above)
- Or deploy backend to AWS

---

## 📝 Quick Test Commands

```powershell
# Frontend only
cd frontend
npm install
npm run dev
# Visit http://localhost:3000

# With mock backend
cd frontend
npm install express --save-dev
node mock-server.js
# In another terminal: npm run dev

# Test build
cd frontend
npm run build
npm start
```

---

## 🎯 What to Focus On

**For UI/UX Testing:**
- ✅ All pages load correctly
- ✅ Navigation works smoothly
- ✅ Forms are user-friendly
- ✅ Mobile responsive
- ✅ No console errors

**For Integration Testing:**
- ✅ API calls are structured correctly
- ✅ Error handling works
- ✅ Loading states display properly
- ✅ Data flows correctly

**For Full Testing (Requires AWS):**
- Deploy backend first (see START_HERE.md)
- Then test end-to-end functionality

---

**That's it! You can test the frontend locally without any AWS deployment! 🎉**
