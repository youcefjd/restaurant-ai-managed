// Application Constants
// This file contains all application-wide constants including API endpoints,
// status values, and configuration options

// =============================================================================
// API Configuration
// =============================================================================

// Base API URL - uses environment variable or defaults to localhost
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API version prefix
export const API_VERSION = '/api';

// Full API URL
export const API_URL = `${API_BASE_URL}${API_VERSION}`;

// =============================================================================
// API Endpoints
// =============================================================================

export const API_ENDPOINTS = {
  // Restaurant endpoints
  RESTAURANTS: {
    LIST: '/',
    CREATE: '/',
    UPDATE: (id) => `/${id}`,
    DELETE: (id) => `/${id}`,
    GET: (id) => `/${id}`,
  },

  // Table endpoints
  TABLES: {
    LIST: (restaurantId) => `/${restaurantId}/tables`,
    CREATE: (restaurantId) => `/${restaurantId}/tables`,
    UPDATE: (restaurantId, tableId) => `/${restaurantId}/tables/${tableId}`,
    DELETE: (restaurantId, tableId) => `/${restaurantId}/tables/${tableId}`,
    GET: (restaurantId, tableId) => `/${restaurantId}/tables/${tableId}`,
  },

  // Booking endpoints
  BOOKINGS: {
    LIST: '/bookings/',
    CREATE: '/bookings/',
    GET: (id) => `/bookings/${id}`,
    UPDATE: (id) => `/bookings/${id}`,
    DELETE: (id) => `/bookings/${id}`,
    CANCEL: (id) => `/bookings/${id}`,
  },

  // Customer endpoints
  CUSTOMERS: {
    LIST: '/customers/',
    CREATE: '/customers/',
    GET: (id) => `/customers/${id}`,
    UPDATE: (id) => `/customers/${id}`,
    DELETE: (id) => `/customers/${id}`,
  },

  // Availability endpoints
  AVAILABILITY: {
    CHECK: '/availability/check',
  },
};

// =============================================================================
// HTTP Methods
// =============================================================================

export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  PATCH: 'PATCH',
  DELETE: 'DELETE',
};

// =============================================================================
// Booking Status Values
// =============================================================================

export const BOOKING_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  CANCELLED: 'cancelled',
  COMPLETED: 'completed',
  NO_SHOW: 'no_show',
};

// Human-readable booking status labels
export const BOOKING_STATUS_LABELS = {
  [BOOKING_STATUS.PENDING]: 'Pending',
  [BOOKING_STATUS.CONFIRMED]: 'Confirmed',
  [BOOKING_STATUS.CANCELLED]: 'Cancelled',
  [BOOKING_STATUS.COMPLETED]: 'Completed',
  [BOOKING_STATUS.NO_SHOW]: 'No Show',
};

// Booking status colors for UI (TailwindCSS classes)
export const BOOKING_STATUS_COLORS = {
  [BOOKING_STATUS.PENDING]: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    dot: 'bg-yellow-400',
  },
  [BOOKING_STATUS.CONFIRMED]: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-200',
    dot: 'bg-green-400',
  },
  [BOOKING_STATUS.CANCELLED]: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-200',
    dot: 'bg-red-400',
  },
  [BOOKING_STATUS.COMPLETED]: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-200',
    dot: 'bg-blue-400',
  },
  [BOOKING_STATUS.NO_SHOW]: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-200',
    dot: 'bg-gray-400',
  },
};

// =============================================================================
// Table Status Values
// =============================================================================

export const TABLE_STATUS = {
  AVAILABLE: 'available',
  OCCUPIED: 'occupied',
  RESERVED: 'reserved',
  MAINTENANCE: 'maintenance',
};

// Human-readable table status labels
export const TABLE_STATUS_LABELS = {
  [TABLE_STATUS.AVAILABLE]: 'Available',
  [TABLE_STATUS.OCCUPIED]: 'Occupied',
  [TABLE_STATUS.RESERVED]: 'Reserved',
  [TABLE_STATUS.MAINTENANCE]: 'Maintenance',
};

// Table status colors for UI (TailwindCSS classes)
export const TABLE_STATUS_COLORS = {
  [TABLE_STATUS.AVAILABLE]: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-200',
    dot: 'bg-green-400',
  },
  [TABLE_STATUS.OCCUPIED]: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-200',
    dot: 'bg-red-400',
  },
  [TABLE_STATUS.RESERVED]: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    dot: 'bg-yellow-400',
  },
  [TABLE_STATUS.MAINTENANCE]: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-200',
    dot: 'bg-gray-400',
  },
};

// =============================================================================
// Restaurant Status Values
// =============================================================================

export const RESTAURANT_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  CLOSED: 'closed',
  TEMPORARILY_CLOSED: 'temporarily_closed',
};

