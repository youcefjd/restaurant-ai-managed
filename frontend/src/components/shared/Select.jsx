import React, { forwardRef, useId } from 'react';
import PropTypes from 'prop-types';
import { ChevronDownIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

/**
 * Select - A reusable dropdown select component with label, validation, and accessibility support
 * 
 * Features:
 * - Customizable label and placeholder
 * - Error state with validation message
 * - Disabled state
 * - Required field indicator
 * - Full keyboard navigation
 * - Screen reader support with ARIA attributes
 * - Responsive design with TailwindCSS
 */
const Select = forwardRef(({
  // Core props
  name,
  value,
  onChange,
  options = [],
  
  // Label and description
  label,
  placeholder = 'Select an option',
  helperText,
  
  // Validation
  error,
  errorMessage,
  required = false,
  
  // State
  disabled = false,
  loading = false,
  
  // Styling
  className = '',
  size = 'md',
  fullWidth = true,
  
  // Accessibility
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy,
  
  // Additional props
  ...rest
}, ref) => {
  // Generate unique IDs for accessibility
  const uniqueId = useId();
  const selectId = `select-${uniqueId}`;
  const errorId = `select-error-${uniqueId}`;
  const helperId = `select-helper-${uniqueId}`;
  
  // Determine if there's an error to display
  const hasError = error || !!errorMessage;
  
  // Size variants for the select
  const sizeClasses = {
    sm: 'py-1.5 pl-3 pr-8 text-sm',
    md: 'py-2 pl-3 pr-10 text-sm',
    lg: 'py-3 pl-4 pr-12 text-base',
  };
  
  // Build the aria-describedby attribute
  const buildAriaDescribedBy = () => {
    const ids = [];
    if (ariaDescribedBy) ids.push(ariaDescribedBy);
    if (hasError) ids.push(errorId);
    if (helperText && !hasError) ids.push(helperId);
    return ids.length > 0 ? ids.join(' ') : undefined;
  };
  
  // Handle change event
  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    }
  };
  
  // Base select classes
  const baseSelectClasses = `
    block
    ${fullWidth ? 'w-full' : ''}
    rounded-md
    border
    bg-white
    shadow-sm
    appearance-none
    focus:outline-none
    focus:ring-2
    focus:ring-offset-0
    transition-colors
    duration-200
    ${sizeClasses[size] || sizeClasses.md}
  `;
  
  // State-specific classes
  const stateClasses = hasError
    ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500'
    : disabled
    ? 'border-gray-200 bg-gray-50 text-gray-500 cursor-not-allowed'
    : 'border-gray-300 text-gray-900 focus:border-indigo-500 focus:ring-indigo-500';
  
  // Combined select classes
  const selectClasses = `${baseSelectClasses} ${stateClasses} ${className}`.trim();
  
  return (
    <div className={`${fullWidth ? 'w-full' : 'inline-block'}`}>
      {/* Label */}
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && (
            <span className="text-red-500 ml-1" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}
      
      {/* Select wrapper for custom arrow icon */}
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          name={name}
          value={value}
          onChange={handleChange}
          disabled={disabled || loading}
          required={required}
          aria-label={!label ? ariaLabel : undefined}
          aria-invalid={hasError ? 'true' : 'false'}
          aria-describedby={buildAriaDescribedBy()}
          aria-required={required}
          className={selectClasses}
          {...rest}
        >
          {/* Placeholder option */}
          {placeholder && (
            <option value="" disabled>
              {loading ? 'Loading...' : placeholder}
            </option>
          )}
          
          {/* Options */}
          {options.map((option) => {
            // Handle both simple values and object options
            const optionValue = typeof option === 'object' ? option.value : option;
            const optionLabel = typeof option === 'object' ? option.label : option;
            const optionDisabled = typeof option === 'object' ? option.disabled : false;
            
            return (
              <option
                key={optionValue}
                value={optionValue}
                disabled={optionDisabled}
              >
                {optionLabel}
              </option>
            );
          })}
        </select>
        
        {/* Custom dropdown arrow */}
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          {hasError ? (
            <ExclamationCircleIcon
              className="h-5 w-5 text-red-500"
              aria-hidden="true"
            />
          ) : (
            <ChevronDownIcon
              className={`h-5 w-5 ${disabled ? 'text-gray-300' : 'text-gray-400'}`}
              aria-hidden="true"
            />
          )}
        </div>
        
        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-y-0 right-8 flex items-center">
            <svg
              className="animate-spin h-4 w-4 text-gray-400"
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
          </div>
        )}
      </div>
      
      {/* Error message */}
      {hasError && errorMessage && (
        <p
          id={errorId}
          className="mt-1 text-sm text-red-600"
          role="alert"
        >
          {errorMessage}
        </p>
      )}
      
      {/* Helper text (only shown when there's no error) */}
      {helperText && !hasError && (
        <p
          id={helperId}
          className="mt-1 text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

// Display name for debugging
Select.displayName = 'Select';

// PropTypes for runtime type checking
Select.propTypes = {
  /** Name attribute for the select element */
  name: PropTypes.string,
  /** Current selected value */
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /** Change handler function */
  onChange: PropTypes.func,
  /** Array of options - can be strings/numbers or objects with value, label, disabled */
  options: PropTypes.arrayOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
      PropTypes.shape({
        value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
        label: PropTypes.string.isRequired,
        disabled: PropTypes.bool,
      }),
    ])
  ),
  /** Label text displayed above the select */
  label: PropTypes.string,
  /** Placeholder text shown when no option is selected */
  placeholder: PropTypes.string,
  /** Helper text displayed below the select */
  helperText: PropTypes.string,
  /** Whether the select has an error */
  error: PropTypes.bool,
  /** Error message to display */
  errorMessage: PropTypes.string,
  /** Whether the field is required */
  required: PropTypes.bool,
  /** Whether the select is disabled */
  disabled: PropTypes.bool,
  /** Whether options are loading */
  loading: PropTypes.bool,
  /** Additional CSS classes */
  className: PropTypes.string,
  /** Size variant */
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  /** Whether the select should take full width */
  fullWidth: PropTypes.bool,
  /** Aria label for accessibility */
  'aria-label': PropTypes.string,
  /** Aria describedby for accessibility */
  'aria-describedby': PropTypes.string,
};

// Default props
Select.defaultProps = {
  options: [],
  placeholder: 'Select an option',
  required: false,
  disabled: false,
  loading: false,
  className: '',
  size: 'md',
  fullWidth: true,
};

export default Select;