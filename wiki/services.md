# Backend Services

Business logic is organized into service modules in `backend/services/`.

## Service Architecture

```
API Route
    │
    ▼
Service Layer
    │
    ├──► Database (Supabase)
    ├──► External APIs (Retell, Stripe, etc.)
    └──► Other Services
```

## Core Services

### Conversation Handler

**File:** `backend/services/conversation_handler.py`

The brain of the voice AI system. Processes customer messages and generates responses.

**Responsibilities:**
- Load restaurant context (menu, hours, tables)
- Build dynamic system prompt
- Call LLM (Gemini/OpenAI)
- Parse AI response for structured data
- Create orders/bookings when confirmed

**Key function:**
```python
async def process_message(
    message: str,
    customer_phone: str,
    restaurant_phone: str,
    conversation_history: List[Dict],
    db: SupabaseDB
) -> Dict:
    # Returns structured response with intent, message, order items, etc.
```

### LLM Service

**File:** `backend/services/llm_service.py`

Abstraction for language model calls.

**Providers:**
- Primary: Google Gemini
- Fallback: OpenAI GPT-4

**Key methods:**
```python
# Streaming response
async for chunk in llm_service.generate_response(
    system_prompt="...",
    user_message="...",
    conversation_history=[...]
):
    yield chunk

# Complete response
response = await llm_service.generate_complete_response(...)
```

### Retell Service

**File:** `backend/services/retell_service.py`

Client for Retell AI API.

**Capabilities:**
- Agent management (create, update, delete)
- Phone number management
- Call management
- SMS capabilities

See [Voice AI](./voice-ai.md) for details.

### Transcript Service

**File:** `backend/services/transcript_service.py`

Manages conversation transcript storage.

**Key functions:**
```python
save_transcript(
    account_id: int,
    customer_phone: str,
    conversation_id: str,
    messages: List[Dict],
    outcome: str,
    order_id: Optional[int]
)
```

### Stripe Connect Service

**File:** `backend/services/stripe_connect_service.py`

Handles Stripe Connect marketplace payments.

**Key features:**
- Restaurant onboarding to Stripe Express
- Payment processing with automatic commission split
- Balance queries
- Dashboard link generation

```python
# Process payment with commission split
await stripe_connect_service.create_payment_intent(
    order_id=1,
    amount_cents=5000,
    restaurant_stripe_account_id="acct_xxx",
    commission_rate=10.0
)
```

### Booking Service

**File:** `backend/services/booking_service.py`

Handles table reservation logic.

**Key features:**
- Availability checking
- Conflict prevention
- Automatic table assignment (smallest suitable table)

## Voice Services (Alternative Stack)

These services exist for the alternative voice pipeline (not currently primary):

### Voice Service

**File:** `backend/services/voice_service.py`

Twilio TwiML generation for voice calls.

### Deepgram Service

**File:** `backend/services/deepgram_service.py`

Speech-to-text with Deepgram.

### ElevenLabs Service

**File:** `backend/services/elevenlabs_service.py`

Text-to-speech with ElevenLabs.

### OpenAI TTS Service

**File:** `backend/services/openai_tts_service.py`

Text-to-speech with OpenAI.

## Utility Services

### Google Maps Service

**File:** `backend/services/google_maps_service.py`

Import restaurant operating hours from Google Business.

### Menu Parser

**File:** `backend/services/menu_parser.py`

Parse menus from uploaded files (CSV, PDF).

### Payment Service

**File:** `backend/services/payment_service.py`

General payment processing logic.

### SMS Service

**File:** `backend/services/sms_service.py`

Send SMS notifications (order confirmations, etc.).

### Audit Service

**File:** `backend/services/audit_service.py`

Audit logging for important actions.

## Service Initialization

Most services are instantiated as module-level singletons:

```python
# In service file
llm_service = LLMService()

# In API routes
from backend.services.llm_service import llm_service
```

Services check for required environment variables and set `is_enabled()` accordingly.

---

**Related:**
- [Conversation Handler](./conversation-handler.md)
- [Voice AI](./voice-ai.md)
- [API Reference](./api-reference.md)
