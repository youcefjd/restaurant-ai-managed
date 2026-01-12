import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

// Toast Context for global toast management
const ToastContext = createContext(null);

// Toast types configuration
const TOAST_TYPES = {
  success: {
    icon: CheckCircleIcon,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-400',
    iconColor: 'text-green-400',
    titleColor: 'text-green-800',
    messageColor: 'text-green-700',
  },
  error: {
    icon: XCircleIcon,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-400',
    iconColor: 'text-red-400',
    titleColor: 'text-red-800',
    messageColor: 'text-red-700',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-400',
    iconColor: 'text-yellow-400',
    titleColor: 'text-yellow-800',
    messageColor: 'text-yellow-700',
  },
  info: {
    icon: InformationCircleIcon,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-400',
    iconColor: 'text-blue-400',
    titleColor: 'text-blue-800',
    messageColor: 'text-blue-700',
  },
};

// Default duration for toast visibility (in milliseconds)
const DEFAULT_DURATION = 5000;

/**
 * Individual Toast Component
 * Displays a single toast notification with animation
 */
function ToastItem({ toast, onDismiss }) {
  const { id, type, title, message, duration = DEFAULT_DURATION } = toast;
  const config = TOAST_TYPES[type] || TOAST_TYPES.info;
  const Icon = config.icon;

  // Auto-dismiss after duration
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onDismiss]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={`
        w-full max-w-sm overflow-hidden rounded-lg border-l-4 shadow-lg
        ${config.bgColor} ${config.borderColor}
        transform transition-all duration-300 ease-in-out
        animate-slide-in
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          {/* Icon */}
          <div className="flex-shrink-0">
            <Icon className={`h-5 w-5 ${config.iconColor}`} aria-hidden="true" />
          </div>

          {/* Content */}
          <div className="ml-3 w-0 flex-1">
            {title && (
              <p className={`text-sm font-medium ${config.titleColor}`}>
                {title}
              </p>
            )}
            {message && (
              <p className={`mt-1 text-sm ${config.messageColor}`}>
                {message}
              </p>
            )}
          </div>

          {/* Dismiss button */}
          <div className="ml-4 flex flex-shrink-0">
            <button
              type="button"
              onClick={() => onDismiss(id)}
              className={`
                inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2
                ${config.titleColor} hover:opacity-75
                focus:ring-${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'yellow' : 'blue'}-500
              `}
              aria-label="Dismiss notification"
            >
              <span className="sr-only">Dismiss</span>
              <XMarkIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      {/* Progress bar for auto-dismiss */}
      {duration > 0 && (
        <div className="h-1 bg-gray-200">
          <div
            className={`h-full ${config.iconColor.replace('text-', 'bg-')} animate-progress`}
            style={{
              animationDuration: `${duration}ms`,
            }}
          />
        </div>
      )}
    </div>
  );
}

/**
 * Toast Container Component
 * Manages the display of multiple toasts
 */
function ToastContainer({ toasts, onDismiss, position = 'top-right' }) {
  // Position classes for the container
  const positionClasses = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'top-center': 'top-0 left-1/2 -translate-x-1/2',
    'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
  };

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      className={`
        fixed z-50 p-4 space-y-4 pointer-events-none
        ${positionClasses[position] || positionClasses['top-right']}
        sm:p-6
      `}
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
}

/**
 * Toast Provider Component
 * Provides toast context to the application
 */
export function ToastProvider({ children, position = 'top-right', maxToasts = 5 }) {
  const [toasts, setToasts] = useState([]);

  // Generate unique ID for each toast
  const generateId = useCallback(() => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add a new toast
  const addToast = useCallback(
    ({ type = 'info', title, message, duration = DEFAULT_DURATION }) => {
      const id = generateId();

      setToasts((prev) => {
        // Limit the number of toasts
        const newToasts = [...prev, { id, type, title, message, duration }];
        if (newToasts.length > maxToasts) {
          return newToasts.slice(-maxToasts);
        }
        return newToasts;
      });

      return id;
    },
    [generateId, maxToasts]
  );

  // Remove a toast by ID
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  // Clear all toasts
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Convenience methods for different toast types
  const success = useCallback(
    (message, title = 'Success') => addToast({ type: 'success', title, message }),
    [addToast]
  );

  const error = useCallback(
    (message, title = 'Error') => addToast({ type: 'error', title, message }),
    [addToast]
  );

  const warning = useCallback(
    (message, title = 'Warning') => addToast({ type: 'warning', title, message }),
    [addToast]
  );

  const info = useCallback(
    (message, title = 'Info') => addToast({ type: 'info', title, message }),
    [addToast]
  );

  const contextValue = {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    success,
    error,
    warning,
    info,
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} position={position} />
    </ToastContext.Provider>
  );
}

/**
 * Custom hook to use toast notifications
 * @returns Toast context methods
 */
export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  return context;
}

/**
 * Standalone Toast Component for direct usage
 * Can be used without the provider for simple cases
 */
export function Toast({
  type = 'info',
  title,
  message,
  isVisible = true,
  onDismiss,
  duration = DEFAULT_DURATION,
  className = '',
}) {
  const [visible, setVisible] = useState(isVisible);
  const config = TOAST_TYPES[type] || TOAST_TYPES.info;
  const Icon = config.icon;

  // Sync with external visibility prop
  useEffect(() => {
    setVisible(isVisible);
  }, [isVisible]);

  // Auto-dismiss after duration
  useEffect(() => {
    if (visible && duration > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        onDismiss?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [visible, duration, onDismiss]);

  const handleDismiss = () => {
    setVisible(false);
    onDismiss?.();
  };

  if (!visible) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={`
        w-full max-w-sm overflow-hidden rounded-lg border-l-4 shadow-lg
        ${config.bgColor} ${config.borderColor}
        ${className}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <Icon className={`h-5 w-5 ${config.iconColor}`} aria-hidden="true" />
          </div>

          <div className="ml-3 w-0 flex-1">
            {title && (
              <p className={`text-sm font-medium ${config.titleColor}`}>
                {title}
              </p>
            )}
            {message && (
              <p className={`mt-1 text-sm ${config.messageColor}`}>
                {message}
              </p>
            )}
          </div>

          {onDismiss && (
            <div className="ml-4 flex flex-shrink-0">
              <button
                type="button"
                onClick={handleDismiss}
                className={`
                  inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2
                  ${config.titleColor} hover:opacity-75
                `}
                aria-label="Dismiss notification"
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Add CSS animations to your global styles or tailwind config
// These styles should be added to your index.css or tailwind.config.js
const toastStyles = `
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes progress {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }

  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }

  .animate-progress {
    animation: progress linear forwards;
  }
`;

// Export styles for injection if needed
export { toastStyles };

// Default export
export default Toast;