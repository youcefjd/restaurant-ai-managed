# Authentication

The platform uses JWT-based authentication for securing API endpoints.

## Overview

- Restaurant owners authenticate with email/password
- Admin users have separate login
- JWTs are used for stateless authentication
- Tokens are stored client-side and sent with each request

## Login Flows

### Restaurant Login

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=owner@restaurant.com&password=secret
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "owner@restaurant.com",
    "business_name": "Joe's Pizza"
  }
}
```

### Admin Login

```
POST /auth/admin/login
Content-Type: application/json

{
  "email": "admin@restaurantai.com",
  "password": "admin123"
}
```

Note: Admin credentials are currently hardcoded. This should be moved to database for production.

## JWT Tokens

Tokens include:
- `sub`: User ID or account ID
- `email`: User email
- `exp`: Expiration timestamp
- `type`: Token type (restaurant or admin)

Configuration:
```bash
JWT_SECRET_KEY=your-secret-key-here
```

## Protected Routes

Routes are protected using FastAPI dependencies:

```python
from backend.api.auth import get_current_user

@router.get("/orders")
async def get_orders(current_user = Depends(get_current_user)):
    # current_user contains the decoded JWT payload
    account_id = current_user["account_id"]
    ...
```

## Frontend Integration

The frontend stores the token in localStorage:

```typescript
// On login
localStorage.setItem('auth_token', response.access_token);

// API client includes token automatically
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Token Verification

```
GET /auth/me
Authorization: Bearer {token}
```

Returns current user info or 401 if invalid/expired.

## Password Hashing

Passwords are hashed using bcrypt:

```python
from backend.auth import get_password_hash, verify_password

hashed = get_password_hash("plaintext")
is_valid = verify_password("plaintext", hashed)
```

## Signup

New restaurant accounts are created via:

```
POST /auth/signup
Content-Type: application/json

{
  "business_name": "New Restaurant",
  "owner_email": "owner@new.com",
  "owner_phone": "4155551234",
  "password": "securepassword"
}
```

## Frontend Protected Routes

React components use `ProtectedRoute` wrapper:

```tsx
<Route element={<ProtectedRoute />}>
  <Route path="/restaurant/*" element={<RestaurantLayout />} />
</Route>
```

The `AuthContext` provides auth state:

```tsx
const { user, isAuthenticated, login, logout } = useAuth();
```

---

**Related:**
- [API Overview](./api-overview.md)
- [Frontend](./frontend.md)
