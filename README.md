# Agentic Chaser

**LLM-Powered Autonomous Document & LOA Management System for UK Financial Advisors**

An intelligent system that helps UK IFAs be proactive by autonomously identifying chase items, answering natural language queries, and providing actionable insights about their client base.

---

## 🎯 Problem Statement

UK Independent Financial Advisors (IFAs) manage 150-250 client relationships while spending 60-70% of their time on administrative tasks instead of advice. They struggle with:

- **Reactive Trap**: Starting proactive but getting pulled into reactive work
- **Memory Problem**: Can't remember all client details, life events, and follow-ups across 200+ clients
- **Information Overload**: Surrounded by data but starved of insights
- **Compliance Burden**: FCA Consumer Duty requires demonstrating ongoing value

**Agentic Chaser** solves this by providing a proactive chatbot that answers questions, identifies opportunities, tracks follow-ups, and helps advisors be more effective.

---

## ✨ Key Features

### 1. **Natural Language Query System**
Ask questions in plain English and get intelligent answers:
- "Show me clients with ISA allowance still available this tax year"
- "Which clients haven't had a review in over 12 months?"
- "What documents am I still waiting for from clients?"
- "Show me all open action items across my client base"

### 2. **Agentic Architecture with LangGraph**
- Uses Azure OpenAI (GPT-4o-mini) for intelligent reasoning
- Semantic tool matching - LLM selects tools based on descriptions, not keywords
- 40+ specialized tools for different query types
- Autonomous workflow orchestration

### 3. **Autonomous Chasing System**
- Identifies LOAs, documents, and post-advice items needing chase
- Intelligent prioritization based on urgency, client value, and stuck risk
- Generates context-aware communications
- Tracks provider performance

### 4. **Proactive Insights**
- Investment analysis (equity allocation, allowances, excess cash)
- Client lifecycle management (reviews, life events, birthdays)
- Compliance tracking (recommendations, conversations, documents)
- Business analytics (client value, conversion rates, satisfaction)

---

## 🏗️ Architecture & Logic

### System Architecture

```
┌─────────────────┐
│   Frontend      │  React + Vite + Tailwind CSS
│   (Vercel)      │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   Backend API   │  FastAPI + Python
│   (Render)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────────┐
│ Lang  │ │ Insights    │
│ Graph │ │ Engine      │
│ Agent │ │ (Mock Data) │
└───┬───┘ └─────────────┘
    │
┌───▼──────────────┐
│ Azure OpenAI     │
│ (GPT-4o-mini)    │
└──────────────────┘
```

### Agentic Workflow Logic

1. **Query Reception**: User submits natural language query via frontend
2. **Agent Initialization**: `InsightsAgent` initializes with:
   - Azure OpenAI LLM (GPT-4o-mini)
   - 40+ semantic tools (insights + chasing)
   - LangGraph workflow
3. **Tool Selection**: LLM analyzes query and selects appropriate tool(s) based on:
   - Tool descriptions (semantic matching, not keyword matching)
   - Query intent and context
   - Parameter extraction (client names, dates, thresholds)
4. **Tool Execution**: Selected tools execute and return results
5. **Response Generation**: LLM synthesizes tool results into clear, actionable answer
6. **Response Delivery**: Formatted response returned to frontend

### Tool Categories

**Investment Analysis Tools:**
- `analyze_equity_allocation` - Clients underweight in equities
- `check_allowance_availability` - ISA/annual allowance queries
- `analyze_excess_cash` - Cash above emergency fund needs
- `analyze_retirement_goals` - Retirement planning gaps

**Client Management Tools:**
- `find_clients_due_review` - Clients needing reviews
- `find_similar_profiles` - Similar client profiles
- `identify_life_events` - Upcoming life events
- `find_birthdays` - Monthly birthdays

**Compliance Tools:**
- `get_recommendations` - Past recommendations
- `get_conversation_history` - Conversation analysis
- `find_documents_waiting` - Pending documents
- `find_promises` - Commitments made

**Chasing Tools:**
- `identify_loas_needing_chase` - LOAs requiring follow-up
- `identify_documents_needing_chase` - Document requests
- `identify_post_advice_needing_chase` - Post-advice items

**Business Analytics Tools:**
- `analyze_client_value` - Highest value clients
- `analyze_conversion_rates` - Referral source analysis
- `find_satisfied_clients` - Long-term satisfied clients

### Mock Data System

Since this is a hackathon project, all data is mock:
- `MockDataService` - Provides mock data for all endpoints
- `InsightsMock` - Mock insights data
- `MockSession` - Mock database session (no real DB needed)
- Realistic client profiles, cases, and scenarios

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure OpenAI credentials

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export USE_MOCK_DATA="true"
```

5. **Run backend:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run frontend:**
```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

