import { Fragment, useRef, useEffect } from 'react';
import { ExclamationTriangleIcon, TrashIcon, XMarkIcon } from '@heroicons/react/24/outline';

/**
 * ConfirmDialog - A reusable confirmation dialog for destructive actions
 * 
 * Features:
 * - Modal overlay with backdrop
 * - Keyboard accessible (Escape to close, Tab trapping)
 * - Focus management
 * - Customizable title, message, and button text
 * - Loading state support
 * - Responsive design
 */

// Variant configurations for different types of confirmations
const variants = {
  danger: {
    icon: TrashIcon,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    buttonBg: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    iconBg: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    buttonBg: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
  },
};

function ConfirmDialog({
  isOpen = false,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed? This action cannot be undone.',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
}) {
  const dialogRef = useRef(null);
  const confirmButtonRef = useRef(null);
  const cancelButtonRef = useRef(null);

  // Get variant configuration
  const variantConfig = variants[variant] || variants.danger;
  const IconComponent = variantConfig.icon;

  // Handle escape key to close dialog
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when dialog is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, isLoading, onClose]);

  // Focus management - focus cancel button when dialog opens
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus();
    }
  }, [isOpen]);

  // Handle tab trapping within the dialog
  const handleKeyDown = (event) => {
    if (event.key === 'Tab') {
      const focusableElements = dialogRef.current?.querySelectorAll(
        'button:not([disabled])'
      );
      
      if (!focusableElements || focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    }
  };

  // Handle backdrop click
  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget && !isLoading) {
      onClose();
    }
  };

  // Handle confirm action
  const handleConfirm = async () => {
    if (isLoading) return;
    
    try {
      await onConfirm();
    } catch (error) {
      // Error handling should be done in the parent component
      console.error('Confirm action failed:', error);
    }
  };

  // Don't render if not open
  if (!isOpen) return null;

  return (
    <Fragment>
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 z-50 overflow-y-auto"
        aria-labelledby="confirm-dialog-title"
        role="dialog"
        aria-modal="true"
      >
        {/* Background overlay with click handler */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          aria-hidden="true"
          onClick={handleBackdropClick}
        />

        {/* Dialog positioning container */}
        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          {/* Dialog panel */}
          <div
            ref={dialogRef}
            className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg"
            onKeyDown={handleKeyDown}
          >
            {/* Close button for mobile */}
            <button
              type="button"
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-500 sm:hidden"
              onClick={onClose}
              disabled={isLoading}
              aria-label="Close dialog"
            >
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>

            {/* Dialog content */}
            <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
              <div className="sm:flex sm:items-start">
                {/* Icon */}
                <div
                  className={`mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${variantConfig.iconBg} sm:mx-0 sm:h-10 sm:w-10`}
                >
                  <IconComponent
                    className={`h-6 w-6 ${variantConfig.iconColor}`}
                    aria-hidden="true"
                  />
                </div>

                {/* Title and message */}
                <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                  <h3
                    id="confirm-dialog-title"
                    className="text-base font-semibold leading-6 text-gray-900"
                  >
                    {title}
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">{message}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
              {/* Confirm button */}
              <button
                ref={confirmButtonRef}
                type="button"
                className={`inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm sm:ml-3 sm:w-auto focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${variantConfig.buttonBg}`}
                onClick={handleConfirm}
                disabled={isLoading}
                aria-busy={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    {/* Loading spinner */}
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Processing...
                  </span>
                ) : (
                  confirmText
                )}
              </button>

              {/* Cancel button */}
              <button
                ref={cancelButtonRef}
                type="button"
                className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={onClose}
                disabled={isLoading}
              >
                {cancelText}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

export default ConfirmDialog;