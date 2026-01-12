import { forwardRef } from 'react';

/**
 * Spinner component for indicating loading states
 * Supports multiple sizes and can be used standalone or with text
 */
const Spinner = forwardRef(function Spinner(
  {
    size = 'md',
    color = 'primary',
    className = '',
    label = 'Loading...',
    showLabel = false,
    fullScreen = false,
    overlay = false,
  },
  ref
) {
  // Size mappings for the spinner
  const sizeClasses = {
    xs: 'h-3 w-3 border-[2px]',
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-[3px]',
    xl: 'h-16 w-16 border-4',
  };

  // Color mappings for the spinner border
  const colorClasses = {
    primary: 'border-blue-600 border-t-transparent',
    secondary: 'border-gray-600 border-t-transparent',
    white: 'border-white border-t-transparent',
    success: 'border-green-600 border-t-transparent',
    danger: 'border-red-600 border-t-transparent',
    warning: 'border-yellow-600 border-t-transparent',
  };

  // Label size mappings
  const labelSizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  // Base spinner element
  const spinnerElement = (
    <div
      ref={ref}
      role="status"
      aria-label={label}
      className={`inline-flex flex-col items-center justify-center ${className}`}
    >
      {/* Animated spinner circle */}
      <div
        className={`
          animate-spin 
          rounded-full 
          ${sizeClasses[size] || sizeClasses.md}
          ${colorClasses[color] || colorClasses.primary}
        `}
        aria-hidden="true"
      />
      
      {/* Visible label (optional) */}
      {showLabel && (
        <span
          className={`
            mt-2 
            ${labelSizeClasses[size] || labelSizeClasses.md}
            ${color === 'white' ? 'text-white' : 'text-gray-600'}
          `}
        >
          {label}
        </span>
      )}
      
      {/* Screen reader only label (always present for accessibility) */}
      {!showLabel && (
        <span className="sr-only">{label}</span>
      )}
    </div>
  );

  // Full screen centered spinner
  if (fullScreen) {
    return (
      <div
        className={`
          fixed 
          inset-0 
          z-50 
          flex 
          items-center 
          justify-center
          ${overlay ? 'bg-black/50' : 'bg-white'}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="Loading content"
      >
        {spinnerElement}
      </div>
    );
  }

  // Overlay spinner (for containers)
  if (overlay) {
    return (
      <div
        className="
          absolute 
          inset-0 
          z-10 
          flex 
          items-center 
          justify-center 
          bg-white/75 
          backdrop-blur-sm
        "
        role="dialog"
        aria-modal="true"
        aria-label="Loading content"
      >
        {spinnerElement}
      </div>
    );
  }

  // Default inline spinner
  return spinnerElement;
});

/**
 * PageSpinner - Full page loading spinner with centered layout
 * Use this when loading entire page content
 */
export function PageSpinner({ label = 'Loading page...' }) {
  return (
    <div 
      className="flex min-h-[400px] w-full items-center justify-center"
      role="status"
      aria-label={label}
    >
      <Spinner size="lg" showLabel label={label} />
    </div>
  );
}

/**
 * ButtonSpinner - Small spinner for use inside buttons
 * Use this to indicate button loading state
 */
export function ButtonSpinner({ className = '' }) {
  return (
    <Spinner 
      size="xs" 
      color="white" 
      className={className}
      label="Processing..."
    />
  );
}

/**
 * InlineSpinner - Inline spinner for text content
 * Use this when loading inline content
 */
export function InlineSpinner({ text = 'Loading...', className = '' }) {
  return (
    <span 
      className={`inline-flex items-center gap-2 ${className}`}
      role="status"
    >
      <Spinner size="xs" />
      <span className="text-sm text-gray-600">{text}</span>
    </span>
  );
}

/**
 * CardSpinner - Spinner for card/container overlays
 * Use this when loading content within a card or section
 */
export function CardSpinner({ label = 'Loading...' }) {
  return (
    <div 
      className="flex h-32 w-full items-center justify-center"
      role="status"
      aria-label={label}
    >
      <Spinner size="md" showLabel label={label} />
    </div>
  );
}

/**
 * TableRowSpinner - Spinner for table row loading states
 * Use this when loading table data
 */
export function TableRowSpinner({ colSpan = 1 }) {
  return (
    <tr>
      <td 
        colSpan={colSpan} 
        className="px-6 py-12 text-center"
      >
        <Spinner size="md" showLabel label="Loading data..." />
      </td>
    </tr>
  );
}

// Default export
export default Spinner;