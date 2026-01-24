# Technology Stack

Current technologies used in the Restaurant AI Platform.

## Backend

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | FastAPI | Latest | REST API and WebSocket server |
| Language | Python | 3.10+ | Backend language |
| Server | Uvicorn | Latest | ASGI server |
| Validation | Pydantic | v2 | Request/response schemas |
| HTTP Client | httpx | Latest | Async HTTP requests |

## Frontend

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | React | 18.2 | UI library |
| Language | TypeScript | Latest | Type-safe JavaScript |
| Build Tool | Vite | 7.x | Fast dev server and bundler |
| Styling | Tailwind CSS | 3.4 | Utility-first CSS |
| Routing | React Router | v6 | Client-side routing |
| Data Fetching | TanStack Query | v5 | Server state management |
| HTTP Client | Axios | Latest | API requests |
| Charts | Recharts | Latest | Analytics visualizations |
| Icons | Lucide React | Latest | Icon library |
| Animations | Framer Motion | Latest | UI animations |

## Database

| Service | Purpose |
|---------|---------|
| **Supabase** | PostgreSQL database hosting |
| PostgREST | Auto-generated REST API |
| Row Level Security | Access control policies |

## Voice AI

| Service | Purpose |
|---------|---------|
| **Retell AI** | Primary voice platform (STT + TTS + call management) |
| WebSocket | Real-time conversation with custom LLM |

### Alternative Voice Stack (Available but not primary)

| Service | Purpose |
|---------|---------|
| Twilio | Phone number management |
| Deepgram | Speech-to-text |
| ElevenLabs | Text-to-speech |

## AI / LLM

| Service | Purpose |
|---------|---------|
| **Google Gemini** | Primary LLM for conversation |
| OpenAI GPT-4 | Fallback LLM |

Default model: `gemini-2.0-flash`

## Payments

| Service | Purpose |
|---------|---------|
| **Stripe Connect** | Marketplace payments with commission splitting |
| Payment Intents | Order payment processing |
| Express Accounts | Restaurant payouts |

## Optional Services

| Service | Purpose |
|---------|---------|
| Google Maps API | Import operating hours from Google Business |

## Development Tools

| Tool | Purpose |
|------|---------|
| dotenv | Environment variable management |
| pytest | Backend testing |
| ESLint | Frontend linting |
| TypeScript | Type checking |

## Infrastructure Considerations

### Development
- Backend: Uvicorn with hot reload
- Frontend: Vite dev server with proxy to backend
- Database: Supabase cloud instance

### Production
- Backend: Uvicorn or Gunicorn with multiple workers
- Frontend: Static build served via CDN or Nginx
- Database: Supabase managed PostgreSQL
- SSL: Required for Retell webhooks

---

**Related:**
- [Architecture](./architecture.md)
- [Getting Started](./getting-started.md)
