# Restaurant AI Platform - Wiki

A multi-tenant SaaS platform enabling restaurants to automate phone ordering through AI-powered voice agents.

## Quick Navigation

### Getting Started
- [Quick Start Guide](./getting-started.md) - Setup and run the project
- [Environment Variables](./environment-variables.md) - Configuration reference

### Architecture
- [System Architecture](./architecture.md) - High-level system overview
- [Technology Stack](./technology-stack.md) - Current technologies in use

### Core Systems
- [Voice AI System](./voice-ai.md) - Retell AI integration and voice call flow
- [Database](./database.md) - Supabase schema and data models
- [Authentication](./authentication.md) - JWT-based auth system

### Backend
- [API Overview](./api-overview.md) - REST API structure
- [API Reference](./api-reference.md) - Detailed endpoint documentation
- [Services](./services.md) - Business logic services

### Frontend
- [Frontend Architecture](./frontend.md) - React application structure
- [Pages & Components](./frontend-pages.md) - UI components overview

### AI & Conversation
- [Conversation Handler](./conversation-handler.md) - AI conversation logic
- [Voice Agent Prompt](./voice-agent-prompt.md) - System prompt template

### Development
- [Development Practices](./development-practices.md) - Code standards and workflows

### Specifications (Functional Reference)
- [Specification Index](./specifications/SPECIFICATION_INDEX.md) - Overview of all specs
- [Functional Specification](./specifications/FUNCTIONAL_SPECIFICATION.md) - Complete feature specification
- [AI Conversation Spec](./specifications/AI_CONVERSATION_SPECIFICATION.md) - Voice/SMS conversation flows
- [Data Models & Workflows](./specifications/DATA_MODELS_AND_WORKFLOWS.md) - Entity definitions and business logic

---

## Platform Overview

### What It Does

**For Restaurant Owners:**
- AI phone assistant that answers calls 24/7
- Takes takeout/delivery orders via natural conversation
- Handles table reservations
- Real-time order management dashboard
- Menu management with instant availability updates
- Analytics and revenue tracking

**For Platform Admins:**
- Multi-restaurant management
- Commission and subscription management
- Platform-wide analytics
- Restaurant onboarding oversight

**For Customers:**
- Call restaurant and speak naturally to AI
- Place orders by phone
- Make reservations by phone
- Receive SMS confirmations

### Current Tech Stack

| Component | Technology |
|-----------|------------|
| Voice AI | **Retell AI** |
| Database | **Supabase** (PostgreSQL) |
| LLM | **Google Gemini** (OpenAI fallback) |
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript + Vite |
| Payments | Stripe Connect |
| Styling | Tailwind CSS |

### Key Branch

Current development: `voice/retell-ai`

---

## Project Structure

```
restaurant-ai-managed/
├── backend/
│   ├── api/              # API route handlers
│   ├── services/         # Business logic
│   ├── core/             # Utilities and config
│   ├── main.py           # FastAPI app entry
│   └── database.py       # Supabase connection
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # UI components
│   │   ├── contexts/     # React contexts
│   │   └── services/     # API client
│   └── vite.config.ts
├── specifications/       # Functional specs
├── wiki/                 # This documentation
└── VOICE_AGENT_SYSTEM_PROMPT.md
```

---

## Status

This wiki reflects the current state of the codebase as of January 2026. The platform uses:

- **Retell AI** for voice (replacing older Twilio+Deepgram+ElevenLabs stack)
- **Supabase** for database (replacing SQLite/SQLAlchemy)
- **Google Gemini** for LLM (with OpenAI fallback)

Older documentation files in the root directory may reference deprecated technologies.
