# ⚡ AI-Driven DevOps Orchestrator

> An intelligent automation platform that connects GitHub, Jira, and Slack using AI agents — automatically processing events, creating tickets, and dispatching notifications in real time.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.76-purple)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 What It Does

When a developer pushes code to GitHub, this system:

1. **Receives** the webhook event and verifies its authenticity
2. **Summarizes** the commit using an LLM (Groq / LLaMA 3)
3. **Creates** a Jira ticket automatically with an AI-generated title
4. **Sends** a rich Slack notification to the team channel
5. **Updates** the live dashboard in real time via WebSocket

All of this happens in **under 15 seconds** — without any human intervention.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Port 3000)                  │
│   login  │  register  │  projects  │  api-setup  │ dashboard │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend (Port 8000)                │
│  /auth/*  │  /api/projects/*  │  /webhooks/*  │  /ws        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    AI Agent Pipeline (LangGraph)              │
│  Summarize → Router → Jira Creator → Slack Notifier → Final  │
└──────────┬─────────────────────────────────────┬────────────┘
           │                                     │
    ┌──────▼──────┐                    ┌─────────▼────────┐
    │  Groq API   │                    │  SQLite Database  │
    │  (LLaMA 3)  │                    │  users, projects  │
    └─────────────┘                    │  stats, otp_codes │
                                       └──────────────────┘
```

---

## 🚀 Features

### 🔐 Authentication & Security
- User registration with **email OTP verification** (Gmail SMTP)
- **Strong password enforcement** — 8+ chars, upper, lower, number, special
- JWT-based authentication with 24-hour token expiry
- Password reset via email OTP
- HMAC-SHA256 webhook signature verification

### 📁 Multi-Project Management
- Create unlimited projects per user
- Each project has **isolated API credentials** (GitHub, Slack, Jira)
- Edit project name/description at any time
- GitHub-style **type-to-confirm** deletion dialog

### 🤖 AI Agent Pipeline
- **LangGraph** state machine with 5 nodes
- **LLM-powered** event summarization (Groq / LLaMA 3.1)
- Intelligent event routing based on event type
- Automatic Jira ticket creation with AI-generated titles
- Rich Slack card notifications with commit details

### 📊 Real-time Dashboard
- Live activity feed via **WebSocket**
- Git Events, Jira Tickets, Slack Alerts counters
- Stats persist across logout/login sessions
- Auto Jira Tickets panel with priority filtering

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JavaScript, Tailwind CDN |
| Backend | FastAPI, Uvicorn, Python 3.10+ |
| AI Framework | LangGraph 0.2.76, LangChain Core |
| LLM Provider | Groq API (llama-3.1-8b-instant) |
| Database | SQLite, SQLAlchemy 2.0, Pydantic v2 |
| Auth | JWT (python-jose), Passlib (bcrypt) |
| Email | Gmail SMTP (smtplib SSL) |
| Integrations | GitHub REST API, Jira REST API v3, Slack Web API |
| Real-time | WebSocket (FastAPI native) |

---

## 📋 Prerequisites

- Python 3.10+
- Git
- ngrok (for GitHub webhook testing)
- Accounts: GitHub, Jira (Atlassian), Slack, Groq

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/devops-orchestrator.git
cd devops-orchestrator
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# AI
GROQ_API_KEY=gsk_your_groq_key
GROQ_MODEL=llama-3.1-8b-instant

# GitHub
GITHUB_TOKEN=ghp_your_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your_signing_secret
DEFAULT_SLACK_CHANNEL=#automation-alert

# Jira
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@email.com
JIRA_API_TOKEN=your_jira_token
JIRA_PROJECT_KEY=SCRUM

# Email OTP
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your16charapppassword
```

### 5. Start the backend
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Start the frontend
```bash
cd frontend
python -m http.server 3000 --bind 127.0.0.1
```

### 7. Expose webhook endpoint (development)
```bash
ngrok http 8000
```
Add the ngrok URL as your GitHub webhook:
`https://your-ngrok-url.ngrok.io/webhooks/github`

---

## 📁 Project Structure

```
devops_orchestrator/
│
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # Login, register, verify, reset
│   │       ├── projects.py      # Project CRUD
│   │       ├── credentials.py   # Per-project API keys
│   │       ├── stats.py         # Dashboard statistics
│   │       ├── github.py        # GitHub webhook handler
│   │       ├── slack.py         # Slack webhook handler
│   │       └── jira.py          # Jira routes
│   │
│   ├── agent/
│   │   ├── graph.py             # LangGraph pipeline definition
│   │   ├── state.py             # AgentState TypedDict
│   │   └── nodes/
│   │       ├── summarize_node.py
│   │       ├── router_node.py
│   │       ├── jira_creator_node.py
│   │       ├── slack_notifier_node.py
│   │       └── finalize_node.py
│   │
│   ├── core/
│   │   ├── auth.py              # JWT get_current_user
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy engine & init_db
│   │   └── websocket.py         # ConnectionManager
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── user_credentials.py
│   │   ├── otp.py
│   │   └── stats.py
│   │
│   ├── services/
│   │   └── email_service.py     # Gmail SMTP OTP sender
│   │
│   └── main.py                  # FastAPI app factory
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── verify-email.html
│   ├── reset-password.html
│   ├── projects.html
│   ├── api-setup.html
│   └── index.html               # Main dashboard
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔄 Event Flow

```
GitHub Push Event
       │
       ▼
POST /webhooks/github
       │
       ▼
Verify HMAC-SHA256 Signature
       │
       ▼
Queue Async Processing
       │
       ▼
[LangGraph Pipeline]
       │
   Summarize ──► LLM generates commit summary
       │
   Router ────► Decides: create_jira_issue
       │
   Jira ──────► Creates ticket: "SCRUM-XX: ..."
       │
   Slack ─────► Sends rich card to #automation-alert
       │
   Finalize ──► Saves stats + broadcasts to WebSocket
       │
       ▼
Dashboard updates in real time ✅
```

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/verify-email` | Verify OTP code |
| POST | `/auth/login` | Login and get JWT |
| POST | `/auth/forgot-password` | Send reset OTP |
| POST | `/auth/reset-password` | Set new password |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project |
| PATCH | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/projects/{id}/credentials` | Save API keys |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/github` | GitHub webhook receiver |
| POST | `/webhooks/slack` | Slack webhook receiver |

### WebSocket
| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WS | `/ws` | Real-time dashboard updates |

---

## 🗄️ Database Schema

```sql
users              -- User accounts (email, password_hash, is_active)
user_credentials   -- Legacy per-user API keys
projects           -- User projects (name, description, user_id)
project_credentials -- Per-project API keys (github, slack, jira)
otp_codes          -- Email verification tokens (6-digit, 10min expiry)
stats              -- Per-project event counters
activity_log       -- Per-project event history
```

---

## 🧪 Running Tests

```bash
pytest backend/tests/ -v
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Inam Ur Rehman**

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) — AI agent framework
- [Groq](https://groq.com/) — Ultra-fast LLM inference
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework
