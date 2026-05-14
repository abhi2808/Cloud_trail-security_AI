# 🛡️ CloudTrail AI Investigator

**Natural language security investigation tool for AWS CloudTrail logs.**

Ask security questions in plain English — get investigator-style answers instantly.

> *"Who terminated EC2 instances in the last 24 hours?"*
> *"Show all root user activity this week"*
> *"Who modified security groups today?"*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────────────┐    │
│  │ InputBar │→│ Zustand  │→│  Axios API │→│  ChatWindow    │    │
│  │          │ │  Store   │ │ (X-App-Key)│ │  + EventCards  │    │
│  └──────────┘ └──────────┘ └──────┬─────┘ └────────────────┘    │
│                                   │                             │
└───────────────────────────────────┼─────────────────────────────┘
                                    │ POST /api/query
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                         │
│                                                                 │
│  ┌──────────────────┐   ┌────────────────┐   ┌──────────────┐   │
│  │  Auth Middleware │   │  Query Route   │   │  CORS        │   │
│  │  (X-App-Key)     │   │ POST /api/query│   │  Middleware  │   │
│  └──────────────────┘   └───────┬────────┘   └──────────────┘   │
│                                 │                               │
│                    ┌────────────┼─────────────┐                 │
│                    ▼            ▼             ▼                 │
│           ┌──────────┐  ┌─────────────┐ ┌──────────────┐        |
│           │  AI SVC  │  │ CloudTrail  │ │  Event       │        │
│           │(Gemini/  │  │ SVC (boto3) │ │  Taxonomy    │        │
│           │ Groq)    │  │             │ │              │        │
│           └────┬─────┘  └─────┬───────┘ └──────────────┘        │
│                │              │                                 │
└────────────────┼──────────────┼─────────────────────────────────┘
                 │              │
        ┌────────┴──┐     ┌─────┴──────┐
        │ Gemini /  │     │   AWS      │
        │ Groq API  │     │ CloudTrail │
        └───────────┘     │ API        │
                          └────────────┘
```

### Request Flow

1. **User** types a question in plain English
2. **AI Service (Step 1)** converts natural language → `ExtractedIntent` (event name, user, time range, etc.)
3. **CloudTrail Service** calls `LookupEvents` with extracted parameters
4. **AI Service (Step 2)** interprets raw CloudTrail JSON → human-readable security analysis
5. **Frontend** displays the answer + collapsible raw event table

---

## 📋 Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| AWS Account | With CloudTrail enabled |
| AI API Key | Gemini Pro or Groq (llama3-70b) |

---

## 🔐 IAM Setup

Create a read-only IAM user for CloudTrail access:

### 1. Create IAM User

```
User name: cloudtrail-investigator-readonly
Access type: Programmatic access only (no console)
```

### 2. Attach Inline Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrail",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:ListTrails"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Save the Access Key ID and Secret Access Key

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd CloudTrail_APP
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```

Edit `backend/.env` with your actual values:

```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJal...
AWS_REGION=us-east-1
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
AI_PROVIDER=gemini
APP_SECRET_KEY=my-super-secret-key-123
CLIENT_URL=http://localhost:5173
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env from example
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_SECRET_KEY=my-super-secret-key-123
VITE_AWS_REGION=us-east-1
```

> ⚠️ `VITE_APP_SECRET_KEY` must match `APP_SECRET_KEY` in the backend `.env`

### 4. Install Root Dependencies

```bash
cd ..  # back to root
npm install
```

### 5. Run Both Servers

```bash
npm run dev
```

Or run individually:

```bash
# Terminal 1 — Backend
npm run backend

# Terminal 2 — Frontend
npm run frontend
```

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

---

## 🎯 Demo Queries

