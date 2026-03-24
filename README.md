# Smart English Test-Prep Agent 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered adaptive learning system for Vietnamese high school students preparing for the National English Exam.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## 🎯 Overview

The Smart English Test-Prep Agent is an intelligent, adaptive learning platform designed specifically for Vietnamese students preparing for the National High School Graduation Exam (Kỳ thi tốt nghiệp THPT) in English.

### What Makes It Different?

- **✅ Truly Adaptive:** Failed concepts automatically get +40% more focus the next day
- **✅ Synthetic Questions:** AI generates brand new questions daily (no recycling)
- **✅ Bilingual Feedback:** Vietnamese explanations + English grammar rules
- **✅ Data-Driven:** Based on 2019-2025 exam pattern analysis
- **✅ University Counseling:** Predicts admission chances at Vietnamese universities

### Key Innovation: Adaptive Learning Loop

```
Day N: Student struggles with "Reported Speech" (40% accuracy)
    ↓
Adaptive weight: 1.00 → 1.40 (+40%)
    ↓
Day N+1: 3x more Reported Speech questions appear
    ↓
Student practices and improves: 40% → 55% → 69%
    ↓
Weight normalizes as mastery increases
```

---

## ✨ Features

### Core Learning System

| Feature | Description |
|---------|-------------|
| **Daily 15-Minute Tests** | Micro-learning sessions with 15 questions |
| **Adaptive Weighting** | Failed concepts get +40% weight increase |
| **Synthetic Question Generation** | AI creates unique questions (no duplicates) |
| **Real-time Feedback** | Instant Vietnamese/English explanations |
| **Streak System** | Gamification to maintain engagement |
| **Knowledge Graph** | Tracks mastery per concept |

### Assessment & Analytics

| Feature | Description |
|---------|-------------|
| **Bi-weekly Mega Tests** | 50-question full mock exams (60 minutes) |
| **Competency Maps** | Radar chart visualization (4 skill areas) |
| **Progress Trends** | Track improvement over time |
| **Weakness Analysis** | AI identifies learning gaps |

### University Counseling

| Feature | Description |
|---------|-------------|
| **Admission Probability** | Calculates chances based on predicted score |
| **University Database** | 10+ Vietnamese universities with benchmarks |
| **Recovery Plans** | Personalized study schedules for weak areas |
| **School Categorization** | Safe / Target / Reach recommendations |
| **Exam Countdown** | Study milestones based on exam date |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Dashboard │  │  Test UI  │  │ Feedback │  │ Charts  │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    FASTAPI BACKEND                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST API Layer (30+ endpoints)                     │  │
│  │  - Authentication (JWT)                               │  │
│  │  - Request Validation                                 │  │
│  │  - Error Handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  Routes    │  │  Middleware  │  │   Exception     │   │
│  └────────────┘  └─────────────┘  │   Handlers       │   │
│                                          └─────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    SERVICES LAYER                            │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │ RAG Engine    │ Daily Tests  │   Feedback   │Assessment│  │
│  │ (Exam Ingest) │ (Adaptive    │  (Root Cause  │(Mega    │  │
│  │ 2019-2025)   │  Generator)  │   Analysis)  │ Tests)  │  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Counseling Agent                        │   │
│  │       (University Admissions & Recovery Plans)       │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    DATABASE LAYER                             │
│  ┌──────────────┬──────────────┬──────────────────────────┐  │
│  │  Students    │  Questions   │   Knowledge Graph       │  │
│  │  Tests       │  Feedback    │   Universities          │  │
│  │  Competency  │  Benchmarks  │   Recovery Plans         │  │
│  └──────────────┴──────────────┴──────────────────────────┘  │
│                      PostgreSQL + PGVector                      │
└─────────────────────────────────────────────────────────────┘

External Services:
┌──────────────┐  ┌──────────────┐
│ Anthropic API │  │ PGVector     │
│  (Claude 3.5) │  │ (Embeddings)  │
└──────────────┘  └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+** with PGVector extension
- **Anthropic API Key** (for Claude)
- **Git**