The frontend automatically connects to `http://localhost:8000/api` for local development.

---

## 🌐 Deployment

### Backend Deployment (Render)

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Sign up/login

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select repository: `updated123/CHASER` (or your repo)

3. **Configure Service:**
   - **Name**: `agentic-chaser-api` (or any name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend` ⚠️ **IMPORTANT**
   - **Build Command**: 
     ```bash
     pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

4. **Set Environment Variables:**
   Click "Advanced" → "Add Environment Variable" and add:
   ```
   ALLOWED_ORIGINS=*
   USE_MOCK_DATA=true
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   AZURE_OPENAI_API_KEY=your-api-key
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - Your backend URL will be: `https://your-service-name.onrender.com`

6. **Test:**
   - Visit: `https://your-service-name.onrender.com/health`
   - Should see: `{"status":"healthy","service":"agentic-chaser-api"}`

**Note:** Render free tier services sleep after 15 minutes. First request after sleep takes 30-60 seconds to wake up.

### Frontend Deployment (Vercel)

1. **Go to Vercel Dashboard:**
   - Visit: https://vercel.com/dashboard
   - Sign up/login with GitHub

2. **Import Project:**
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Select repository: `updated123/CHASER` (or your repo)

3. **Configure Project:**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Set Environment Variable:**
   - Go to "Settings" → "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://your-service-name.onrender.com
     ```
   ⚠️ **IMPORTANT:** Do NOT include `/api` at the end!

5. **Deploy:**
   - Click "Deploy"
   - Wait 1-2 minutes
   - Your frontend will be live!

6. **Verify:**
   - Open your Vercel URL
   - Open browser console (F12)
   - Should see: `🔗 API Base URL: https://your-service-name.onrender.com/api`

---

## 📝 API Endpoints

### Natural Language Query
```http
POST /api/insights/natural-language?query=Show me clients with ISA allowance
```

### Dashboard
```http
GET /api/dashboard/stats
GET /api/chases/active
```

### Health Check
```http
GET /health
```

### API Documentation
```http
GET /docs
```

---

## 🔧 Troubleshooting

### Backend Timeout on Render
- **Issue**: Backend takes 30-60 seconds to respond
- **Solution**: This is normal for Render free tier. Services sleep after 15 minutes.
- **Fix**: 
  1. Visit `https://your-service.onrender.com/health` to wake it up
  2. Wait 30-60 seconds
  3. Refresh frontend
  4. Or use the "Wake Backend" button in the UI

### CORS Error
- **Issue**: Frontend can't connect to backend
- **Solution**: Ensure `ALLOWED_ORIGINS=*` is set in Render environment variables

### Frontend Can't Find Backend
- **Issue**: Network error in frontend
- **Solution**: 
  1. Verify `VITE_API_URL` is set in Vercel (without `/api`)
  2. Ensure backend URL is correct
  3. Check backend is awake (visit `/health` endpoint)

### Query Returns Error
- **Issue**: "I encountered an error processing your request"
- **Solution**: 
  1. Check Render logs for detailed error
  2. Verify Azure OpenAI credentials are set correctly
  3. Check that all environment variables are set

---

## 🎓 Sample Queries

### Investment Analysis
- "Which clients are underweight in equities relative to their risk profile?"
- "Show me clients with ISA allowance still available this tax year"
- "Which clients have cash excess above 6 months expenditure?"

### Proactive Management
- "Which clients haven't had a review in over 12 months?"
- "Show me all business owners who might benefit from R&D tax credits"
- "Which clients have birthdays this month?"

### Compliance
- "Pull every recommendation I made to David Chen"
- "What documents am I still waiting for from clients?"
- "What did I promise to send the Jackson family?"

### Business Insights
- "What concerns did clients raise in meetings this month?"
- "Which services do my highest-value clients use most?"
- "Show me conversion rates by referral source"

### Follow-ups
- "Show me all open action items across my client base"
- "What follow-ups did I commit to that are now overdue?"
- "Which clients am I waiting on for information?"

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11, LangChain, LangGraph, Azure OpenAI
- **Frontend**: React 18, Vite, Tailwind CSS
- **LLM**: Azure OpenAI GPT-4o-mini
- **Deployment**: Render (backend), Vercel (frontend)
- **Architecture**: Agentic workflow with semantic tool matching

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

Built for the UK Financial Advisor Proactive Chatbot Challenge. Designed to help IFAs be more proactive and deliver better value to clients while meeting FCA Consumer Duty requirements.
