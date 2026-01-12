import axios from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor for adding auth tokens and logging
apiClient.interceptors.request.use(
  (config) => {
    // Get auth token from localStorage if it exists
    const TOKEN_REDACTED('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }

    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors and transforming responses
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }

    return response;
  },
  (error) => {
    // Handle different error scenarios
    const errorResponse = {
      message: 'An unexpected error occurred',
      status: null,
      data: null,
    };

    if (error.response) {
      // Server responded with error status
      errorResponse.status = error.response.status;
      errorResponse.data = error.response.data;

      switch (error.response.status) {
        case 400:
          errorResponse.message = error.response.data?.detail || 'Invalid request. Please check your input.';
          break;
        case 401:
          errorResponse.message = 'Authentication required. Please log in.';
          // Clear auth token and redirect to login if needed
          localStorage.removeItem('authToken');
          // Optionally trigger a redirect to login page
          // window.location.href = '/login';
          break;
        case 403:
          errorResponse.message = 'You do not have permission to perform this action.';
          break;
        case 404:
          errorResponse.message = error.response.data?.detail || 'The requested resource was not found.';
          break;
        case 422:
          // Validation error from FastAPI
          const validationErrors = error.response.data?.detail;
          if (Array.isArray(validationErrors)) {
            errorResponse.message = validationErrors
              .map((err) => `${err.loc?.join('.')}: ${err.msg}`)
              .join(', ');
          } else {
            errorResponse.message = 'Validation error. Please check your input.';
          }
          break;
        case 429:
          errorResponse.message = 'Too many requests. Please try again later.';
          break;
        case 500:
          errorResponse.message = 'Server error. Please try again later.';
          break;
        case 502:
        case 503:
        case 504:
          errorResponse.message = 'Service temporarily unavailable. Please try again later.';
          break;
        default:
          errorResponse.message = error.response.data?.detail || `Error: ${error.response.status}`;
      }
    } else if (error.request) {
      // Request was made but no response received
      errorResponse.message = 'Unable to connect to the server. Please check your internet connection.';
    } else {
      // Error in setting up the request
      errorResponse.message = error.message || 'An error occurred while making the request.';
    }

    // Log error in development
    if (import.meta.env.DEV) {
      console.error('[API Error]', {
        url: error.config?.url,
        method: error.config?.method,
        ...errorResponse,
      });
    }

    // Create enhanced error object
    const enhancedError = new Error(errorResponse.message);
    enhancedError.status = errorResponse.status;
    enhancedError.data = errorResponse.data;
    enhancedError.originalError = error;

    return Promise.reject(enhancedError);
  }
);

// API helper functions for common operations

/**
 * Restaurants API
 */
export const restaurantsApi = {
  // Get all restaurants
  getAll: () => apiClient.get('/api/'),
  
  // Get single restaurant by ID
  getById: (id) => apiClient.get(`/api/${id}`),
  
  // Create new restaurant
  create: (data) => apiClient.post('/api/', data),
  
  // Update existing restaurant
  update: (id, data) => apiClient.put(`/api/${id}`, data),
  
  // Delete restaurant
  delete: (id) => apiClient.delete(`/api/${id}`),
};

/**
 * Tables API
 */
export const tablesApi = {
  // Get all tables for a restaurant
  getByRestaurant: (restaurantId) => apiClient.get(`/api/${restaurantId}/tables`),
  
  // Create new table for a restaurant
  create: (restaurantId, data) => apiClient.post(`/api/${restaurantId}/tables`, data),
  
  // Update table
  update: (restaurantId, tableId, data) => 
    apiClient.put(`/api/${restaurantId}/tables/${tableId}`, data),
  
  // Delete table
  delete: (restaurantId, tableId) => 
    apiClient.delete(`/api/${restaurantId}/tables/${tableId}`),
};

/**
 * Bookings API
 */
export const bookingsApi = {
  // Get all bookings with optional filters
  getAll: (params = {}) => apiClient.get('/api/bookings/', { params }),
  
  // Get single booking by ID
  getById: (id) => apiClient.get(`/api/bookings/${id}`),
  
  // Create new booking
  create: (data) => apiClient.post('/api/bookings/', data),
  
  // Update booking
  update: (id, data) => apiClient.put(`/api/bookings/${id}`, data),
  
  // Cancel/delete booking
  cancel: (id) => apiClient.delete(`/api/bookings/${id}`),
};

/**
 * Customers API
 */
export const customersApi = {
  // Get all customers
  getAll: (params = {}) => apiClient.get('/api/customers/', { params }),
  
  // Get single customer by ID
  getById: (id) => apiClient.get(`/api/customers/${id}`),
  
  // Create new customer
  create: (data) => apiClient.post('/api/customers/', data),
  
  // Update customer
  update: (id, data) => apiClient.put(`/api/customers/${id}`, data),
  
  // Delete customer
  delete: (id) => apiClient.delete(`/api/customers/${id}`),
};

/**
 * Availability API
 */
export const availabilityApi = {
  // Check table availability
  check: (data) => apiClient.post('/api/availability/check', data),
};

// Export the configured axios instance as default
export default apiClient;