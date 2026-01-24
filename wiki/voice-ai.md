# Voice AI System

The platform uses **Retell AI** to handle voice interactions with customers.

## Overview

Retell AI provides an all-in-one voice platform that:
- Manages inbound phone calls
- Handles speech-to-text (STT)
- Handles text-to-speech (TTS)
- Connects to our custom LLM via WebSocket

Our backend provides the conversation intelligence through the LLM integration.

## Architecture

```
Customer Phone Call
        │
        ▼
   Retell AI
        │ WebSocket (real-time)
        ▼
Backend /api/retell/chat
        │
        ▼
Conversation Handler
        │
        ├──► Load Restaurant Context
        ├──► Build System Prompt
        ├──► Call Gemini LLM
        └──► Return Response
        │
        ▼
   Retell AI
        │ TTS
        ▼
Customer Hears Response
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/api/retell_voice.py` | Retell webhook and WebSocket endpoints |
| `backend/services/retell_service.py` | Retell API client |
| `backend/services/conversation_handler.py` | AI conversation logic |
| `VOICE_AGENT_SYSTEM_PROMPT.md` | System prompt template |

## Endpoints

### WebSocket: `/api/retell/chat`

Real-time conversation endpoint. Retell connects here to exchange messages.

**Flow:**
1. Retell opens WebSocket on call start
2. Sends transcribed customer speech
3. Receives AI response text
4. Continues until call ends

### HTTP: `/api/retell/webhook`

Receives call lifecycle events from Retell:
- `call_started` - New inbound call
- `call_ended` - Call completed
- `call_analyzed` - Post-call analysis available

## Retell Service

Located at `backend/services/retell_service.py`, provides:

### Agent Management
```python
retell_service.create_agent(name, voice_id, llm_websocket_url)
retell_service.get_agent(agent_id)
retell_service.update_agent(agent_id, **kwargs)
retell_service.list_agents()
retell_service.delete_agent(agent_id)
```

### Phone Number Management
```python
retell_service.create_phone_number(area_code, agent_id)
retell_service.import_phone_number(phone, twilio_sid, twilio_token, agent_id)
retell_service.update_phone_number(phone_number, agent_id)
retell_service.list_phone_numbers()
```

### Call Management
```python
retell_service.create_phone_call(from_number, to_number, agent_id)
retell_service.get_call(call_id)
retell_service.list_calls(filter_criteria)
```

### SMS
```python
retell_service.create_sms_chat(from_number, to_number, agent_id)
retell_service.send_sms(from_number, to_number, message)
```

## Setup

### 1. Get Retell API Key

Sign up at [retellai.com](https://www.retellai.com) and get your API key.

### 2. Configure Environment

```bash
RETELL_API_KEY=your_retell_api_key_here
```

### 3. Create Agent

Create a Retell agent configured to use your backend's WebSocket URL:

```python
agent = await retell_service.create_agent(
    name="Restaurant Assistant",
    voice_id="11labs-Adrian",
    llm_websocket_url="wss://your-domain.com/api/retell/chat"
)
```

### 4. Get Phone Number

Either purchase from Retell or import existing Twilio number:

```python
# Purchase new
phone = await retell_service.create_phone_number(
    area_code=415,
    agent_id=agent["agent_id"]
)

# Or import Twilio number
phone = await retell_service.import_phone_number(
    phone_number="+14155551234",
    twilio_account_sid="AC...",
    twilio_auth_token="...",
    agent_id=agent["agent_id"]
)
```

## Voice Persona

The AI persona is defined in `VOICE_AGENT_SYSTEM_PROMPT.md`. Key characteristics:

- Warm and polite
- Uses courteous phrases ("thank you", "please", "sorry")
- Short responses (under 20 words when possible)
- One question at a time
- Natural acknowledgments before proceeding

## Webhook Verification

Retell signs webhooks with HMAC-SHA256. Verify with:

```python
is_valid = retell_service.verify_webhook_signature(
    payload=request_body_bytes,
    signature=headers["X-Retell-Signature"]
)
```

## Transcript Storage

After calls end, transcripts are saved to the `transcripts` table via `transcript_service.py`.

---

**Related:**
- [Conversation Handler](./conversation-handler.md)
- [Voice Agent Prompt](./voice-agent-prompt.md)
- [Architecture](./architecture.md)