### Backend Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd smart-english-testprep

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Set up environment
cp .env.example backend/.env
# Edit backend/.env with your DATABASE_URL and ANTHROPIC_API_KEY

# 4. Initialize database
createdb english_testprep
psql english_testprep -c "CREATE EXTENSION vector;"
psql english_testprep < database/schema.sql

# 5. Run backend server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Installation

```bash
# 1. Install Node.js dependencies
cd frontend
npm install

# 2. Set up environment
cp .env.example .env.local
# The default API URL is http://localhost:8000

# 3. Run development server
npm run dev
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health/ping

### Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/v1/health/ping

# Verify adaptive learning logic
python backend/scripts/simulate_learning.py 5
```

Expected simulation output:
```
✓ 17 adaptive weight adjustments detected
✓ Failed concepts received +40% weight increase
✓ Student mastery improved: 45% → 69% (+24%)
```
```

---

## 📁 Project Structure

```
smart-english-testprep/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                    # Configuration management
│   │   ├── database.py                 # Database utilities
│   │   ├── auth.py                     # JWT authentication
│   │   ├── main.py                     # FastAPI application
│   │   ├── models/                     # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── requests.py          # API request models
│   │   │   │   └── responses.py         # API response models
│   │   │   ├── core/
│   │   │   │   └── common.py           # Shared enums and base models
│   │   │   └── db/
│   │   │       ├── exam.py              # Exam dataclasses
│   │   │       ├── learning.py          # Learning dataclasses
│   │   │       └── student.py           # Student dataclasses
│   │   ├── routes/                     # API endpoints
│   │   │   ├── health.py
│   │   │   ├── students.py
│   │   │   ├── daily_tests.py
│   │   │   ├── feedback.py
│   │   │   ├── assessment.py
│   │   │   └── counseling.py
│   │   └── services/                   # Business logic
│   │       ├── __init__.py
│   │       ├── rag.py                   # RAG Engine (2019-2025 analysis)
│   │       ├── daily_tests.py          # Daily Test Generator
│   │       ├── feedback.py              # Feedback Engine
│   │       ├── assessment.py            # Mega Tests & Competency
│   │       └── counseling.py            # University Counseling
│   ├── scripts/                         # Utility scripts
│   │   ├── start_server.py              # Start FastAPI server
│   │   ├── generate_first_test.py       # Generate first test
│   │   └── simulate_learning.py        # Adaptive learning simulation
│   ├── database/
│   │   └── schema.sql                    # Database schema
│   ├── requirements.txt                 # Python dependencies
│   └── .env.example                     # Environment template
├── frontend/
│   ├── app/                            # Next.js App Router
│   │   ├── (auth)/                     # Authentication routes
│   │   │   └── login/
│   │   ├── (dashboard)/                # Protected dashboard routes
│   │   │   ├── page.tsx                # Dashboard home
│   │   │   ├── daily-test/             # Daily test interface
│   │   │   ├── analytics/              # Analytics & charts
│   │   │   └── counseling/             # University counseling
│   │   ├── layout.tsx                  # Root layout
│   │   └── globals.css                 # Global styles
│   ├── components/
│   │   ├── ui/                         # Reusable UI primitives
│   │   ├── shared/                     # Layout components
│   │   └── features/                   # Feature-specific components
│   ├── lib/
│   │   ├── api.ts                      # API client
│   │   └── utils.ts                    # Utilities
│   ├── types/
│   │   └── index.ts                    # TypeScript interfaces
│   ├── package.json                    # Node.js dependencies
│   ├── next.config.mjs                 # Next.js config
│   ├── tailwind.config.ts              # Tailwind CSS config
│   ├── tsconfig.json                   # TypeScript config
│   └── vercel.json                     # Vercel deployment config
├── database/
│   └── schema.sql                      # Database schema
├── .env.example                        # Root environment template
├── .gitignore
├── LICENSE
└── README.md                            # This file
```

---

## 📚 API Reference

### Base URL
```
Development: http://localhost:8000
Production: https://api.english-testprep.com
```

### Authentication

Most endpoints require JWT authentication:

```python
# Login
import requests

