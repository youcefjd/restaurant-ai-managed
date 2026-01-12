import React from 'react';
import PropTypes from 'prop-types';

/**
 * Card Component
 * 
 * A reusable container card component with optional header, footer, and various styling options.
 * Supports different variants, padding sizes, and interactive states.
 */
const Card = ({
  children,
  header,
  footer,
  title,
  subtitle,
  headerAction,
  variant = 'default',
  padding = 'default',
  shadow = 'default',
  rounded = 'default',
  border = true,
  hoverable = false,
  clickable = false,
  onClick,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledBy,
  role,
  ...rest
}) => {
  // Base card styles
  const baseStyles = 'bg-white overflow-hidden transition-all duration-200';

  // Variant styles
  const variantStyles = {
    default: 'bg-white',
    primary: 'bg-blue-50 border-blue-200',
    success: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    danger: 'bg-red-50 border-red-200',
    info: 'bg-cyan-50 border-cyan-200',
    dark: 'bg-gray-800 text-white',
  };

  // Padding styles
  const paddingStyles = {
    none: '',
    small: 'p-3',
    default: 'p-4 sm:p-6',
    large: 'p-6 sm:p-8',
  };

  // Body padding (when header or footer exists)
  const bodyPaddingStyles = {
    none: '',
    small: 'px-3 py-3',
    default: 'px-4 py-4 sm:px-6 sm:py-5',
    large: 'px-6 py-6 sm:px-8 sm:py-7',
  };

  // Shadow styles
  const shadowStyles = {
    none: '',
    small: 'shadow-sm',
    default: 'shadow',
    medium: 'shadow-md',
    large: 'shadow-lg',
    xl: 'shadow-xl',
  };

  // Rounded styles
  const roundedStyles = {
    none: '',
    small: 'rounded',
    default: 'rounded-lg',
    large: 'rounded-xl',
    full: 'rounded-3xl',
  };

  // Interactive styles
  const interactiveStyles = hoverable || clickable
    ? 'hover:shadow-lg hover:scale-[1.01] cursor-pointer'
    : '';

  // Border styles
  const borderStyles = border ? 'border border-gray-200' : '';

  // Combine all card styles
  const cardStyles = [
    baseStyles,
    variantStyles[variant] || variantStyles.default,
    !header && !footer ? paddingStyles[padding] : '',
    shadowStyles[shadow] || shadowStyles.default,
    roundedStyles[rounded] || roundedStyles.default,
    borderStyles,
    interactiveStyles,
    className,
  ].filter(Boolean).join(' ');

  // Header styles
  const headerStyles = [
    'px-4 py-4 sm:px-6',
    border ? 'border-b border-gray-200' : '',
    variant === 'dark' ? 'border-gray-700' : '',
    headerClassName,
  ].filter(Boolean).join(' ');

  // Body styles
  const bodyStyles = [
    header || footer ? bodyPaddingStyles[padding] : '',
    bodyClassName,
  ].filter(Boolean).join(' ');

  // Footer styles
  const footerStyles = [
    'px-4 py-4 sm:px-6',
    border ? 'border-t border-gray-200' : '',
    variant === 'dark' ? 'border-gray-700 bg-gray-900' : 'bg-gray-50',
    footerClassName,
  ].filter(Boolean).join(' ');

  // Handle click events
  const handleClick = (event) => {
    if (clickable && onClick) {
      onClick(event);
    }
  };

  // Handle keyboard events for accessibility
  const handleKeyDown = (event) => {
    if (clickable && onClick && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      onClick(event);
    }
  };

  // Determine the appropriate role
  const cardRole = role || (clickable ? 'button' : undefined);

  // Render header section
  const renderHeader = () => {
    // If custom header is provided, use it
    if (header) {
      return (
        <div className={headerStyles}>
          {header}
        </div>
      );
    }

    // If title is provided, render default header structure
    if (title) {
      return (
        <div className={headerStyles}>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="min-w-0 flex-1">
              <h3 
                className={`text-lg font-semibold leading-6 ${
                  variant === 'dark' ? 'text-white' : 'text-gray-900'
                }`}
                id={ariaLabelledBy}
              >
                {title}
              </h3>
              {subtitle && (
                <p 
                  className={`mt-1 text-sm ${
                    variant === 'dark' ? 'text-gray-300' : 'text-gray-500'
                  }`}
                >
                  {subtitle}
                </p>
              )}
            </div>
            {headerAction && (
              <div className="flex-shrink-0">
                {headerAction}
              </div>
            )}
          </div>
        </div>
      );
    }

    return null;
  };

  // Render footer section
  const renderFooter = () => {
    if (!footer) return null;

    return (
      <div className={footerStyles}>
        {footer}
      </div>
    );
  };

  // Render body section
  const renderBody = () => {
    if (!children) return null;

    // If no header or footer, children are rendered directly in the card
    if (!header && !footer && !title) {
      return children;
    }

    return (
      <div className={bodyStyles}>
        {children}
      </div>
    );
  };

  return (
    <div
      className={cardStyles}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role={cardRole}
      tabIndex={clickable ? 0 : undefined}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      {...rest}
    >
      {renderHeader()}
      {renderBody()}
      {renderFooter()}
    </div>
  );
};