// Human-readable restaurant status labels
export const RESTAURANT_STATUS_LABELS = {
  [RESTAURANT_STATUS.ACTIVE]: 'Active',
  [RESTAURANT_STATUS.INACTIVE]: 'Inactive',
  [RESTAURANT_STATUS.CLOSED]: 'Closed',
  [RESTAURANT_STATUS.TEMPORARILY_CLOSED]: 'Temporarily Closed',
};

// Restaurant status colors for UI (TailwindCSS classes)
export const RESTAURANT_STATUS_COLORS = {
  [RESTAURANT_STATUS.ACTIVE]: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-200',
    dot: 'bg-green-400',
  },
  [RESTAURANT_STATUS.INACTIVE]: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-200',
    dot: 'bg-gray-400',
  },
  [RESTAURANT_STATUS.CLOSED]: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-200',
    dot: 'bg-red-400',
  },
  [RESTAURANT_STATUS.TEMPORARILY_CLOSED]: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    dot: 'bg-yellow-400',
  },
};

// =============================================================================
// Pagination Defaults
// =============================================================================

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 25, 50, 100],
  MAX_PAGE_SIZE: 100,
};

// =============================================================================
// Date and Time Formats
// =============================================================================

export const DATE_FORMATS = {
  // Display formats
  DISPLAY_DATE: 'MMM dd, yyyy', // Jan 01, 2024
  DISPLAY_TIME: 'hh:mm a', // 12:30 PM
  DISPLAY_DATETIME: 'MMM dd, yyyy hh:mm a', // Jan 01, 2024 12:30 PM
  DISPLAY_DATE_SHORT: 'MM/dd/yyyy', // 01/01/2024
  DISPLAY_DATE_LONG: 'EEEE, MMMM dd, yyyy', // Monday, January 01, 2024

  // API formats (ISO 8601)
  API_DATE: 'yyyy-MM-dd', // 2024-01-01
  API_TIME: 'HH:mm:ss', // 14:30:00
  API_DATETIME: "yyyy-MM-dd'T'HH:mm:ss", // 2024-01-01T14:30:00

  // Input formats
  INPUT_DATE: 'yyyy-MM-dd', // For HTML date inputs
  INPUT_TIME: 'HH:mm', // For HTML time inputs
  INPUT_DATETIME: "yyyy-MM-dd'T'HH:mm", // For HTML datetime-local inputs
};

// =============================================================================
// Time Slots Configuration
// =============================================================================

export const TIME_SLOTS = {
  // Restaurant operating hours (default)
  DEFAULT_OPEN_TIME: '09:00',
  DEFAULT_CLOSE_TIME: '22:00',

  // Booking duration options (in minutes)
  DURATION_OPTIONS: [30, 60, 90, 120, 150, 180],
  DEFAULT_DURATION: 90,

  // Time slot interval for availability (in minutes)
  SLOT_INTERVAL: 30,

  // Minimum advance booking time (in hours)
  MIN_ADVANCE_BOOKING: 1,

  // Maximum advance booking time (in days)
  MAX_ADVANCE_BOOKING: 30,
};

// =============================================================================
// Party Size Configuration
// =============================================================================

export const PARTY_SIZE = {
  MIN: 1,
  MAX: 20,
  DEFAULT: 2,
  OPTIONS: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20],
};

// =============================================================================
// Form Validation Rules
// =============================================================================

export const VALIDATION = {
  // Name fields
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 100,

  // Email
  EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,

  // Phone (flexible pattern for international numbers)
  PHONE_PATTERN: /^[+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]*$/,
  PHONE_MIN_LENGTH: 7,
  PHONE_MAX_LENGTH: 20,

  // Address
  ADDRESS_MAX_LENGTH: 500,

  // Notes/Comments
  NOTES_MAX_LENGTH: 1000,

  // Table capacity
  TABLE_MIN_CAPACITY: 1,
  TABLE_MAX_CAPACITY: 50,
};

// =============================================================================
// Error Messages
// =============================================================================

export const ERROR_MESSAGES = {
  // Generic errors
  GENERIC: 'Something went wrong. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timed out. Please try again.',
  NOT_FOUND: 'The requested resource was not found.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied.',
  SERVER_ERROR: 'Server error. Please try again later.',

  // Validation errors
  REQUIRED_FIELD: 'This field is required.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  INVALID_PHONE: 'Please enter a valid phone number.',
  NAME_TOO_SHORT: `Name must be at least ${VALIDATION.NAME_MIN_LENGTH} characters.`,
  NAME_TOO_LONG: `Name must be less than ${VALIDATION.NAME_MAX_LENGTH} characters.`,

  // Booking errors
  BOOKING_CONFLICT: 'This time slot is no longer available.',
  PAST_DATE: 'Cannot book for a past date.',
  TOO_FAR_ADVANCE: `Cannot book more than ${TIME_SLOTS.MAX_ADVANCE_BOOKING} days in advance.`,
  INVALID_PARTY_SIZE: `Party size must be between ${PARTY_SIZE.MIN} and ${PARTY_SIZE.MAX}.`,

  // Table errors
  TABLE_NOT_AVAILABLE: 'This table is not available.',
  INVALID_CAPACITY: 'Invalid table capacity.',

  // Restaurant errors
  RESTAURANT_CLOSED: 'This restaurant is currently closed.',
};

