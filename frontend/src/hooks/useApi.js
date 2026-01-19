import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for adding auth tokens, logging, etc.
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common error scenarios
    if (error.response?.status === 401) {
      // Unauthorized - could redirect to login or refresh token
      localStorage.removeItem('authToken');
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);

/**
 * Custom hook for making API calls with loading, error, and data state management
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.url - The API endpoint URL
 * @param {string} options.method - HTTP method (GET, POST, PUT, DELETE)
 * @param {Object} options.initialData - Initial data state
 * @param {boolean} options.immediate - Whether to fetch immediately on mount
 * @param {Function} options.onSuccess - Callback on successful response
 * @param {Function} options.onError - Callback on error
 * @param {Object} options.params - URL query parameters
 * @param {Object} options.body - Request body for POST/PUT
 * 
 * @returns {Object} - { data, loading, error, execute, reset, setData }
 */
export function useApi({
  url = '',
  method = 'GET',
  initialData = null,
  immediate = false,
  onSuccess = null,
  onError = null,
  params = null,
  body = null,
} = {}) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Track if component is mounted to prevent state updates after unmount
  const isMounted = useRef(true);
  // Track the current request to allow cancellation
  const abortControllerRef = useRef(null);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      // Cancel any pending request on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Execute the API request
   * 
   * @param {Object} executeOptions - Override options for this specific call
   * @param {string} executeOptions.url - Override URL
   * @param {Object} executeOptions.params - Override query parameters
   * @param {Object} executeOptions.body - Override request body
   * @param {Object} executeOptions.pathParams - Path parameters to replace in URL (e.g., {id})
   * 
   * @returns {Promise} - Resolves with response data or rejects with error
   */
  const execute = useCallback(async (executeOptions = {}) => {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    // Merge options
    let finalUrl = executeOptions.url || url;
    const finalParams = executeOptions.params || params;
    const finalBody = executeOptions.body || body;
    const pathParams = executeOptions.pathParams || {};

    // Replace path parameters in URL (e.g., /api/{id} -> /api/123)
    Object.entries(pathParams).forEach(([key, value]) => {
      finalUrl = finalUrl.replace(`{${key}}`, encodeURIComponent(value));
    });

    if (!finalUrl) {
      const noUrlError = new Error('No URL provided for API request');
      setError(noUrlError);
      return Promise.reject(noUrlError);
    }

    setLoading(true);
    setError(null);

    try {
      const config = {
        url: finalUrl,
        method: executeOptions.method || method,
        signal: abortControllerRef.current.signal,
      };

      // Add query parameters for GET requests
      if (finalParams) {
        config.params = finalParams;
      }

      // Add body for POST/PUT/PATCH requests
      if (finalBody && ['POST', 'PUT', 'PATCH'].includes(config.method.toUpperCase())) {
        config.data = finalBody;
      }

      const response = await apiClient(config);

      if (isMounted.current) {
        setData(response.data);
        setLoading(false);
        
        if (onSuccess) {
          onSuccess(response.data, response);
        }
      }

      return response.data;
    } catch (err) {
      // Don't update state if request was aborted
      if (axios.isCancel(err)) {
        return Promise.reject(err);
      }

      const errorMessage = parseError(err);
      
      if (isMounted.current) {
        setError(errorMessage);
        setLoading(false);
        
        if (onError) {
          onError(errorMessage, err);
        }
      }

      return Promise.reject(errorMessage);
    }
  }, [url, method, params, body, onSuccess, onError]);

  /**
   * Reset the hook state to initial values
   */
  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setLoading(false);
  }, [initialData]);

  /**
   * Cancel any pending request
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
  }, []);

  // Execute immediately on mount if specified
  useEffect(() => {
    if (immediate && url) {
      execute();
    }
  }, [immediate]); // Only run on mount, not when execute changes

  return {
    data,
    loading,
    error,
    execute,
    reset,
    cancel,
    setData,
    setError,
  };
}

/**
 * Simplified hook for GET requests that fetch on mount
 * 
 * @param {string} url - The API endpoint URL
 * @param {Object} params - Query parameters
 * @param {Object} options - Additional options
 * 
 * @returns {Object} - { data, loading, error, refetch }
 */
