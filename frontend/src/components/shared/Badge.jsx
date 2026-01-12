import React from 'react';
import PropTypes from 'prop-types';

/**
 * Badge component for displaying status indicators with color variants
 * 
 * @param {Object} props - Component props
 * @param {string} props.variant - Color variant: 'success', 'warning', 'error', 'info', 'neutral', 'primary'
 * @param {string} props.size - Size variant: 'sm', 'md', 'lg'
 * @param {React.ReactNode} props.children - Badge content
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.dot - Show a dot indicator before the text
 * @param {boolean} props.pill - Use pill shape (more rounded)
 * @param {string} props.ariaLabel - Accessible label for screen readers
 */
const Badge = ({
  variant = 'neutral',
  size = 'md',
  children,
  className = '',
  dot = false,
  pill = false,
  ariaLabel,
}) => {
  // Define color variants with background, text, and dot colors
  const variantStyles = {
    success: {
      base: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      dot: 'bg-green-500',
    },
    warning: {
      base: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      dot: 'bg-yellow-500',
    },
    error: {
      base: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      dot: 'bg-red-500',
    },
    info: {
      base: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      dot: 'bg-blue-500',
    },
    neutral: {
      base: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      dot: 'bg-gray-500',
    },
    primary: {
      base: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
      dot: 'bg-indigo-500',
    },
  };

  // Define size variants
  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  };

  // Define dot sizes based on badge size
  const dotSizes = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2 w-2',
    lg: 'h-2.5 w-2.5',
  };

  // Get the current variant styles, fallback to neutral if invalid
  const currentVariant = variantStyles[variant] || variantStyles.neutral;
  const currentSize = sizeStyles[size] || sizeStyles.md;
  const currentDotSize = dotSizes[size] || dotSizes.md;

  // Build the className string
  const badgeClasses = [
    'inline-flex items-center font-medium',
    currentVariant.base,
    currentSize,
    pill ? 'rounded-full' : 'rounded',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <span
      className={badgeClasses}
      role="status"
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
    >
      {/* Optional dot indicator */}
      {dot && (
        <span
          className={`${currentDotSize} ${currentVariant.dot} rounded-full mr-1.5 flex-shrink-0`}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
};

Badge.propTypes = {
  variant: PropTypes.oneOf(['success', 'warning', 'error', 'info', 'neutral', 'primary']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  dot: PropTypes.bool,
  pill: PropTypes.bool,
  ariaLabel: PropTypes.string,
};

/**
 * Predefined status badges for common booking/table states
 */

// Booking status badge
export const BookingStatusBadge = ({ status, ...props }) => {
  const statusConfig = {
    confirmed: { variant: 'success', label: 'Confirmed' },
    pending: { variant: 'warning', label: 'Pending' },
    cancelled: { variant: 'error', label: 'Cancelled' },
    completed: { variant: 'info', label: 'Completed' },
    'no-show': { variant: 'neutral', label: 'No Show' },
  };

  const config = statusConfig[status?.toLowerCase()] || { variant: 'neutral', label: status };

  return (
    <Badge variant={config.variant} dot {...props}>
      {config.label}
    </Badge>
  );
};

BookingStatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};

// Table status badge
export const TableStatusBadge = ({ status, ...props }) => {
  const statusConfig = {
    available: { variant: 'success', label: 'Available' },
    occupied: { variant: 'error', label: 'Occupied' },
    reserved: { variant: 'warning', label: 'Reserved' },
    maintenance: { variant: 'neutral', label: 'Maintenance' },
  };

  const config = statusConfig[status?.toLowerCase()] || { variant: 'neutral', label: status };

  return (
    <Badge variant={config.variant} dot {...props}>
      {config.label}
    </Badge>
  );
};

TableStatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};

// Restaurant status badge
export const RestaurantStatusBadge = ({ isActive, ...props }) => {
  return (
    <Badge variant={isActive ? 'success' : 'neutral'} dot {...props}>
      {isActive ? 'Active' : 'Inactive'}
    </Badge>
  );
};

RestaurantStatusBadge.propTypes = {
  isActive: PropTypes.bool.isRequired,
};

// Capacity badge (shows table capacity)
export const CapacityBadge = ({ capacity, ...props }) => {
  return (
    <Badge variant="primary" pill {...props}>
      {capacity} {capacity === 1 ? 'seat' : 'seats'}
    </Badge>
  );
};

CapacityBadge.propTypes = {
  capacity: PropTypes.number.isRequired,
};

// Count badge (for notifications, etc.)
export const CountBadge = ({ count, max = 99, ...props }) => {
  const displayCount = count > max ? `${max}+` : count;

  return (
    <Badge
      variant="error"
      size="sm"
      pill
      className="min-w-[1.25rem] justify-center"
      ariaLabel={`${count} items`}
      {...props}
    >
      {displayCount}
    </Badge>
  );
};

CountBadge.propTypes = {
  count: PropTypes.number.isRequired,
  max: PropTypes.number,
};

export default Badge;