// PropTypes for runtime type checking
Card.propTypes = {
  /** Card content */
  children: PropTypes.node,
  /** Custom header content (overrides title/subtitle) */
  header: PropTypes.node,
  /** Footer content */
  footer: PropTypes.node,
  /** Card title (renders default header) */
  title: PropTypes.string,
  /** Card subtitle (shown below title) */
  subtitle: PropTypes.string,
  /** Action element in header (button, link, etc.) */
  headerAction: PropTypes.node,
  /** Card color variant */
  variant: PropTypes.oneOf(['default', 'primary', 'success', 'warning', 'danger', 'info', 'dark']),
  /** Padding size */
  padding: PropTypes.oneOf(['none', 'small', 'default', 'large']),
  /** Shadow size */
  shadow: PropTypes.oneOf(['none', 'small', 'default', 'medium', 'large', 'xl']),
  /** Border radius */
  rounded: PropTypes.oneOf(['none', 'small', 'default', 'large', 'full']),
  /** Show border */
  border: PropTypes.bool,
  /** Add hover effect */
  hoverable: PropTypes.bool,
  /** Make card clickable */
  clickable: PropTypes.bool,
  /** Click handler (required if clickable) */
  onClick: PropTypes.func,
  /** Additional CSS classes for card */
  className: PropTypes.string,
  /** Additional CSS classes for header */
  headerClassName: PropTypes.string,
  /** Additional CSS classes for body */
  bodyClassName: PropTypes.string,
  /** Additional CSS classes for footer */
  footerClassName: PropTypes.string,
  /** Accessibility label */
  'aria-label': PropTypes.string,
  /** ID of element that labels this card */
  'aria-labelledby': PropTypes.string,
  /** ARIA role */
  role: PropTypes.string,
};

// Default props
Card.defaultProps = {
  variant: 'default',
  padding: 'default',
  shadow: 'default',
  rounded: 'default',
  border: true,
  hoverable: false,
  clickable: false,
  className: '',
  headerClassName: '',
  bodyClassName: '',
  footerClassName: '',
};

/**
 * Card.Header - Standalone header component for more complex headers
 */
Card.Header = ({ children, className = '', ...rest }) => (
  <div 
    className={`px-4 py-4 sm:px-6 border-b border-gray-200 ${className}`}
    {...rest}
  >
    {children}
  </div>
);

Card.Header.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

Card.Header.displayName = 'Card.Header';

/**
 * Card.Body - Standalone body component
 */
Card.Body = ({ children, className = '', padding = 'default', ...rest }) => {
  const paddingStyles = {
    none: '',
    small: 'px-3 py-3',
    default: 'px-4 py-4 sm:px-6 sm:py-5',
    large: 'px-6 py-6 sm:px-8 sm:py-7',
  };

  return (
    <div 
      className={`${paddingStyles[padding]} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
};

Card.Body.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  padding: PropTypes.oneOf(['none', 'small', 'default', 'large']),
};

Card.Body.displayName = 'Card.Body';

/**
 * Card.Footer - Standalone footer component
 */
Card.Footer = ({ children, className = '', align = 'right', ...rest }) => {
  const alignStyles = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
  };

  return (
    <div 
      className={`px-4 py-4 sm:px-6 border-t border-gray-200 bg-gray-50 flex items-center ${alignStyles[align]} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
};

Card.Footer.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  align: PropTypes.oneOf(['left', 'center', 'right', 'between']),
};

Card.Footer.displayName = 'Card.Footer';

/**
 * Card.Title - Title component for card headers
 */
Card.Title = ({ children, as: Component = 'h3', className = '', ...rest }) => (
  <Component 
    className={`text-lg font-semibold leading-6 text-gray-900 ${className}`}
    {...rest}
  >
    {children}
  </Component>
);

Card.Title.propTypes = {
  children: PropTypes.node.isRequired,
  as: PropTypes.elementType,
  className: PropTypes.string,
};

Card.Title.displayName = 'Card.Title';

/**
 * Card.Description - Description/subtitle component
 */
Card.Description = ({ children, className = '', ...rest }) => (
  <p 
    className={`mt-1 text-sm text-gray-500 ${className}`}
    {...rest}
  >
    {children}
  </p>
);

Card.Description.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

Card.Description.displayName = 'Card.Description';

export default Card;