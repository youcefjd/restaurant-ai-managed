import { Fragment, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { XMarkIcon } from '@heroicons/react/24/outline';

/**
 * Reusable Modal component with header, body, and footer sections
 * Supports multiple sizes, custom styling, and accessibility features
 */
const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className = '',
  overlayClassName = '',
  contentClassName = '',
}) => {
  // Handle escape key press
  const handleEscapeKey = useCallback(
    (event) => {
      if (closeOnEscape && event.key === 'Escape') {
        onClose();
      }
    },
    [closeOnEscape, onClose]
  );

  // Handle overlay click
  const handleOverlayClick = (event) => {
    if (closeOnOverlayClick && event.target === event.currentTarget) {
      onClose();
    }
  };

  // Add/remove event listeners and manage body scroll
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'hidden';
      
      // Focus trap - focus the modal when it opens
      const modal = document.getElementById('modal-content');
      if (modal) {
        modal.focus();
      }
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleEscapeKey]);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  // Size classes mapping
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    full: 'max-w-full mx-4',
  };

  return (
    <Fragment>
      {/* Overlay */}
      <div
        className={`
          fixed inset-0 z-50 overflow-y-auto
          ${overlayClassName}
        `}
        aria-labelledby="modal-title"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          {/* Background overlay */}
          <div
            className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
            aria-hidden="true"
            onClick={handleOverlayClick}
          />

          {/* Center modal trick */}
          <span
            className="hidden sm:inline-block sm:h-screen sm:align-middle"
            aria-hidden="true"
          >
            &#8203;
          </span>

          {/* Modal content */}
          <div
            id="modal-content"
            tabIndex={-1}
            className={`
              inline-block transform overflow-hidden rounded-lg bg-white text-left
              align-bottom shadow-xl transition-all
              sm:my-8 sm:w-full sm:align-middle
              ${sizeClasses[size] || sizeClasses.md}
              ${contentClassName}
              ${className}
            `}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            {(title || showCloseButton) && (
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 sm:px-6">
                {title && (
                  <h3
                    id="modal-title"
                    className="text-lg font-semibold leading-6 text-gray-900"
                  >
                    {title}
                  </h3>
                )}
                {showCloseButton && (
                  <button
                    type="button"
                    className="
                      ml-auto rounded-md bg-white text-gray-400
                      hover:text-gray-500 focus:outline-none focus:ring-2
                      focus:ring-indigo-500 focus:ring-offset-2
                      transition-colors duration-200
                    "
                    onClick={onClose}
                    aria-label="Close modal"
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                )}
              </div>
            )}

            {/* Body */}
            <div className="px-4 py-4 sm:px-6">{children}</div>

            {/* Footer */}
            {footer && (
              <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 sm:px-6">
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>
    </Fragment>
  );
};

// PropTypes for runtime type checking
Modal.propTypes = {
  /** Controls whether the modal is visible */
  isOpen: PropTypes.bool.isRequired,
  /** Callback function when modal should close */
  onClose: PropTypes.func.isRequired,
  /** Modal title displayed in the header */
  title: PropTypes.node,
  /** Modal body content */
  children: PropTypes.node.isRequired,
  /** Footer content (typically action buttons) */
  footer: PropTypes.node,
  /** Modal size variant */
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', 'full']),
  /** Whether clicking the overlay closes the modal */
  closeOnOverlayClick: PropTypes.bool,
  /** Whether pressing Escape closes the modal */
  closeOnEscape: PropTypes.bool,
  /** Whether to show the close button in header */
  showCloseButton: PropTypes.bool,
  /** Additional CSS classes for the modal container */
  className: PropTypes.string,
  /** Additional CSS classes for the overlay */
  overlayClassName: PropTypes.string,
  /** Additional CSS classes for the content wrapper */
  contentClassName: PropTypes.string,
};

/**
 * Modal Header subcomponent for custom header content
 */
export const ModalHeader = ({ children, className = '' }) => (
  <div className={`border-b border-gray-200 px-4 py-3 sm:px-6 ${className}`}>
    {children}
  </div>
);

ModalHeader.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

/**
 * Modal Body subcomponent for custom body content
 */
export const ModalBody = ({ children, className = '' }) => (
  <div className={`px-4 py-4 sm:px-6 ${className}`}>{children}</div>
);

ModalBody.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

/**
 * Modal Footer subcomponent with common button layouts
 */
export const ModalFooter = ({
  children,
  className = '',
  align = 'right',
}) => {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
  };

  return (
    <div
      className={`
        flex items-center gap-3
        ${alignClasses[align] || alignClasses.right}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

ModalFooter.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  align: PropTypes.oneOf(['left', 'center', 'right', 'between']),
};

/**
 * Confirmation Modal - A preset modal for confirm/cancel dialogs
 */
export const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'danger',
  isLoading = false,
}) => {
  const confirmButtonClasses = {
    danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
    primary: 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500',
    success: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
    warning: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <ModalFooter>
          <button
            type="button"
            className="
              inline-flex justify-center rounded-md border border-gray-300
              bg-white px-4 py-2 text-sm font-medium text-gray-700
              shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2
              focus:ring-indigo-500 focus:ring-offset-2
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors duration-200
            "
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={`
              inline-flex justify-center rounded-md border border-transparent
              px-4 py-2 text-sm font-medium text-white shadow-sm
              focus:outline-none focus:ring-2 focus:ring-offset-2
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors duration-200
              ${confirmButtonClasses[confirmVariant] || confirmButtonClasses.primary}
            `}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
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
              </>
            ) : (
              confirmText
            )}
          </button>
        </ModalFooter>
      }
    >
      <p className="text-sm text-gray-500">{message}</p>
    </Modal>
  );
};

ConfirmModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  title: PropTypes.string,
  message: PropTypes.node.isRequired,
  confirmText: PropTypes.string,
  cancelText: PropTypes.string,
  confirmVariant: PropTypes.oneOf(['danger', 'primary', 'success', 'warning']),
  isLoading: PropTypes.bool,
};

export default Modal;