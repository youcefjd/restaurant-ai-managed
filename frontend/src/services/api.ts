import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for dev proxy
// In preview/production, use the same hostname as the frontend but port 8000
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  if (import.meta.env.DEV) {
    // Development mode - use proxy
    return '/api'
  }
  // Preview/Production mode - use same hostname, port 8000
  const hostname = window.location.hostname
  return `http://${hostname}:8000/api`
}

const API_BASE_URL = getApiBaseUrl()

const api = axios.create({
  baseURL: API_BASE_URL,
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
  createRestaurant: (data: any) => api.post('/admin/restaurants', data),
  updateCommission: (id: number, data: { platform_commission_rate: number, commission_enabled: boolean }) =>
    api.put(`/admin/restaurants/${id}/commission`, data),
  updateSubscription: (id: number, data: { subscription_tier?: string, subscription_status?: string }) =>
    api.put(`/admin/restaurants/${id}/subscription`, data),
  suspendRestaurant: (id: number) => api.post(`/admin/restaurants/${id}/suspend`),
  activateRestaurant: (id: number) => api.post(`/admin/restaurants/${id}/activate`),
}

// Restaurant API
export const restaurantAPI = {
  // Orders - with dedicated endpoints for performance
  getOrders: (accountId: number, params?: { status_filter?: string }) =>
    api.get('/orders', { params: { account_id: accountId, ...params } }),
  getTodayOrders: () => api.get('/restaurant/orders/today'),
  getActiveOrders: () => api.get('/restaurant/orders/active'),
  getUpcomingOrders: (limit: number = 10) => api.get('/restaurant/orders/upcoming', { params: { limit } }),
  getOrderStats: (params?: { date_from?: string; date_to?: string }) =>
    api.get('/restaurant/orders/stats', { params }),
  getOrderDetails: (id: number) => api.get(`/restaurant/orders/${id}`),
  updateOrderStatus: (id: number, status: string) =>
    api.patch(`/restaurant/orders/${id}/status`, { status }),
  updatePaymentStatus: (id: number, payment_status: string, payment_method?: string) =>
    api.patch(`/restaurant/orders/${id}/payment`, { payment_status, payment_method }),
  getMenu: (accountId: number) => api.get(`/onboarding/accounts/${accountId}/menu-full`),
  importMenu: (accountId: number, formData: FormData) => 
    api.post(`/onboarding/accounts/${accountId}/menus/import`, formData),
  createMenu: (accountId: number, data: { menu_name?: string; menu_description?: string }) =>
    api.post(`/onboarding/accounts/${accountId}/menus`, null, {
      params: {
        menu_name: data.menu_name || '',
        ...(data.menu_description && { menu_description: data.menu_description }),
      }
    }),
  createCategory: (menuId: number, data: { name: string; description?: string; display_order?: number }) =>
    api.post(`/onboarding/menus/${menuId}/categories`, null, {
      params: {
        category_name: data.name,
        category_description: data.description,
        display_order: data.display_order || 0,
      }
    }),
  updateMenu: (menuId: number, data: { menu_name?: string; menu_description?: string }) =>
    api.put(`/onboarding/menus/${menuId}`, data),
  deleteMenu: (menuId: number) => api.delete(`/onboarding/menus/${menuId}`),
  createMenuItem: (data: any) => api.post('/onboarding/items', data),
  updateMenuItem: (itemId: number, data: any) => api.put(`/onboarding/items/${itemId}`, data),
  deleteMenuItem: (itemId: number) => api.delete(`/onboarding/items/${itemId}`),
  deleteAllMenuItems: (accountId: number, menuId: number) =>
    api.delete(`/onboarding/accounts/${accountId}/menus/${menuId}/items`),
  createModifier: (data: any) => api.post('/onboarding/modifiers', data),
  getAccount: (accountId: number) => api.get(`/onboarding/accounts/${accountId}`),
  updateTwilioPhone: (accountId: number, phoneNumber: string) =>
    api.patch(`/onboarding/accounts/${accountId}/twilio-phone`, { twilio_phone_number: phoneNumber }),
  removeTwilioPhone: (accountId: number) =>
    api.delete(`/onboarding/accounts/${accountId}/twilio-phone`),
  updateOperatingHours: (accountId: number, hours: { opening_time?: string; closing_time?: string; operating_days?: number[] }) =>
    api.patch(`/onboarding/accounts/${accountId}/operating-hours`, hours),
  updateTaxRate: (accountId: number, taxRate: number) =>
    api.patch(`/onboarding/accounts/${accountId}/tax-rate`, { tax_rate: taxRate }),
  updateOrderSettings: (accountId: number, maxAdvanceOrderDays: number) =>
    api.patch(`/onboarding/accounts/${accountId}/order-settings`, { max_advance_order_days: maxAdvanceOrderDays }),
  searchGoogleMaps: (query: string, location?: string) =>
    api.get('/onboarding/google-maps/search', { params: { query, location } }),
  getGoogleMapsPlace: (placeId: string) =>
    api.get(`/onboarding/google-maps/place/${placeId}`),
  updateHoursFromGoogle: (accountId: number, placeId: string) =>
    api.post(`/onboarding/accounts/${accountId}/operating-hours-from-google`, { place_id: placeId }),

  // Analytics
  getAnalyticsSummary: (days: number = 30) =>
    api.get('/restaurant/orders/analytics/summary', { params: { days } }),
  getPopularItems: (days: number = 30, limit: number = 10) =>
    api.get('/restaurant/orders/analytics/popular-items', { params: { days, limit } }),
  getOrderTrends: (days: number = 30) =>
    api.get('/restaurant/orders/analytics/trends', { params: { days } }),

  // Bookings / Table Reservations
  getBookings: (accountId: number, params?: { status_filter?: string; date_from?: string }) =>
    api.get('/bookings', { params: { account_id: accountId, ...params } }),
  updateBookingStatus: (id: number, status: string) =>
    api.put(`/bookings/${id}`, { status }),

  // Deliveries
  getDeliveries: (accountId: number, params?: { status_filter?: string }) =>
    api.get('/deliveries', { params: { account_id: accountId, ...params } }),
  updateDeliveryStatus: (id: number, status: string) =>
    api.put(`/deliveries/${id}`, { status }),

  // Transcripts
  getTranscripts: (accountId: number, params?: { transcript_type?: string }) =>
    api.get(`/onboarding/accounts/${accountId}/transcripts`, { params }),
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
