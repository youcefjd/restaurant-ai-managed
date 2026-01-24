# System Architecture

High-level overview of the Restaurant AI Platform architecture.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Customer                                  │
│                    (Phone Call)                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Retell AI                                   │
│         (Voice Platform - STT + TTS + Call Management)          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (:8000)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  /api/retell/chat (WebSocket)                              │ │
│  │  - Receives transcribed speech                             │ │
│  │  - Sends AI responses                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Conversation Handler                                      │ │
│  │  - Loads restaurant context (menu, hours)                  │ │
│  │  - Builds system prompt                                    │ │
│  │  - Calls LLM (Gemini/OpenAI)                              │ │
│  │  - Parses response (order items, intent)                   │ │
│  │  - Creates orders/bookings in database                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Gemini    │   │  Supabase   │   │   Stripe    │
│    (LLM)    │   │ (Database)  │   │ (Payments)  │
└─────────────┘   └─────────────┘   └─────────────┘


┌─────────────────────────────────────────────────────────────────┐
│               Restaurant Owner / Admin                           │
│                    (Web Browser)                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                React Frontend (:3000)                            │
│  - Dashboard, Orders, Menu, Analytics, Settings                 │
│  - Communicates with Backend via REST API                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (:8000)                         │
│  - /api/auth/* (Authentication)                                 │
│  - /api/restaurant/* (Order management)                         │
│  - /api/onboarding/* (Menu, settings)                          │
│  - /api/admin/* (Platform admin)                                │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Retell AI (Voice Platform)

Handles the voice interaction layer:
- Receives incoming phone calls
- Converts speech to text (STT)
- Connects to our backend via WebSocket for AI responses
- Converts text responses to speech (TTS)
- Manages call lifecycle

**Integration point:** `/api/retell/chat` WebSocket endpoint

### 2. FastAPI Backend

Python backend handling all business logic:
- REST API for frontend (authentication, orders, menus, admin)
- WebSocket endpoint for Retell AI real-time conversation
- Conversation handler that orchestrates AI responses
- Integration with external services (Stripe, Google Maps)

### 3. Conversation Handler

Core AI logic (`backend/services/conversation_handler.py`):
- Loads restaurant-specific context (menu, hours, tables)
- Builds dynamic system prompt from template
- Calls LLM (Gemini or OpenAI)
- Extracts structured data from AI responses
- Creates orders and bookings in database

### 4. LLM Service

Abstraction layer for language models (`backend/services/llm_service.py`):
- Primary: Google Gemini
- Fallback: OpenAI GPT-4
- Supports streaming responses
- Handles provider failover

### 5. Supabase (Database)

PostgreSQL database via Supabase:
- Stores all application data
- Restaurant accounts, menus, orders, bookings
- Uses service role key for backend access
- Row Level Security (RLS) policies for additional security

### 6. React Frontend

TypeScript React application:
- Vite build tool
- TanStack React Query for data fetching
- Tailwind CSS for styling
- Restaurant dashboard and admin dashboard

## Data Flow: Voice Order

1. Customer calls Retell-provisioned phone number
2. Retell connects to backend WebSocket with call metadata
3. Backend identifies restaurant from phone number
4. Customer speaks, Retell transcribes and sends text
5. Conversation Handler:
   - Loads restaurant menu and context
   - Builds system prompt with menu data
   - Sends to Gemini LLM
   - Receives AI response with intent and order items
6. Backend returns response text to Retell
7. Retell speaks response to customer
8. Conversation continues until order complete
9. Backend creates order in Supabase
10. Call ends, transcript saved

## Multi-Tenancy

Each restaurant is isolated:
- Unique phone number per restaurant
- Separate menu, hours, and settings
- All queries filtered by `account_id`
- AI only knows that restaurant's data

## Key Integration Points

| Service | Purpose | Config |
|---------|---------|--------|
| Retell AI | Voice calls, STT/TTS | `RETELL_API_KEY` |
| Supabase | Database | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |
| Google Gemini | LLM responses | `GOOGLE_AI_API_KEY` |
| OpenAI | LLM fallback | `OPENAI_API_KEY` |
| Stripe Connect | Payments | `STRIPE_*` keys |
| Google Maps | Hours import | `GOOGLE_MAPS_API_KEY` |

---

**Related:**
- [Technology Stack](./technology-stack.md)
- [Voice AI](./voice-ai.md)
- [Database](./database.md)
