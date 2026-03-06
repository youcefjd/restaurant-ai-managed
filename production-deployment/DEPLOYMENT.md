# Production Deployment Guide

## Architecture Overview

```
belltab.com / www.belltab.com  →  Vercel (frontend)
                                      ↓ API calls
                               Railway (backend)
                                      ↓
                               Supabase (database)
```

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | https://www.belltab.com / https://frontend-gilt-three-99.vercel.app |
| Backend | Railway | https://restaurant-ai-backend-production-b1df.up.railway.app |
| Database | Supabase | https://jtmltcdnthzpvdayuwkl.supabase.co |
| Domain DNS | Cloudflare | belltab.com |

---

## Auto-Deploy (Git Push)

Both services auto-deploy when you push to `main`:

```bash
git add .
git commit -m "your changes"
git push origin main
```

- **Vercel** picks up changes in `frontend/` and rebuilds
- **Railway** picks up all changes and rebuilds the backend

---

## Manual Deploy

### Frontend (Vercel)

```bash
cd frontend

# Build locally
npm run build

# Prepare Vercel output
vercel build --prod

# Deploy prebuilt artifacts
vercel deploy --prebuilt --prod --yes
```

### Backend (Railway)

```bash
# From project root
railway up --detach
```

---

## Monitoring

### Vercel

```bash
# List recent deployments
vercel ls

# Inspect a specific deployment
vercel inspect <deployment-url>

# View logs
vercel logs <deployment-url> --project frontend
```

### Railway

```bash
# View live logs
railway logs -n 50

# Check service status
railway status

# Redeploy latest (no code changes)
railway redeploy --yes
```

---

## Domain & DNS (Cloudflare)

Domain `belltab.com` is registered and managed on Cloudflare.

| Type | Name | Value | Proxy |
|------|------|-------|-------|
| A | `@` | `216.198.79.1` | DNS only (grey cloud) |
| CNAME | `www` | `5dedd8564f6c44d6.vercel-dns-017.com.` | DNS only (grey cloud) |

**Important:** Proxy must be "DNS only" (grey cloud), not "Proxied" (orange cloud). Cloudflare proxy interferes with Vercel's SSL.

---

## Email Integration (Contact Form)

The "Get Started" contact form on belltab.com sends emails via **Resend API**.

**Flow:**
1. User fills form on belltab.com
2. Frontend POSTs to `POST /api/contact` on Railway backend
3. Backend sends email via Resend API from `onboarding@resend.dev` to `djeddar@icloud.com`
4. User's email is set as `Reply-To` so you can reply directly

**Resend dashboard:** https://resend.com/emails

Free tier: 100 emails/day, sender is `onboarding@resend.dev`. To send from a custom domain (e.g. `hello@belltab.com`), add and verify the domain in Resend dashboard.

---

## Environment Variables

### Vercel (Frontend)

Set in `frontend/.env.production` (committed to repo):

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://restaurant-ai-backend-production-b1df.up.railway.app/api` |

### Railway (Backend)

Set via Railway dashboard or CLI (`railway variables set KEY=VALUE`):

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |
| `RESEND_API_KEY` | Resend API key for contact form emails |
| `CONTACT_EMAIL` | Recipient for contact form (default: djeddar@icloud.com) |
| `SMTP_USER` | (unused, kept for reference) iCloud SMTP user |
| `SMTP_APP_PASSWORD` | (unused, kept for reference) iCloud app-specific password |
| `RETELL_API_KEY` | Retell AI voice agent key |
| `STRIPE_SECRET_KEY` | Stripe payments key |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key |
| `GOOGLE_GENAI_API_KEY` | Gemini LLM key |
| `ENVIRONMENT` | `production` |

To list all variables:
```bash
railway variables
```

---

## Vercel Project Settings

| Setting | Value |
|---------|-------|
| Project Name | `frontend` |
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Production Branch | `main` |
| Git Repo | `youcefjd/restaurant-ai-managed` |

Custom domains: `belltab.com`, `www.belltab.com`, `frontend-gilt-three-99.vercel.app`

---

## Railway Service Settings

| Setting | Value |
|---------|-------|
| Service Name | `restaurant-ai-backend` |
| Source | `youcefjd/restaurant-ai-managed` (main branch) |
| Builder | Railpack (auto-detects Python) |
| Start Command | `python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}` |
| Public Domain | `restaurant-ai-backend-production-b1df.up.railway.app` |

Config file: `railway.toml` at project root.

---

## Git Configuration

```bash
# Required git config (must match Vercel/GitHub account)
git config --global user.email "issh_hrc@hotmail.co.uk"
git config --global user.name "Youcef Djeddar"
```

**Important:** The commit author email MUST match the Vercel team member email (`issh_hrc@hotmail.co.uk`), otherwise Git-triggered deploys will fail.

---

## Onboarding a New Restaurant

1. Create restaurant account + user credentials in the backend (via admin dashboard or API)
2. Share the Vercel app URL + their login credentials
3. They sign in at `belltab.com` or `frontend-gilt-three-99.vercel.app` and manage their restaurant

All restaurants use the same deployment — the app is multi-tenant, scoped by authenticated user.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Vercel deploy errors with "Git author must have access" | Check `git config user.email` matches `issh_hrc@hotmail.co.uk` |
| Vercel deploy 0ms build | Check Root Directory is set to `frontend` in project settings |
| Railway deploy stuck at INITIALIZING | Check `.railwayignore` excludes `.venv/` — local Mac binaries break Linux builds |
| Railway SMTP timeout | SMTP ports are blocked on Railway. Use Resend API (HTTP-based) instead |
| Contact form "Something went wrong" | Check Railway logs: `railway logs -n 20` |
| belltab.com not loading | Check Cloudflare DNS records, ensure proxy is "DNS only" |