response = requests.post('http://localhost:8000/api/v1/students/login', json={
    'email': 'student@example.com',
    'password': 'password123'
})
token = response.json()['access_token']

# Use token in requests
headers = {'Authorization': f'Bearer {token}'}
requests.get('http://localhost:8000/api/v1/students/me', headers=headers)
```

### Key Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Health** | `/api/v1/health/ping` | GET | Health check |
| **Students** | `/api/v1/students/register` | POST | Register new student |
| | `/api/v1/students/login` | POST | Login & get JWT token |
| | `/api/v1/students/me` | GET | Get current student profile |
| | `/api/v1/students/progress` | GET | Get learning progress |
| **Daily Tests** | `/api/v1/daily-tests/generate` | POST | Generate 15-minute test |
| | `/api/v1/daily-tests/{id}/start` | POST | Start a test |
| | `/api/v1/daily-tests/{id}/submit` | POST | Submit answers |
| | `/api/v1/daily-tests/history` | GET | Get test history |
| **Feedback** | `/api/v1/feedback/generate` | POST | Get feedback for attempt |
| | `/api/v1/feedback/weak-concepts` | GET | Get weak concepts |
| **Assessment** | `/api/v1/assessment/status` | GET | Check mega test status |
| | `/api/v1/assessment/mega-test/generate` | POST | Generate 50-question test |
| | `/api/v1/assessment/competency-map/latest` | GET | Get competency map |
| **Counseling** | `/api/v1/counseling/report` | GET | Get counseling report |
| | `/api/v1/counseling/recovery-plan` | GET | Get recovery plan |
| | `/api/v1/counseling/exam-countdown` | GET | Get exam countdown |

### Response Examples

**Generate Daily Test:**
```bash
curl -X POST "http://localhost:8000/api/v1/daily-tests/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student_123", "test_date": "2025-03-22"}'
```

**Get Feedback:**
```bash
curl -X POST "http://localhost:8000/api/v1/feedback/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "question_id": "q_456",
    "selected_answer": "B",
    "time_spent_seconds": 30
  }'
```

**Get University Counseling:**
```bash
curl -X GET "http://localhost:8000/api/v1/counseling/report" \
  -H "Authorization: Bearer <token>"
```

---

### Base URL
```
Development: http://localhost:8000
Production: https://api.english-testprep.com
```

### Authentication

Most endpoints require JWT authentication:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/students/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/v1/students/me \
  -H "Authorization: Bearer <token>"
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/students/register` | POST | Register new student |
| `/api/v1/students/login` | POST | Login & get JWT token |
| `/api/v1/daily-tests/generate` | POST | Generate 15-minute test |
| `/api/v1/daily-tests/{id}/submit` | POST | Submit test answers |
| `/api/v1/feedback/generate` | POST | Get feedback for attempt |
| `/api/v1/assessment/mega-test/generate` | POST | Generate 50-question mega test |
| `/api/v1/counseling/report` | GET | Get university counseling report |

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## 🔧 Development

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py
```

### Code Style

```bash
# Format code
black app/ scripts/

# Check linting
flake8 app/ scripts/

