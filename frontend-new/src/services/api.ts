import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Platform Admin API
export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  getRestaurants: (params?: { status_filter?: string; is_active?: boolean }) =>
    api.get('/admin/restaurants', { params }),
  getRestaurantDetails: (id: number) => api.get(`/admin/restaurants/${id}/details`),
  getRevenue: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/admin/revenue', { params }),
  getAnalytics: (days: number = 30) => api.get(`/admin/analytics/growth?days=${days}`),
  suspendRestaurant: (id: number) => api.post(`/admin/restaurants/${id}/suspend`),
  activateRestaurant: (id: number) => api.post(`/admin/restaurants/${id}/activate`),
}

// Restaurant API
export const restaurantAPI = {
  getOrders: (restaurantId: number, params?: { status_filter?: string }) =>
    api.get('/orders', { params: { restaurant_id: restaurantId, ...params } }),
  getOrderDetails: (id: number) => api.get(`/orders/${id}`),
  updateOrderStatus: (id: number, status: string) =>
    api.put(`/orders/${id}`, { status }),
  getMenu: (accountId: number) => api.get(`/onboarding/accounts/${accountId}/menu-full`),
  createMenuItem: (data: any) => api.post('/onboarding/items', data),
  createModifier: (data: any) => api.post('/onboarding/modifiers', data),
}

// Stripe Connect API
export const stripeAPI = {
  getStatus: (accountId: number) => api.get(`/stripe-connect/status/${accountId}`),
  startOnboarding: (data: any) => api.post('/stripe-connect/onboard', data),
  getBalance: (accountId: number) => api.get(`/stripe-connect/balance/${accountId}`),
  getDashboardLink: (accountId: number) => api.get(`/stripe-connect/dashboard-link/${accountId}`),
}

// Deliveries API
export const deliveryAPI = {
  getDeliveries: (params?: { status_filter?: string }) =>
    api.get('/deliveries', { params }),
  updateDelivery: (id: number, data: any) => api.put(`/deliveries/${id}`, data),
  createDelivery: (data: any) => api.post('/deliveries', data),
}

export default api
