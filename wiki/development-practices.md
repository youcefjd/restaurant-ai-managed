# Development Practices

Guidelines and conventions for working on the Restaurant AI Platform.

## Code Organization

### Backend

```
backend/
├── api/           # Route handlers (thin controllers)
├── services/      # Business logic
├── core/          # Utilities, logging, exceptions
├── migrations/    # Database migrations
├── main.py        # App initialization
├── database.py    # Database connection
├── auth.py        # Authentication utilities
├── models.py      # Legacy model definitions
└── schemas.py     # Pydantic schemas
```

**Conventions:**
- Routes in `api/` are thin - they validate input and call services
- Business logic lives in `services/`
- One service per domain (orders, menus, voice, etc.)
- Services are instantiated as module-level singletons

### Frontend

```
frontend/src/
├── pages/         # Page components (route targets)
├── components/    # Reusable UI components
├── contexts/      # React contexts
├── services/      # API client and helpers
└── utils/         # Utility functions
```

**Conventions:**
- One page component per route
- Shared components in `components/ui/`
- Layout components in `components/layouts/`
- All API calls through `services/api.ts`

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `voice/description` - Voice AI work

Current main branch: `main`
Current development branch: `voice/retell-ai`

### Commits

Write clear, descriptive commit messages:

```
feat: Add order analytics endpoint
fix: Handle empty menu in conversation handler
refactor: Extract menu loading to service
```

## API Design

### Endpoints

- Use RESTful conventions
- Prefix with `/api`
- Group by domain (`/api/restaurant/orders`, `/api/admin/stats`)

### Request/Response

- Use Pydantic schemas for validation
- Return consistent error format: `{"detail": "message"}`
- Use appropriate HTTP status codes

### Authentication

- Protected routes use `Depends(get_current_user)`
- Admin routes check for admin role
- Return 401 for unauthenticated, 403 for unauthorized

## Database

### Supabase

- Use `SupabaseDB` wrapper for queries
- All queries should filter by `account_id` for tenant isolation
- Use migrations for schema changes

### Queries

```python
# Good - uses wrapper methods
db.query_one("orders", {"id": order_id, "account_id": account_id})

# Good - explicit select
db.table("orders").select("*").eq("account_id", account_id).execute()
```

## Error Handling

### Backend

- Use custom exceptions from `core/exceptions.py`
- Log errors with context
- Return user-friendly messages

```python
from backend.core.exceptions import ResourceNotFoundError

if not order:
    raise ResourceNotFoundError("Order not found")
```

### Frontend

- TanStack Query handles retries
- Show user-friendly error messages
- Log errors to console in development

## Testing

### Backend

```bash
pytest backend/tests/
```

### Frontend

```bash
cd frontend
npm test
```

## Environment

### Development

- Backend: `uvicorn backend.main:app --reload --port 8000`
- Frontend: `npm run dev` (proxies to backend)
- Use `.env` for local configuration

### Production

- Never commit `.env` files
- Use environment variables or secrets manager
- Enable HTTPS for webhooks

## Logging

Use structured logging:

```python
from backend.core.logging import setup_logging

logger = setup_logging(__name__)

logger.info("Processing order", extra={"order_id": 123})
logger.error("Failed to process", exc_info=True)
```

## Service Health

The `/health` endpoint checks:
- Database connection
- LLM availability
- External service status

Services gracefully degrade if dependencies are unavailable.

## Skills (Claude Commands)

The project includes skill symlinks in `.claude/skills/`:
- `create-pr` - Create pull requests
- `prompt-lookup` - Look up prompts
- `skill-lookup` - Look up skills

These are linked from `.agents/skills/`.

---

**Related:**
- [Getting Started](./getting-started.md)
- [Architecture](./architecture.md)