# Type checking
mypy app/
```

### Adding New Features

1. **New Service:** Add to `app/services/`
2. **New Endpoint:** Add to `app/routes/`
3. **New Models:** Add to `app/models/`
4. **Update Tests:** Add to `tests/`

---

## 🚀 Deploy to Vercel (One-Click Deployment)

### Prerequisites

1. **GitHub Repository** - Push your code to GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free tier available)
3. **Anthropic API Key** - Get your key from [console.anthropic.com](https://console.anthropic.com)
4. **Database (Optional)** - For full functionality, set up PostgreSQL:
   - [Supabase](https://supabase.com) (Free tier available)
   - [Neon](https://neon.tech) (Serverless Postgres)
   - [AWS RDS](https://aws.amazon.com/rds/)

### Deployment Steps

#### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Connect GitHub Repository**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"
   - Import your GitHub repository
   - Root directory: `./` (leave empty for root)

2. **Configure Framework Preset**
   - Framework: **Next.js**
   - Root Directory: `./`
   - Build Command: (Auto-detected)

3. **Set Environment Variables**

   Go to **Settings → Environment Variables** and add:

   ```bash
   # Required
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ENVIRONMENT=production
   JWT_SECRET_KEY=generate-a-strong-random-string

   # Optional (for database features)
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - Get your Vercel URL: `https://your-project.vercel.app`

#### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from project root
cd smart-english-testprep
vercel

# Follow the prompts
# Set environment variables when asked
```

### Post-Deployment Configuration

1. **Verify Backend API**
   ```bash
   curl https://your-project.vercel.app/api/v1/health/ping
   ```

2. **Test Frontend**
   - Visit: `https://your-project.vercel.app`
   - Generate a test and verify AI feedback works

3. **Set Up Database (Optional)**
   - Add `DATABASE_URL` to Vercel environment variables
   - Run migrations if needed

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude AI API key | `sk-ant-xxx` |
| `ENVIRONMENT` | ✅ Yes | Deployment environment | `production` |
| `JWT_SECRET_KEY` | ✅ Yes | JWT signing secret | Generate random |
| `DATABASE_URL` | Optional | PostgreSQL connection | `postgresql://...` |
| `OPENAI_API_KEY` | Optional | For embeddings | `sk-...` |

### Troubleshooting

**Issue: Backend API returns 404**
- ✅ Check `vercel.json` has correct rewrites
- ✅ Verify `backend/api/index.py` exists
- ✅ Check Vercel build logs

**Issue: CORS errors**
- ✅ Root `vercel.json` handles routing
- ✅ Frontend uses relative `/api` path

**Issue: API timeout**
- ✅ Vercel serverless functions have 10s limit (Hobby)
- ✅ Upgrade to Pro for 60s limit

**Issue: Environment variables not working**
- ✅ Use `vercel env pull` to sync locally
- ✅ Redeploy after adding variables

### Development vs Production

| Feature | Development | Production (Vercel) |
|---------|-------------|---------------------|
| Backend | `http://localhost:8000` | Serverless Functions |
| Frontend | `http://localhost:3000` | `https://your-app.vercel.app` |
| API Calls | Absolute URL to localhost | Relative `/api` path |
| Database | Local PostgreSQL | Supabase/Neon/RDS |

### Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic)

---

## 🚢 Traditional Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t english-testprep-api .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  english-testprep-api
```

### Traditional Deployment

```bash
# Using Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker
```

### Systemd Service

```ini
[Unit]
Description=Smart English Test-Prep API
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/english-testprep/backend
Environment="PATH=/var/www/english-testprep/venv/bin"
ExecStart=/var/www/english-testprep/venv/bin/gunicorn app.main:app --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment Variables

Required for production:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
ANTHROPIC_API_KEY=sk-ant-xxxxxx
JWT_SECRET_KEY=change-this-in-production
APP_ENVIRONMENT=production
```

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write docstrings for all functions/classes
- Add type hints where appropriate
- Keep functions focused and modular

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Claude (Anthropic)** - AI reasoning and question generation
- **Vietnamese Ministry of Education** - Exam structure and benchmarks
- **Open Source Community** - Excellent tools and libraries

---

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Check the [API Documentation](backend/API_DOCUMENTATION.md)
- Review the [Setup Guide](backend/FASTAPI_START.md)

---

**Built with ❤️ for Vietnamese students**

*Empowering every student to achieve their English learning goals through AI*
