# Getting Started

Quick guide to set up and run the Restaurant AI Platform locally.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Supabase account** - [supabase.com](https://supabase.com)
- **Google AI API key** - [aistudio.google.com](https://aistudio.google.com)
- **Retell AI account** - [retellai.com](https://www.retellai.com) (for voice features)

## Quick Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd restaurant-ai-managed
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see Environment Variables)

# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

## Required Environment Variables

Create a `.env` file in the project root with at minimum:

```bash
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Authentication (Required)
JWT_SECRET_KEY=your-secret-key-here

# AI (Required for conversation features)
GOOGLE_AI_API_KEY=your-google-ai-key
```

See [Environment Variables](./environment-variables.md) for full configuration.

## Verify Setup

1. Backend health check: `curl http://localhost:8000/health`
2. Frontend loads at http://localhost:3000
3. API docs accessible at http://localhost:8000/api/docs

## Next Steps

- [Set up Retell AI](./voice-ai.md) for voice features
- [Configure Stripe](./environment-variables.md#payments) for payments
- Review [Architecture](./architecture.md) for system overview

---

**Related:**
- [Environment Variables](./environment-variables.md)
- [Architecture](./architecture.md)
- [Technology Stack](./technology-stack.md)
