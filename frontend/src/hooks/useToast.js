import { useState, useCallback, createContext, useContext } from 'react';

// Toast context for global state management
const ToastContext = createContext(null);

// Unique ID generator for toasts
let toastIdCounter = 0;
const generateToastId = () => {
  toastIdCounter += 1;
  return `toast-${toastIdCounter}-${Date.now()}`;
};

// Toast types for consistent styling
export const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// Default duration for toasts (in milliseconds)
const DEFAULT_DURATION = 5000;

/**
 * Custom hook for managing toast notifications
 * Provides methods to show, hide, and manage multiple toast notifications
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  /**
   * Remove a toast by its ID
   * @param {string} id - The unique identifier of the toast to remove
   */
  const removeToast = useCallback((id) => {
    setToasts((currentToasts) => 
      currentToasts.filter((toast) => toast.id !== id)
    );
  }, []);

  /**
   * Add a new toast notification
   * @param {Object} options - Toast configuration options
   * @param {string} options.message - The message to display
   * @param {string} options.type - The type of toast (success, error, warning, info)
   * @param {number} options.duration - How long the toast should be visible (ms)
   * @param {string} options.title - Optional title for the toast
   * @param {boolean} options.dismissible - Whether the toast can be manually dismissed
   * @param {Function} options.onClose - Callback function when toast is closed
   * @returns {string} The ID of the created toast
   */
  const addToast = useCallback(({
    message,
    type = TOAST_TYPES.INFO,
    duration = DEFAULT_DURATION,
    title = '',
    dismissible = true,
    onClose = null,
  }) => {
    const id = generateToastId();
    
    const newToast = {
      id,
      message,
      type,
      title,
      dismissible,
      onClose,
      createdAt: Date.now(),
    };

    setToasts((currentToasts) => [...currentToasts, newToast]);

    // Auto-remove toast after duration (if duration > 0)
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
        if (onClose) {
          onClose();
        }
      }, duration);
    }

    return id;
  }, [removeToast]);

  /**
   * Show a success toast
   * @param {string} message - The success message
   * @param {Object} options - Additional toast options
   */
  const success = useCallback((message, options = {}) => {
    return addToast({
      message,
      type: TOAST_TYPES.SUCCESS,
      title: options.title || 'Success',
      ...options,
    });
  }, [addToast]);

  /**
   * Show an error toast
   * @param {string} message - The error message
   * @param {Object} options - Additional toast options
   */
  const error = useCallback((message, options = {}) => {
    return addToast({
      message,
      type: TOAST_TYPES.ERROR,
      title: options.title || 'Error',
      duration: options.duration ?? 7000, // Errors stay longer by default
      ...options,
    });
  }, [addToast]);

  /**
   * Show a warning toast
   * @param {string} message - The warning message
   * @param {Object} options - Additional toast options
   */
  const warning = useCallback((message, options = {}) => {
    return addToast({
      message,
      type: TOAST_TYPES.WARNING,
      title: options.title || 'Warning',
      ...options,
    });
  }, [addToast]);

  /**
   * Show an info toast
   * @param {string} message - The info message
   * @param {Object} options - Additional toast options
   */
  const info = useCallback((message, options = {}) => {
    return addToast({
      message,
      type: TOAST_TYPES.INFO,
      title: options.title || 'Info',
      ...options,
    });
  }, [addToast]);

  /**
   * Show a loading toast that can be updated later
   * @param {string} message - The loading message
   * @param {Object} options - Additional toast options
   * @returns {Object} Object with update and dismiss methods
   */
  const loading = useCallback((message, options = {}) => {
    const id = addToast({
      message,
      type: TOAST_TYPES.INFO,
      title: options.title || 'Loading...',
      duration: 0, // Loading toasts don't auto-dismiss
      dismissible: false,
      ...options,
    });

    return {
      id,
      /**
       * Update the loading toast to show success
       * @param {string} successMessage - The success message
       */
      success: (successMessage) => {
        removeToast(id);
        success(successMessage);
      },
      /**
       * Update the loading toast to show error
       * @param {string} errorMessage - The error message
       */
      error: (errorMessage) => {
        removeToast(id);
        error(errorMessage);
      },
      /**
       * Dismiss the loading toast
       */
      dismiss: () => {
        removeToast(id);
      },
    };
  }, [addToast, removeToast, success, error]);

  /**
   * Clear all toasts
   */
  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  /**
   * Clear toasts by type
   * @param {string} type - The type of toasts to clear
   */
  const clearByType = useCallback((type) => {
    setToasts((currentToasts) => 
      currentToasts.filter((toast) => toast.type !== type)
    );
  }, []);

  /**
   * Promise-based toast for async operations
   * Shows loading, then success or error based on promise result
   * @param {Promise} promise - The promise to track
   * @param {Object} messages - Messages for different states
   * @param {string} messages.loading - Loading message
   * @param {string} messages.success - Success message
   * @param {string|Function} messages.error - Error message or function that receives error
   * @returns {Promise} The original promise
   */
  const promise = useCallback(async (promiseToTrack, messages = {}) => {
    const loadingToast = loading(messages.loading || 'Loading...');
    
    try {
      const result = await promiseToTrack;
      loadingToast.success(messages.success || 'Operation completed successfully');
      return result;
    } catch (err) {
      const errorMessage = typeof messages.error === 'function' 
        ? messages.error(err) 
        : messages.error || err.message || 'An error occurred';
      loadingToast.error(errorMessage);
      throw err;
    }
  }, [loading]);

  return {
    // Toast state
    toasts,
    
    // Basic methods
    addToast,
    removeToast,
    clearAll,
    clearByType,
    
    // Convenience methods
    success,
    error,
    warning,
    info,
    loading,
    promise,
  };
}

