# Environment Variables

Complete reference for all environment variables used by the platform.

## Required Variables

### Supabase Database

```bash
# Get from: https://supabase.com/dashboard/project/_/settings/api
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here
```

### Authentication

```bash
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## AI / LLM

### Google Gemini (Primary)

```bash
# Get from: https://aistudio.google.com/
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_MODEL=gemini-2.0-flash  # Optional, defaults to gemini-2.0-flash
```

### OpenAI (Fallback)

```bash
# Get from: https://platform.openai.com/
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # Optional
```

### LLM Provider Selection

```bash
# "gemini" (default) or "openai"
LLM_PROVIDER=gemini
```

## Voice AI

### Retell AI (Recommended)

Retell AI handles speech-to-text and text-to-speech automatically.

```bash
# Get from: https://www.retellai.com/
RETELL_API_KEY=your_retell_api_key_here
```

### Twilio (For Phone Numbers)

If using Twilio phone numbers with Retell:

```bash
# Get from: https://www.twilio.com/console
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
```

### Alternative Voice Stack (Not Currently Active)

These are available but the platform currently uses Retell AI:

```bash
# Deepgram STT
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=cgSgspJ2msm6clMCkdW9
ELEVENLABS_MODEL=eleven_turbo_v2_5

# OpenAI TTS
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova
```

## Payments

### Stripe Connect

```bash
# Get from: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

## Optional Services

### Google Maps

For importing restaurant operating hours from Google Business:

```bash
# Get from: https://console.cloud.google.com/
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Kitchen Printer

For email-based cloud printing:

```bash
KITCHEN_PRINTER_EMAIL=your_printer_email_here
```

## Server Configuration

```bash
# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000

# Environment mode
ENVIRONMENT=development  # or "production"

# Server binding
API_HOST=0.0.0.0
API_PORT=8000
```

## Example .env File

```bash
# === REQUIRED ===
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...
JWT_SECRET_KEY=your-32-char-secret

# === AI ===
GOOGLE_AI_API_KEY=AIza...
LLM_PROVIDER=gemini

# === VOICE ===
RETELL_API_KEY=key_...

# === PAYMENTS ===
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# === SERVER ===
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

---

**Related:**
- [Getting Started](./getting-started.md)
- [Voice AI Setup](./voice-ai.md)
