import { forwardRef } from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable Input component with label, validation, and error message display
 * Supports various input types and integrates with form validation
 */
const Input = forwardRef(({
  id,
  name,
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  error,
  helperText,
  required = false,
  disabled = false,
  readOnly = false,
  autoComplete,
  autoFocus = false,
  min,
  max,
  minLength,
  maxLength,
  pattern,
  step,
  className = '',
  inputClassName = '',
  labelClassName = '',
  icon,
  iconPosition = 'left',
  size = 'md',
  fullWidth = true,
  ...rest
}, ref) => {
  // Generate unique ID if not provided
  const inputId = id || `input-${name}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Size variants for the input
  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  // Base input classes
  const baseInputClasses = `
    block rounded-md border-0 shadow-sm ring-1 ring-inset
    placeholder:text-gray-400
    focus:ring-2 focus:ring-inset
    disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 disabled:ring-gray-200
    read-only:bg-gray-50 read-only:text-gray-500
    transition-colors duration-200
  `;

  // State-based ring colors
  const stateClasses = error
    ? 'ring-red-300 text-red-900 focus:ring-red-500'
    : 'ring-gray-300 text-gray-900 focus:ring-indigo-600';

  // Width classes
  const widthClasses = fullWidth ? 'w-full' : '';

  // Icon padding classes
  const iconPaddingClasses = icon
    ? iconPosition === 'left'
      ? 'pl-10'
      : 'pr-10'
    : '';

  // Combine all input classes
  const combinedInputClasses = `
    ${baseInputClasses}
    ${sizeClasses[size]}
    ${stateClasses}
    ${widthClasses}
    ${iconPaddingClasses}
    ${inputClassName}
  `.trim().replace(/\s+/g, ' ');

  // Label classes
  const baseLabelClasses = `
    block text-sm font-medium leading-6 text-gray-900 mb-1
    ${labelClassName}
  `.trim().replace(/\s+/g, ' ');

  // Handle input change
  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    }
  };

  // Handle input blur
  const handleBlur = (e) => {
    if (onBlur) {
      onBlur(e);
    }
  };

  // Handle input focus
  const handleFocus = (e) => {
    if (onFocus) {
      onFocus(e);
    }
  };

  return (
    <div className={`${fullWidth ? 'w-full' : ''} ${className}`}>
      {/* Label */}
      {label && (
        <label htmlFor={inputId} className={baseLabelClasses}>
          {label}
          {required && (
            <span className="text-red-500 ml-1" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}

      {/* Input wrapper for icon positioning */}
      <div className="relative">
        {/* Left icon */}
        {icon && iconPosition === 'left' && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <span className={`h-5 w-5 ${error ? 'text-red-400' : 'text-gray-400'}`}>
              {icon}
            </span>
          </div>
        )}

        {/* Input element */}
        <input
          ref={ref}
          id={inputId}
          name={name}
          type={type}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          readOnly={readOnly}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          min={min}
          max={max}
          minLength={minLength}
          maxLength={maxLength}
          pattern={pattern}
          step={step}
          className={combinedInputClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error
              ? `${inputId}-error`
              : helperText
              ? `${inputId}-helper`
              : undefined
          }
          aria-required={required}
          {...rest}
        />

        {/* Right icon */}
        {icon && iconPosition === 'right' && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <span className={`h-5 w-5 ${error ? 'text-red-400' : 'text-gray-400'}`}>
              {icon}
            </span>
          </div>
        )}

        {/* Error icon (shown when there's an error and no custom right icon) */}
        {error && iconPosition !== 'right' && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <svg
              className="h-5 w-5 text-red-500"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p
          id={`${inputId}-error`}
          className="mt-1.5 text-sm text-red-600"
          role="alert"
        >
          {error}
        </p>
      )}

      {/* Helper text (shown when there's no error) */}
      {helperText && !error && (
        <p
          id={`${inputId}-helper`}
          className="mt-1.5 text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

// Display name for debugging
Input.displayName = 'Input';

// PropTypes for runtime validation
Input.propTypes = {
  /** Unique identifier for the input */
  id: PropTypes.string,
  /** Name attribute for form submission */
  name: PropTypes.string.isRequired,
  /** Input type (text, email, password, number, tel, url, date, time, datetime-local) */
  type: PropTypes.oneOf([
    'text',
    'email',
    'password',
    'number',
    'tel',
    'url',
    'date',
    'time',
    'datetime-local',
    'search',
  ]),
  /** Label text displayed above the input */
  label: PropTypes.string,
  /** Placeholder text */
  placeholder: PropTypes.string,
  /** Current value of the input */
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /** Change handler function */
  onChange: PropTypes.func,
  /** Blur handler function */
  onBlur: PropTypes.func,
  /** Focus handler function */
  onFocus: PropTypes.func,
  /** Error message to display */
  error: PropTypes.string,
  /** Helper text displayed below the input */
  helperText: PropTypes.string,
  /** Whether the field is required */
  required: PropTypes.bool,
  /** Whether the input is disabled */
  disabled: PropTypes.bool,
  /** Whether the input is read-only */
  readOnly: PropTypes.bool,
  /** Autocomplete attribute value */
  autoComplete: PropTypes.string,
  /** Whether to autofocus on mount */
  autoFocus: PropTypes.bool,
  /** Minimum value (for number inputs) */
  min: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /** Maximum value (for number inputs) */
  max: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /** Minimum length for text inputs */
  minLength: PropTypes.number,
  /** Maximum length for text inputs */
  maxLength: PropTypes.number,
  /** Regex pattern for validation */
  pattern: PropTypes.string,
  /** Step value for number inputs */
  step: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /** Additional classes for the wrapper */
  className: PropTypes.string,
  /** Additional classes for the input element */
  inputClassName: PropTypes.string,
  /** Additional classes for the label */
  labelClassName: PropTypes.string,
  /** Icon element to display */
  icon: PropTypes.node,
  /** Position of the icon */
  iconPosition: PropTypes.oneOf(['left', 'right']),
  /** Size variant */
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  /** Whether the input should take full width */
  fullWidth: PropTypes.bool,
};

export default Input;