// =============================================================================
// Success Messages
// =============================================================================

export const SUCCESS_MESSAGES = {
  // Generic
  SAVED: 'Changes saved successfully.',
  DELETED: 'Deleted successfully.',
  CREATED: 'Created successfully.',
  UPDATED: 'Updated successfully.',

  // Booking
  BOOKING_CREATED: 'Booking created successfully.',
  BOOKING_UPDATED: 'Booking updated successfully.',
  BOOKING_CANCELLED: 'Booking cancelled successfully.',
  BOOKING_CONFIRMED: 'Booking confirmed successfully.',

  // Restaurant
  RESTAURANT_CREATED: 'Restaurant created successfully.',
  RESTAURANT_UPDATED: 'Restaurant updated successfully.',
  RESTAURANT_DELETED: 'Restaurant deleted successfully.',

  // Table
  TABLE_CREATED: 'Table created successfully.',
  TABLE_UPDATED: 'Table updated successfully.',
  TABLE_DELETED: 'Table deleted successfully.',

  // Customer
  CUSTOMER_CREATED: 'Customer created successfully.',
  CUSTOMER_UPDATED: 'Customer updated successfully.',
  CUSTOMER_DELETED: 'Customer deleted successfully.',
};

// =============================================================================
// Navigation Routes
// =============================================================================

export const ROUTES = {
  // Main routes
  HOME: '/',
  DASHBOARD: '/dashboard',

  // Restaurant routes
  RESTAURANTS: '/restaurants',
  RESTAURANT_DETAIL: (id) => `/restaurants/${id}`,
  RESTAURANT_NEW: '/restaurants/new',
  RESTAURANT_EDIT: (id) => `/restaurants/${id}/edit`,

  // Table routes
  TABLES: '/tables',
  TABLES_BY_RESTAURANT: (restaurantId) => `/restaurants/${restaurantId}/tables`,
  TABLE_NEW: (restaurantId) => `/restaurants/${restaurantId}/tables/new`,

  // Booking routes
  BOOKINGS: '/bookings',
  BOOKING_DETAIL: (id) => `/bookings/${id}`,
  BOOKING_NEW: '/bookings/new',
  BOOKING_EDIT: (id) => `/bookings/${id}/edit`,

  // Customer routes
  CUSTOMERS: '/customers',
  CUSTOMER_DETAIL: (id) => `/customers/${id}`,
  CUSTOMER_NEW: '/customers/new',
  CUSTOMER_EDIT: (id) => `/customers/${id}/edit`,
};

// =============================================================================
// Local Storage Keys
// =============================================================================

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  LAST_SELECTED_RESTAURANT: 'last_selected_restaurant',
  TABLE_PAGE_SIZE: 'table_page_size',
};

// =============================================================================
// Theme Configuration
// =============================================================================

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
};

// =============================================================================
// Breakpoints (matching TailwindCSS defaults)
// =============================================================================

export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
};

// =============================================================================
// Animation Durations (in milliseconds)
// =============================================================================

export const ANIMATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  TOAST_DURATION: 5000,
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 100,
};

// =============================================================================
// Dashboard Statistics Card Types
// =============================================================================

export const STAT_CARD_TYPES = {
  TOTAL_BOOKINGS: 'total_bookings',
  TODAY_BOOKINGS: 'today_bookings',
  TOTAL_RESTAURANTS: 'total_restaurants',
  TOTAL_CUSTOMERS: 'total_customers',
  AVAILABLE_TABLES: 'available_tables',
  PENDING_BOOKINGS: 'pending_bookings',
};

// =============================================================================
// Export Default Object for Convenience
// =============================================================================

const constants = {
  API_BASE_URL,
  API_VERSION,
  API_URL,
  API_ENDPOINTS,
  HTTP_METHODS,
  BOOKING_STATUS,
  BOOKING_STATUS_LABELS,
  BOOKING_STATUS_COLORS,
  TABLE_STATUS,
  TABLE_STATUS_LABELS,
  TABLE_STATUS_COLORS,
  RESTAURANT_STATUS,
  RESTAURANT_STATUS_LABELS,
  RESTAURANT_STATUS_COLORS,
  PAGINATION,
  DATE_FORMATS,
  TIME_SLOTS,
  PARTY_SIZE,
  VALIDATION,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  ROUTES,
  STORAGE_KEYS,
  THEMES,
  BREAKPOINTS,
  ANIMATION,
  STAT_CARD_TYPES,
};

export default constants;