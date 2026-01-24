# Frontend Architecture

React TypeScript application built with Vite.

## Technology Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI library |
| TypeScript | Type safety |
| Vite 7 | Build tool |
| React Router v6 | Routing |
| TanStack Query v5 | Server state |
| Tailwind CSS 3.4 | Styling |
| Axios | HTTP client |
| Recharts | Charts |
| Lucide React | Icons |
| Framer Motion | Animations |

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Root component + routes
│   ├── pages/
│   │   ├── LandingPage.tsx
│   │   ├── auth/
│   │   │   ├── RestaurantLogin.tsx
│   │   │   ├── AdminLogin.tsx
│   │   │   └── Signup.tsx
│   │   ├── restaurant/       # Restaurant owner pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Menu.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── Transcripts.tsx
│   │   │   ├── Reservations.tsx
│   │   │   └── settings/
│   │   └── admin/            # Platform admin pages
│   │       ├── Dashboard.tsx
│   │       ├── Restaurants.tsx
│   │       ├── Revenue.tsx
│   │       └── Analytics.tsx
│   ├── components/
│   │   ├── layouts/
│   │   │   ├── RestaurantLayout.tsx
│   │   │   └── AdminLayout.tsx
│   │   ├── ui/
│   │   │   ├── PageHeader.tsx
│   │   │   ├── StatCard.tsx
│   │   │   └── TimePeriodFilter.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── LoadingTRex.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx
│   └── services/
│       └── api.ts            # API client
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## Key Files

### Entry Point

`src/main.tsx` - React bootstrap with providers.

### Routes

`src/App.tsx` - All route definitions:

```tsx
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/login" element={<RestaurantLogin />} />
  <Route path="/admin/login" element={<AdminLogin />} />
  <Route path="/signup" element={<Signup />} />

  {/* Protected restaurant routes */}
  <Route element={<ProtectedRoute />}>
    <Route path="/restaurant/*" element={<RestaurantLayout />}>
      <Route path="dashboard" element={<Dashboard />} />
      <Route path="orders" element={<Orders />} />
      <Route path="menu" element={<Menu />} />
      {/* ... */}
    </Route>
  </Route>

  {/* Protected admin routes */}
  <Route element={<ProtectedRoute adminOnly />}>
    <Route path="/admin/*" element={<AdminLayout />}>
      <Route path="dashboard" element={<AdminDashboard />} />
      {/* ... */}
    </Route>
  </Route>
</Routes>
```

### API Client

`src/services/api.ts` - Axios instance with interceptors:

```typescript
const api = axios.create({
  baseURL: '/api'
});

// Auto-attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401s
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Auth Context

`src/contexts/AuthContext.tsx` - Global auth state:

```typescript
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
```

## Layouts

### RestaurantLayout

Sidebar navigation for restaurant owners:
- Dashboard
- Orders
- Menu
- Analytics
- Transcripts
- Reservations
- Settings

### AdminLayout

Sidebar navigation for platform admins:
- Dashboard
- Restaurants
- Revenue
- Analytics

## Components

### ProtectedRoute

Guards routes requiring authentication:

```tsx
<Route element={<ProtectedRoute />}>
  {/* Protected routes */}
</Route>

<Route element={<ProtectedRoute adminOnly />}>
  {/* Admin-only routes */}
</Route>
```

### LoadingTRex

Fun loading animation displayed during page loads.

### StatCard

Reusable statistics card for dashboards.

### PageHeader

Consistent page header with title and actions.

## Data Fetching

Uses TanStack React Query for server state:

```typescript
const { data: orders, isLoading } = useQuery({
  queryKey: ['orders', 'today'],
  queryFn: () => restaurantAPI.getTodayOrders(),
  refetchInterval: 30000, // Refresh every 30s
});
```

## Styling

Tailwind CSS with custom configuration:
- Dark glassmorphism theme
- Custom color palette
- Responsive utilities

## Development

```bash
cd frontend
npm install
npm run dev
```

Vite dev server proxies `/api` to backend at port 8000.

## Build

```bash
npm run build
```

Output in `dist/` directory.

---

**Related:**
- [Frontend Pages](./frontend-pages.md)
- [Authentication](./authentication.md)
