# Agentic Chaser

LLM-Powered Autonomous Document & LOA Management System for UK Financial Advisors

## Overview

Agentic Chaser is an intelligent system that autonomously identifies and prioritizes chase items (LOAs, documents, post-advice items) for financial advisors, reducing administrative burden and enabling advisors to focus on client relationships and advice.

## Key Features

- **Autonomous Chasing**: Intelligently identifies LOAs, documents, and post-advice items that need chasing
- **Natural Language Queries**: Ask questions in plain English to get insights about clients, investments, compliance, and chasing
- **Agentic Architecture**: Uses LangGraph with Azure OpenAI for intelligent tool selection based on semantic descriptions
- **Prioritization**: Automatically prioritizes chase items based on urgency, client value, and case importance
- **Provider Performance Analysis**: Tracks provider response times and reliability

## Tech Stack

- **Backend**: FastAPI, Python, LangChain, LangGraph, Azure OpenAI
- **Frontend**: React, Vite, Tailwind CSS
- **Architecture**: Agentic workflow with semantic tool matching

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables:
```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

Run:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /api/insights/natural-language?query=...` - Process natural language queries
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/chases/active` - Get active chases

## License

MIT
