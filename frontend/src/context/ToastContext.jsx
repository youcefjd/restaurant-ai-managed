import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

// Toast types for different notification styles
const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// Default duration for toast notifications (in milliseconds)
const DEFAULT_DURATION = 5000;

// Create the context
const ToastContext = createContext(null);

/**
 * Generate a unique ID for each toast
 * @returns {string} Unique identifier
 */
const generateId = () => {
  return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Get icon based on toast type
 * @param {string} type - Toast type
 * @returns {JSX.Element} Icon component
 */
const ToastIcon = ({ type }) => {
  switch (type) {
    case TOAST_TYPES.SUCCESS:
      return (
        <svg
          className="h-5 w-5 text-green-400"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
            clipRule="evenodd"
          />
        </svg>
      );
    case TOAST_TYPES.ERROR:
      return (
        <svg
          className="h-5 w-5 text-red-400"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
            clipRule="evenodd"
          />
        </svg>
      );
    case TOAST_TYPES.WARNING:
      return (
        <svg
          className="h-5 w-5 text-yellow-400"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
      );
    case TOAST_TYPES.INFO:
    default:
      return (
        <svg
          className="h-5 w-5 text-blue-400"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
            clipRule="evenodd"
          />
        </svg>
      );
  }
};

/**
 * Get background color classes based on toast type
 * @param {string} type - Toast type
 * @returns {string} Tailwind CSS classes
 */
const getToastStyles = (type) => {
  switch (type) {
    case TOAST_TYPES.SUCCESS:
      return 'bg-green-50 border-green-200';
    case TOAST_TYPES.ERROR:
      return 'bg-red-50 border-red-200';
    case TOAST_TYPES.WARNING:
      return 'bg-yellow-50 border-yellow-200';
    case TOAST_TYPES.INFO:
    default:
      return 'bg-blue-50 border-blue-200';
  }
};

/**
 * Individual Toast Component
 */
const Toast = ({ toast, onDismiss }) => {
  const [isExiting, setIsExiting] = useState(false);

  // Handle dismiss with animation
  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(toast.id);
    }, 300); // Match animation duration
  }, [toast.id, onDismiss]);

  // Auto-dismiss after duration
  useEffect(() => {
    if (toast.duration !== Infinity) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, toast.duration || DEFAULT_DURATION);

      return () => clearTimeout(timer);
    }
  }, [toast.duration, handleDismiss]);

  return (
    <div
      role="alert"
      aria-live="polite"
      aria-atomic="true"
      className={`
        pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border shadow-lg
        transform transition-all duration-300 ease-in-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
        ${getToastStyles(toast.type)}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <ToastIcon type={toast.type} />
          </div>
          <div className="ml-3 w-0 flex-1">
            {toast.title && (
              <p className="text-sm font-medium text-gray-900">{toast.title}</p>
            )}
            <p className={`text-sm text-gray-600 ${toast.title ? 'mt-1' : ''}`}>
              {toast.message}
            </p>
            {toast.action && (
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => {
                    toast.action.onClick();
                    handleDismiss();
                  }}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
                >
                  {toast.action.label}
                </button>
              </div>
            )}
          </div>
          <div className="ml-4 flex flex-shrink-0">
            <button
              type="button"
              onClick={handleDismiss}
              className="inline-flex rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              aria-label="Dismiss notification"
            >
              <span className="sr-only">Close</span>
              <svg
                className="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Toast Container Component - renders all active toasts
 */
const ToastContainer = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="assertive"
      className="pointer-events-none fixed inset-0 z-50 flex flex-col items-end px-4 py-6 sm:items-end sm:p-6"
    >
      <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </div>
    </div>
  );
};

/**
 * Toast Provider Component
 * Wraps the application and provides toast notification functionality
 */
export const ToastProvider = ({ children, maxToasts = 5 }) => {
  const [toasts, setToasts] = useState([]);

  /**
   * Add a new toast notification
   * @param {Object} options - Toast options
   * @param {string} options.type - Toast type (success, error, warning, info)
   * @param {string} options.message - Toast message
   * @param {string} [options.title] - Optional toast title
   * @param {number} [options.duration] - Duration in ms (default: 5000, use Infinity for persistent)
   * @param {Object} [options.action] - Optional action button
   * @param {string} options.action.label - Action button label
   * @param {Function} options.action.onClick - Action button click handler
   * @returns {string} Toast ID
   */
  const addToast = useCallback(
    ({ type = TOAST_TYPES.INFO, message, title, duration = DEFAULT_DURATION, action }) => {
      const id = generateId();

      setToasts((prevToasts) => {
        // Remove oldest toasts if we exceed maxToasts
        const newToasts = [...prevToasts, { id, type, message, title, duration, action }];
        if (newToasts.length > maxToasts) {
          return newToasts.slice(-maxToasts);
        }
        return newToasts;
      });

      return id;
    },
    [maxToasts]
  );

  /**
   * Remove a toast by ID
   * @param {string} id - Toast ID to remove
   */
  const removeToast = useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);

  /**
   * Remove all toasts
   */
  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Convenience methods for different toast types
  const success = useCallback(
    (message, options = {}) => addToast({ ...options, type: TOAST_TYPES.SUCCESS, message }),
    [addToast]
  );

  const error = useCallback(
    (message, options = {}) => addToast({ ...options, type: TOAST_TYPES.ERROR, message }),
    [addToast]
  );

  const warning = useCallback(
    (message, options = {}) => addToast({ ...options, type: TOAST_TYPES.WARNING, message }),
    [addToast]
  );

  const info = useCallback(
    (message, options = {}) => addToast({ ...options, type: TOAST_TYPES.INFO, message }),
    [addToast]
  );

  // Context value with all toast methods
  const contextValue = {
    toasts,
    addToast,
    removeToast,
    clearAllToasts,
    success,
    error,
    warning,
    info,
    TOAST_TYPES,
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </ToastContext.Provider>
  );
};

/**
 * Custom hook to use toast notifications
 * @returns {Object} Toast context with methods
 * @throws {Error} If used outside of ToastProvider
 */
export const useToast = () => {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  return context;
};

// Export toast types for external use
export { TOAST_TYPES };

export default ToastContext;