/**
 * Toast Provider component for context-based toast management
 * Wrap your app with this provider to use useToastContext
 */
export function ToastProvider({ children }) {
  const toast = useToast();
  
  return (
    <ToastContext.Provider value={toast}>
      {children}
    </ToastContext.Provider>
  );
}

/**
 * Hook to access toast context
 * Must be used within a ToastProvider
 */
export function useToastContext() {
  const context = useContext(ToastContext);
  
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  
  return context;
}

/**
 * Get the appropriate CSS classes for a toast type
 * @param {string} type - The toast type
 * @returns {Object} Object containing background, icon, and text color classes
 */
export function getToastStyles(type) {
  const styles = {
    [TOAST_TYPES.SUCCESS]: {
      background: 'bg-green-50 border-green-200',
      icon: 'text-green-500',
      title: 'text-green-800',
      message: 'text-green-700',
    },
    [TOAST_TYPES.ERROR]: {
      background: 'bg-red-50 border-red-200',
      icon: 'text-red-500',
      title: 'text-red-800',
      message: 'text-red-700',
    },
    [TOAST_TYPES.WARNING]: {
      background: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-500',
      title: 'text-yellow-800',
      message: 'text-yellow-700',
    },
    [TOAST_TYPES.INFO]: {
      background: 'bg-blue-50 border-blue-200',
      icon: 'text-blue-500',
      title: 'text-blue-800',
      message: 'text-blue-700',
    },
  };

  return styles[type] || styles[TOAST_TYPES.INFO];
}

/**
 * Get the icon name for a toast type (for use with @heroicons/react)
 * @param {string} type - The toast type
 * @returns {string} The icon name
 */
export function getToastIconName(type) {
  const icons = {
    [TOAST_TYPES.SUCCESS]: 'CheckCircleIcon',
    [TOAST_TYPES.ERROR]: 'XCircleIcon',
    [TOAST_TYPES.WARNING]: 'ExclamationTriangleIcon',
    [TOAST_TYPES.INFO]: 'InformationCircleIcon',
  };

  return icons[type] || icons[TOAST_TYPES.INFO];
}

export default useToast;