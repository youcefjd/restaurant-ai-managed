# Voice AI Setup Guide

Complete setup guide for the real-time voice AI system using Twilio Media Streams, Deepgram STT, OpenAI/Gemini LLM, and ElevenLabs TTS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Key Setup](#api-key-setup)
3. [Environment Variables](#environment-variables)
4. [ngrok Configuration](#ngrok-configuration)
5. [Twilio Configuration](#twilio-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.9+
- Twilio account with a phone number
- API accounts for:
  - Deepgram (for STT)
  - OpenAI or Google AI (for LLM)
  - ElevenLabs (for TTS)
- ngrok account (for local testing)

---

## API Key Setup

### 1. Deepgram Setup (Speech-to-Text)

**Steps:**
1. Sign up at [deepgram.com](https://deepgram.com)
2. Go to API Keys section
3. Create a new API key
4. Copy the API key

**Pricing:** ~$0.0043/min (per-second billing)

**Model Used:** `nova-2` (real-time, low latency)

---

### 2. LLM Provider Setup

Choose **ONE** of the following:

#### Option A: Google Gemini Flash-Lite (Default) ⭐ Recommended

**Steps:**
1. Sign up at [aistudio.google.com](https://aistudio.google.com)
2. Go to API Keys section
3. Create a new API key
4. Copy the API key

**Pricing:**
- Input: ~$0.10/1M tokens
- Output: ~$0.40/1M tokens
- **Significantly cheaper (~30-40% savings)**

**Model Used:** `gemini-2.0-flash-exp` or `gemini-1.5-flash`

#### Option B: OpenAI GPT-4o (Fallback - Higher Quality, More Expensive)

**Steps:**
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Go to API Keys section
3. Create a new API key
4. Copy the API key

**Pricing:** 
- Input: ~$2.50/1M tokens
- Output: ~$10/1M tokens

**Model Used:** `gpt-4o`

**Note:** OpenAI is used as an automatic fallback if Gemini fails. You can also set `LLM_PROVIDER=openai` to use OpenAI as primary.

---

### 3. ElevenLabs Setup (Text-to-Speech)

**Steps:**
1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Go to API Keys section
3. Create a new API key
4. Copy the API key

**Pricing:** Subscription-based + per-character usage

**Model Used:** `eleven_turbo_v2_5` (low latency)

**Voice:** Default conversational voice (can be customized via `ELEVENLABS_VOICE_ID`)

---

### 4. ngrok Setup (Local Testing)

**Steps:**
1. Sign up at [ngrok.com](https://ngrok.com)
2. Install ngrok:
   ```bash
   # macOS
   brew install ngrok/ngrok/ngrok
   
   # Or download from https://ngrok.com/download
   ```
3. Get your authtoken from the ngrok dashboard
4. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

---

## Environment Variables

Add the following to your `.env` file:

```env
# Deepgram (Required)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# LLM Provider - Gemini is default, OpenAI is fallback
# Primary: Gemini (default, cheaper)
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_PROVIDER=gemini

# Fallback: OpenAI (optional, used if Gemini fails)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# ElevenLabs (Required)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_MODEL=eleven_turbo_v2_5
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Optional, uses default if not set

# Twilio (Required - existing)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# WebSocket URL (Required)
# For local testing with ngrok:
PUBLIC_WS_URL=wss://your-ngrok-url.ngrok.io

# For production:
# PUBLIC_WS_URL=wss://your-production-domain.com
```

---

## ngrok Configuration

### Starting ngrok Tunnel

1. Start your FastAPI server:
   ```bash
   cd /path/to/restaurant-ai-managed
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

2. In a separate terminal, start ngrok:
   ```bash
   ngrok http 8000
   ```

3. Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)

4. Update your `.env` file:
   ```env
   PUBLIC_WS_URL=wss://abc123.ngrok.io
   ```

**Important:** 
- Use `wss://` (secure WebSocket) if ngrok provides HTTPS
- Use `ws://` only for local testing without ngrok HTTPS
- The ngrok URL changes each time you restart ngrok (free plan)
- For production, use your actual domain with SSL certificate

### Using ngrok with Custom Domain (Optional)

If you have a paid ngrok plan:
```bash
ngrok http 8000 --domain=your-custom-domain.ngrok.io
```

---

## Twilio Configuration

### 1. Enable Media Streams

1. Log in to [Twilio Console](https://console.twilio.com)
2. Go to Phone Numbers → Manage → Active Numbers
3. Click on your phone number
4. Scroll to "Voice & Fax" section
5. Find "Media Streams" and enable it

### 2. Configure Webhooks

In the same phone number configuration:

**Voice Configuration:**
- **A Call Comes In (Webhook):** 
  - Method: `POST`
  - URL: `https://your-ngrok-url.ngrok.io/api/voice/welcome`
  - Or production: `https://your-domain.com/api/voice/welcome`

**Status Callback:**
- **Status Callback URL:**
  - Method: `POST`
  - URL: `https://your-ngrok-url.ngrok.io/api/voice/status`
  - Or production: `https://your-domain.com/api/voice/status`

### 3. Set Restaurant Phone Number

In the restaurant dashboard:
1. Go to Settings
2. Enter your Twilio phone number (E.164 format: `+15551234567`)
3. Save

---

## Testing

### 1. Verify Services Are Running

```bash
# Check health endpoint
curl http://localhost:8000/api/voice/health
```

Expected response:
```json
{
  "service": "voice",
  "enabled": true,
  "status": "healthy"
}
```

### 2. Test WebSocket Connection

1. Start your server
2. Start ngrok
3. Call your Twilio number
4. Check server logs for:
   - "Media Streams WebSocket connection accepted"
   - "Deepgram live transcription started"
   - Any errors

### 3. Test Conversation Flow

**Test Menu Question:**
- Say: "What vegetarian options do you have?"
- Expected: AI lists vegetarian items from menu

**Test Order:**
- Say: "I'd like to order a pizza"
- Expected: AI asks for details (size, toppings, etc.)

**Test Reservation:**
- Say: "I want to make a reservation for 4 people tomorrow at 7pm"
- Expected: AI checks availability and confirms booking

### 4. Test Error Handling

**Simulate Service Failure:**
- Temporarily remove an API key from `.env`
- Make a call
- Expected: SMS fallback message sent to customer

---

## Troubleshooting

### Issue: WebSocket Connection Fails

**Symptoms:**
- Error: "Media Streams WebSocket connection failed"
- Call hangs up immediately

**Solutions:**
1. Verify `PUBLIC_WS_URL` is set correctly in `.env`
2. Check ngrok is running and accessible
3. Verify WebSocket URL uses `wss://` (secure) or `ws://` (insecure)
4. Check firewall/network allows WebSocket connections
5. Verify FastAPI server is running on the correct port

### Issue: Deepgram Not Transcribing

**Symptoms:**
- No transcripts appearing in logs
- AI not responding

**Solutions:**
1. Verify `DEEPGRAM_API_KEY` is set correctly
2. Check Deepgram API key is valid (not expired)
3. Check Deepgram account has credits
4. Verify audio format conversion (mulaw → linear16)
5. Check server logs for Deepgram errors

### Issue: LLM Not Responding

**Symptoms:**
- Transcriptions received but no AI response
- Timeout errors

**Solutions:**
1. Verify Gemini API key is set (primary provider)
2. Verify OpenAI API key is set (fallback provider)
3. Check `LLM_PROVIDER` environment variable (default: `gemini`)
4. Verify API keys have sufficient credits/quota
5. Check server logs for LLM API errors - system will automatically try fallback
6. Check logs for "Using OpenAI as fallback" or "Using Gemini as fallback" messages

### Issue: ElevenLabs Not Generating Audio

**Symptoms:**
- AI responses appear but no audio played
- Customer hears silence

**Solutions:**
1. Verify `ELEVENLABS_API_KEY` is set correctly
2. Check ElevenLabs account has subscription/credits
3. Verify `ELEVENLABS_VOICE_ID` is valid (if set)
4. Check server logs for ElevenLabs API errors
5. Verify audio chunks are being sent to Twilio

### Issue: SMS Fallback Not Sending

**Symptoms:**
- Voice fails but no SMS sent

**Solutions:**
1. Verify Twilio credentials are set
2. Check restaurant has `twilio_phone_number` configured
3. Verify SMS service is enabled
4. Check server logs for SMS sending errors

### Issue: Restaurant Not Found

**Symptoms:**
- "No restaurant found for Twilio number" error

**Solutions:**
1. Verify phone number is set in restaurant settings
2. Check phone number format (E.164: `+15551234567`)
3. Verify phone number matches Twilio number exactly
4. Check database for restaurant account

---

## Cost Estimates

### Per 5-Minute Call

**With OpenAI:**
- Twilio Media Streams: ~$0.0425
- Deepgram STT: ~$0.0215
- OpenAI GPT-4o: ~$0.01-0.02
- ElevenLabs TTS: ~$0.01-0.02
- **Total: ~$0.07-0.11**

**With Gemini (Recommended):**
- Twilio Media Streams: ~$0.0425
- Deepgram STT: ~$0.0215
- Gemini Flash-Lite: ~$0.003-0.005
- ElevenLabs TTS: ~$0.01-0.02
- **Total: ~$0.06-0.08** (savings of ~30-40%)

### Monthly (1,000 calls = 5,000 minutes)

- **With OpenAI:** ~$70-110/month
- **With Gemini:** ~$60-80/month ⭐ Recommended

---

## Production Deployment

### 1. Use Production Domain

Update `.env`:
```env
PUBLIC_WS_URL=wss://your-production-domain.com
```

### 2. SSL Certificate Required

WebSocket connections require SSL (wss://) in production. Ensure your server has a valid SSL certificate.

### 3. Update Twilio Webhooks

Update webhook URLs in Twilio Console to use production domain instead of ngrok.

### 4. Monitor Service Health

Set up monitoring for:
- API rate limits
- Service availability
- Error rates
- Response times

### 5. Scale Considerations

For high traffic:
- Consider Redis for conversation state (currently in-memory)
- Load balancing for multiple server instances
- Connection pooling for database

---

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Verify all environment variables are set
3. Test each service individually (Deepgram, LLM, ElevenLabs)
4. Check API provider dashboards for quota/credit limits

---

**Last Updated:** 2025-01-15