| Query | What It Does |
|---|---|
| "Who terminated EC2 instances in the last 24 hours?" | Looks up `TerminateInstances` events in the last day |
| "Show all IAM user creation events this week" | Searches for `CreateUser` events in the last 7 days |
| "Who modified security groups today?" | Finds `AuthorizeSecurityGroupIngress`, `RevokeSecurityGroupIngress` events |
| "Show all root user activity in the last 7 days" | Filters events by root username |
| "Who created new AWS access keys this month?" | Looks up `CreateAccessKey` events |
| "Any suspicious console logins?" | Checks `ConsoleLogin` events for missing MFA, external IPs, off-hours |

### Expected Output

For *"Who terminated EC2 instances in the last 24 hours?"*:

```
A total of 3 EC2 instances were terminated in the last 24 hours.

Key findings:
• 15-Apr-2026 14:32:10 IST — user "deploy-bot" (arn:aws:iam::123456:user/deploy-bot) 
  terminated instance from IP 10.0.1.50 in us-east-1
• 15-Apr-2026 11:05:44 IST — user "abhinav" (arn:aws:iam::123456:user/abhinav) 
  terminated instance from IP 203.0.113.42 in us-east-1
  ⚠️ External IP address detected

🔍 Total matching events found: 3
```

---

## 📁 Project Structure

```
CloudTrail_APP/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── query.py         ← POST /api/query, GET /api/health
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py            ← Pydantic BaseSettings
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai.py                ← Gemini/Groq intent + interpretation
│   │   │   ├── cloudtrail.py        ← boto3 LookupEvents wrapper
│   │   │   └── event_taxonomy.py    ← AWS event name taxonomy
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── query.py             ← Pydantic schemas
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py              ← X-App-Key validation
│   │   ├── __init__.py
│   │   └── main.py                  ← FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── InputBar.jsx
│   │   │   ├── EventCard.jsx
│   │   │   ├── ThinkingIndicator.jsx
│   │   │   └── SuggestedQueries.jsx
│   │   ├── constants/
│   │   │   └── demoQueries.js
│   │   ├── lib/
│   │   │   └── api.js
│   │   ├── pages/
│   │   │   └── HomePage.jsx
│   │   ├── store/
│   │   │   └── chatStore.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── package.json                     ← Root: concurrently runs both servers
├── .gitignore
└── README.md
```

---

## 🔑 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Two-step AI flow** | Step 1 extracts structured params, Step 2 interprets events — separating concerns for better accuracy |
| **Gemini + Groq fallback** | Gemini Pro for primary; Groq (llama3-70b) as a cost-effective backup |
| **Client-side filtering** | CloudTrail `LookupEvents` only supports ONE attribute per call; extra filters applied in Python |
| **Exponential backoff** | CloudTrail API has aggressive rate limits; retries prevent flaky failures |
| **X-App-Key middleware** | Lightweight API authentication without full OAuth for a PoC |
| **IST timestamps** | Designed for Indian security teams — all times displayed in UTC+5:30 |

---

## 🛣️ Future Roadmap

- [ ] **Swap Gemini → AWS Bedrock** — Keep AI inference within AWS boundary
- [ ] **CloudTrail Lake SQL** — Use Athena/Lake for richer queries beyond 90-day LookupEvents limit
- [ ] **GuardDuty Integration** — Correlate CloudTrail findings with GuardDuty alerts
- [ ] **Multi-Account Support** — Investigate across AWS Organizations member accounts
- [ ] **Export Reports** — Generate PDF/CSV investigation reports
- [ ] **Saved Investigations** — Persist query history and bookmark important findings
- [ ] **Real-time Streaming** — WebSocket-based live event monitoring
- [ ] **Role-based Access** — Full JWT/OAuth authentication with team management

---

## ⚠️ Security Notes

- **No credentials on the frontend** — AWS keys stay backend-only
- **Read-only AWS access** — IAM policy restricted to `cloudtrail:Lookup*` and `Get*`
- **No write APIs** — Backend never calls any AWS write/modify action
- **App key auth** — All API endpoints require `X-App-Key` header validation
- **CORS restricted** — Only the configured `CLIENT_URL` is allowed

---

## 📄 License

MIT License — feel free to use for internal security tooling.
