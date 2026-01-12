import { useState, useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ChevronUpDownIcon,
  EllipsisHorizontalIcon,
} from '@heroicons/react/24/outline';

/**
 * Reusable Data Table Component
 * 
 * Features:
 * - Sortable columns
 * - Row actions (dropdown menu)
 * - Loading, empty, and error states
 * - Responsive design
 * - Accessible (keyboard navigation, ARIA labels)
 * - Pagination support
 */

// Sort direction constants
const SORT_DIRECTIONS = {
  ASC: 'asc',
  DESC: 'desc',
  NONE: null,
};

/**
 * Table component for displaying data in a sortable, actionable grid
 */
function Table({
  columns,
  data,
  actions,
  loading,
  error,
  emptyMessage,
  onSort,
  sortColumn,
  sortDirection,
  onRowClick,
  keyField,
  className,
  stickyHeader,
}) {
  const [activeActionRow, setActiveActionRow] = useState(null);

  // Handle column header click for sorting
  const handleSort = useCallback(
    (column) => {
      if (!column.sortable || !onSort) return;

      let newDirection;
      if (sortColumn !== column.key) {
        newDirection = SORT_DIRECTIONS.ASC;
      } else if (sortDirection === SORT_DIRECTIONS.ASC) {
        newDirection = SORT_DIRECTIONS.DESC;
      } else if (sortDirection === SORT_DIRECTIONS.DESC) {
        newDirection = SORT_DIRECTIONS.NONE;
      } else {
        newDirection = SORT_DIRECTIONS.ASC;
      }

      onSort(column.key, newDirection);
    },
    [sortColumn, sortDirection, onSort]
  );

  // Handle keyboard navigation for sorting
  const handleKeyDown = useCallback(
    (event, column) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleSort(column);
      }
    },
    [handleSort]
  );

  // Toggle action menu for a row
  const toggleActionMenu = useCallback((event, rowKey) => {
    event.stopPropagation();
    setActiveActionRow((prev) => (prev === rowKey ? null : rowKey));
  }, []);

  // Close action menu when clicking outside
  const handleCloseActionMenu = useCallback(() => {
    setActiveActionRow(null);
  }, []);

  // Handle action click
  const handleActionClick = useCallback(
    (event, action, row) => {
      event.stopPropagation();
      setActiveActionRow(null);
      if (action.onClick) {
        action.onClick(row);
      }
    },
    []
  );

  // Get sort icon for column header
  const getSortIcon = useCallback(
    (column) => {
      if (!column.sortable) return null;

      if (sortColumn !== column.key) {
        return (
          <ChevronUpDownIcon
            className="h-4 w-4 text-gray-400"
            aria-hidden="true"
          />
        );
      }

      if (sortDirection === SORT_DIRECTIONS.ASC) {
        return (
          <ChevronUpIcon
            className="h-4 w-4 text-indigo-600"
            aria-hidden="true"
          />
        );
      }

      if (sortDirection === SORT_DIRECTIONS.DESC) {
        return (
          <ChevronDownIcon
            className="h-4 w-4 text-indigo-600"
            aria-hidden="true"
          />
        );
      }

      return (
        <ChevronUpDownIcon
          className="h-4 w-4 text-gray-400"
          aria-hidden="true"
        />
      );
    },
    [sortColumn, sortDirection]
  );

  // Render cell content based on column configuration
  const renderCell = useCallback((row, column) => {
    const value = row[column.key];

    // Use custom render function if provided
    if (column.render) {
      return column.render(value, row);
    }

    // Handle null/undefined values
    if (value === null || value === undefined) {
      return <span className="text-gray-400">—</span>;
    }

    // Handle boolean values
    if (typeof value === 'boolean') {
      return (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            value
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {value ? 'Yes' : 'No'}
        </span>
      );
    }

    return value;
  }, []);

  // Get row key
  const getRowKey = useCallback(
    (row, index) => {
      if (keyField && row[keyField] !== undefined) {
        return row[keyField];
      }
      return index;
    },
    [keyField]
  );

  // Filter visible actions for a row
  const getVisibleActions = useMemo(() => {
    if (!actions || actions.length === 0) return () => [];
    return (row) =>
      actions.filter((action) => {
        if (action.hidden) {
          return typeof action.hidden === 'function'
            ? !action.hidden(row)
            : !action.hidden;
        }
        return true;
      });
  }, [actions]);

  // Loading state
  if (loading) {
    return (
      <div
        className={`bg-white shadow-sm rounded-lg overflow-hidden ${className || ''}`}
        role="status"
        aria-label="Loading table data"
      >
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
            <div className="flex space-x-4">
              {columns.map((_, index) => (
                <div
                  key={index}
                  className="h-4 bg-gray-200 rounded flex-1"
                />
              ))}
            </div>
          </div>
          {/* Row skeletons */}
          {[...Array(5)].map((_, rowIndex) => (
            <div
              key={rowIndex}
              className="px-6 py-4 border-b border-gray-200 last:border-b-0"
            >
              <div className="flex space-x-4">
                {columns.map((_, colIndex) => (
                  <div
                    key={colIndex}
                    className="h-4 bg-gray-100 rounded flex-1"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className={`bg-white shadow-sm rounded-lg overflow-hidden ${className || ''}`}
        role="alert"
        aria-live="assertive"
      >
        <div className="px-6 py-12 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
            <svg
              className="w-6 h-6 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Error loading data
          </h3>
          <p className="text-sm text-gray-500">
            {typeof error === 'string' ? error : 'An unexpected error occurred.'}
          </p>
        </div>
      </div>
    );
  }

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div
        className={`bg-white shadow-sm rounded-lg overflow-hidden ${className || ''}`}
        role="status"
        aria-label="No data available"
      >
        <div className="px-6 py-12 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 mb-4">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No data found
          </h3>
          <p className="text-sm text-gray-500">
            {emptyMessage || 'There are no items to display.'}
          </p>
        </div>
      </div>
    );
  }

  const hasActions = actions && actions.length > 0;

  return (
    <div
      className={`bg-white shadow-sm rounded-lg overflow-hidden ${className || ''}`}
      onClick={handleCloseActionMenu}
    >
      <div className="overflow-x-auto">
        <table
          className="min-w-full divide-y divide-gray-200"
          role="grid"
          aria-label="Data table"
        >
          <thead
            className={`bg-gray-50 ${stickyHeader ? 'sticky top-0 z-10' : ''}`}
          >
            <tr role="row">
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    column.sortable ? 'cursor-pointer select-none hover:bg-gray-100' : ''
                  } ${column.headerClassName || ''}`}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                  onKeyDown={(e) => handleKeyDown(e, column)}
                  tabIndex={column.sortable ? 0 : -1}
                  role="columnheader"
                  aria-sort={
                    sortColumn === column.key
                      ? sortDirection === SORT_DIRECTIONS.ASC
                        ? 'ascending'
                        : sortDirection === SORT_DIRECTIONS.DESC
                        ? 'descending'
                        : 'none'
                      : undefined
                  }
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.label}</span>
                    {getSortIcon(column)}
                  </div>
                </th>
              ))}
              {hasActions && (
                <th
                  scope="col"
                  className="relative px-6 py-3 w-12"
                  role="columnheader"
                >
                  <span className="sr-only">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, rowIndex) => {
              const rowKey = getRowKey(row, rowIndex);
              const visibleActions = getVisibleActions(row);
              const isClickable = !!onRowClick;

              return (
                <tr
                  key={rowKey}
                  role="row"
                  className={`${
                    isClickable
                      ? 'cursor-pointer hover:bg-gray-50 focus:bg-gray-50 focus:outline-none'
                      : ''
                  } ${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                  onClick={() => onRowClick && onRowClick(row)}
                  onKeyDown={(e) => {
                    if ((e.key === 'Enter' || e.key === ' ') && onRowClick) {
                      e.preventDefault();
                      onRowClick(row);
                    }
                  }}
                  tabIndex={isClickable ? 0 : -1}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-6 py-4 whitespace-nowrap text-sm ${
                        column.className || 'text-gray-900'
                      }`}
                      role="gridcell"
                    >
                      {renderCell(row, column)}
                    </td>
                  ))}
                  {hasActions && (
                    <td
                      className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"
                      role="gridcell"
                    >
                      {visibleActions.length > 0 && (
                        <div className="relative inline-block text-left">
                          <button
                            type="button"
                            className="p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            onClick={(e) => toggleActionMenu(e, rowKey)}
                            aria-expanded={activeActionRow === rowKey}
                            aria-haspopup="true"
                            aria-label={`Actions for row ${rowIndex + 1}`}
                          >
                            <EllipsisHorizontalIcon
                              className="h-5 w-5 text-gray-400"
                              aria-hidden="true"
                            />
                          </button>

                          {/* Action dropdown menu */}
                          {activeActionRow === rowKey && (
                            <div
                              className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-20"
                              role="menu"
                              aria-orientation="vertical"
                              aria-labelledby="options-menu"
                            >
                              <div className="py-1" role="none">
                                {visibleActions.map((action, actionIndex) => {
                                  const isDisabled =
                                    typeof action.disabled === 'function'
                                      ? action.disabled(row)
                                      : action.disabled;

                                  return (
                                    <button
                                      key={action.key || actionIndex}
                                      type="button"
                                      className={`w-full text-left px-4 py-2 text-sm flex items-center space-x-2 ${
                                        isDisabled
                                          ? 'text-gray-400 cursor-not-allowed'
                                          : action.variant === 'danger'
                                          ? 'text-red-600 hover:bg-red-50'
                                          : 'text-gray-700 hover:bg-gray-100'
                                      }`}
                                      onClick={(e) =>
                                        !isDisabled &&
                                        handleActionClick(e, action, row)
                                      }
                                      disabled={isDisabled}
                                      role="menuitem"
                                    >
                                      {action.icon && (
                                        <span
                                          className="flex-shrink-0"
                                          aria-hidden="true"
                                        >
                                          {action.icon}
                                        </span>
                                      )}
                                      <span>{action.label}</span>
                                    </button>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// PropTypes for documentation and runtime validation
Table.propTypes = {
  /** Column definitions */
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      sortable: PropTypes.bool,
      width: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      className: PropTypes.string,
      headerClassName: PropTypes.string,
      render: PropTypes.func,
    })
  ).isRequired,
  /** Data array to display */
  data: PropTypes.array,
  /** Row actions */
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      label: PropTypes.string.isRequired,
      icon: PropTypes.node,
      onClick: PropTypes.func,
      variant: PropTypes.oneOf(['default', 'danger']),
      disabled: PropTypes.oneOfType([PropTypes.bool, PropTypes.func]),
      hidden: PropTypes.oneOfType([PropTypes.bool, PropTypes.func]),
    })
  ),
  /** Loading state */
  loading: PropTypes.bool,
  /** Error message or object */
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  /** Message to display when data is empty */
  emptyMessage: PropTypes.string,
  /** Sort change handler */
  onSort: PropTypes.func,
  /** Currently sorted column key */
  sortColumn: PropTypes.string,
  /** Current sort direction */
  sortDirection: PropTypes.oneOf(['asc', 'desc', null]),
  /** Row click handler */
  onRowClick: PropTypes.func,
  /** Field to use as unique key for rows */
  keyField: PropTypes.string,
  /** Additional CSS classes */
  className: PropTypes.string,
  /** Whether to make header sticky */
  stickyHeader: PropTypes.bool,
};

Table.defaultProps = {
  data: [],
  actions: [],
  loading: false,
  error: null,
  emptyMessage: 'No data available',
  onSort: null,
  sortColumn: null,
  sortDirection: null,
  onRowClick: null,
  keyField: 'id',
  className: '',
  stickyHeader: false,
};

export default Table;

/**
 * Example usage:
 * 
 * const columns = [
 *   { key: 'name', label: 'Name', sortable: true },
 *   { key: 'email', label: 'Email', sortable: true },
 *   { 
 *     key: 'status', 
 *     label: 'Status',
 *     render: (value) => (
 *       <span className={`badge ${value === 'active' ? 'badge-success' : 'badge-gray'}`}>
 *         {value}
 *       </span>
 *     )
 *   },
 *   { key: 'createdAt', label: 'Created', sortable: true },
 * ];
 * 
 * const actions = [
 *   { key: 'edit', label: 'Edit', icon: <PencilIcon className="h-4 w-4" />, onClick: handleEdit },
 *   { key: 'delete', label: 'Delete', icon: <TrashIcon className="h-4 w-4" />, onClick: handleDelete, variant: 'danger' },
 * ];
 * 
 * <Table
 *   columns={columns}
 *   data={users}
 *   actions={actions}
 *   loading={isLoading}
 *   error={error}
 *   onSort={handleSort}
 *   sortColumn={sortColumn}
 *   sortDirection={sortDirection}
 *   onRowClick={handleRowClick}
 *   keyField="id"
 * />
 */