export function useFetch(url, params = null, options = {}) {
  const { data, loading, error, execute, setData } = useApi({
    url,
    method: 'GET',
    params,
    immediate: true,
    ...options,
  });

  return {
    data,
    loading,
    error,
    refetch: execute,
    setData,
  };
}

/**
 * Hook for POST requests (create operations)
 * 
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Additional options
 * 
 * @returns {Object} - { data, loading, error, post }
 */
export function usePost(url, options = {}) {
  const { data, loading, error, execute, reset } = useApi({
    url,
    method: 'POST',
    ...options,
  });

  const post = useCallback((body, executeOptions = {}) => {
    return execute({ body, ...executeOptions });
  }, [execute]);

  return {
    data,
    loading,
    error,
    post,
    reset,
  };
}

/**
 * Hook for PUT requests (update operations)
 * 
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Additional options
 * 
 * @returns {Object} - { data, loading, error, put }
 */
export function usePut(url, options = {}) {
  const { data, loading, error, execute, reset } = useApi({
    url,
    method: 'PUT',
    ...options,
  });

  const put = useCallback((body, executeOptions = {}) => {
    return execute({ body, ...executeOptions });
  }, [execute]);

  return {
    data,
    loading,
    error,
    put,
    reset,
  };
}

/**
 * Hook for DELETE requests
 * 
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Additional options
 * 
 * @returns {Object} - { loading, error, remove }
 */
export function useDelete(url, options = {}) {
  const { loading, error, execute, reset } = useApi({
    url,
    method: 'DELETE',
    ...options,
  });

  const remove = useCallback((executeOptions = {}) => {
    return execute(executeOptions);
  }, [execute]);

  return {
    loading,
    error,
    remove,
    reset,
  };
}

/**
 * Parse error response into a user-friendly message
 * 
 * @param {Error} error - The error object
 * @returns {Object} - { message, status, details }
 */
function parseError(error) {
  if (axios.isAxiosError(error)) {
    const response = error.response;
    
    if (response) {
      // Server responded with an error
      return {
        message: response.data?.detail || response.data?.message || getDefaultErrorMessage(response.status),
        status: response.status,
        details: response.data?.errors || response.data,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Unable to reach the server. Please check your internet connection.',
        status: 0,
        details: null,
      };
    }
  }
  
  // Something else went wrong
  return {
    message: error.message || 'An unexpected error occurred',
    status: null,
    details: null,
  };
}

/**
 * Get default error message based on HTTP status code
 * 
 * @param {number} status - HTTP status code
 * @returns {string} - User-friendly error message
 */
function getDefaultErrorMessage(status) {
  const messages = {
    400: 'Invalid request. Please check your input.',
    401: 'Please log in to continue.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    409: 'This operation conflicts with existing data.',
    422: 'The provided data is invalid.',
    429: 'Too many requests. Please try again later.',
    500: 'Server error. Please try again later.',
    502: 'Server is temporarily unavailable.',
    503: 'Service is temporarily unavailable.',
  };
  
  return messages[status] || `An error occurred (${status})`;
}

// Export the axios instance for direct use if needed
export { apiClient };

/**
 * Simple hook that returns HTTP method helpers using apiClient
 * Usage: const api = useApiHelpers();
 *        const response = await api.get('/url');
 */
export function useApiHelpers() {
  const get = async (url, config = {}) => {
    return apiClient.get(url, config);
  };

  const post = async (url, data, config = {}) => {
    return apiClient.post(url, data, config);
  };

  const put = async (url, data, config = {}) => {
    return apiClient.put(url, data, config);
  };

  const del = async (url, config = {}) => {
    return apiClient.delete(url, config);
  };

  return { get, post, put, delete: del };
}

// Default export
export default useApi;