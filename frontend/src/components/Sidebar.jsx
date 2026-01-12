import { NavLink, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  BuildingStorefrontIcon,
  TableCellsIcon,
  CalendarDaysIcon,
  UsersIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';

/**
 * Navigation menu items configuration
 * Each item defines the route, label, and icon for the sidebar
 */
const navigationItems = [
  {
    path: '/',
    label: 'Dashboard',
    icon: HomeIcon,
    description: 'Overview and statistics',
  },
  {
    path: '/restaurants',
    label: 'Restaurants',
    icon: BuildingStorefrontIcon,
    description: 'Manage restaurants',
  },
  {
    path: '/tables',
    label: 'Tables',
    icon: TableCellsIcon,
    description: 'Manage tables',
  },
  {
    path: '/bookings',
    label: 'Bookings',
    icon: CalendarDaysIcon,
    description: 'Manage reservations',
  },
  {
    path: '/customers',
    label: 'Customers',
    icon: UsersIcon,
    description: 'Customer database',
  },
];

/**
 * Sidebar Component
 * 
 * A responsive navigation sidebar with:
 * - Collapsible state for desktop
 * - Mobile overlay drawer
 * - Active state highlighting
 * - Keyboard navigation support
 * - ARIA accessibility attributes
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls mobile sidebar visibility
 * @param {function} props.onClose - Callback to close mobile sidebar
 * @param {boolean} props.isCollapsed - Controls desktop collapsed state
 * @param {function} props.onToggleCollapse - Callback to toggle collapse
 */
function Sidebar({ 
  isOpen = false, 
  onClose = () => {}, 
  isCollapsed = false, 
  onToggleCollapse = () => {} 
}) {
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close sidebar on route change (mobile only)
  useEffect(() => {
    if (isMobile && isOpen) {
      onClose();
    }
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle escape key to close mobile sidebar
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (isMobile && isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobile, isOpen]);

  /**
   * Determines if a navigation item is currently active
   * Handles both exact matches and nested routes
   */
  const isActiveRoute = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  /**
   * Renders a single navigation item
   */
  const renderNavItem = (item) => {
    const Icon = item.icon;
    const isActive = isActiveRoute(item.path);

    return (
      <li key={item.path}>
        <NavLink
          to={item.path}
          className={({ isActive: routerActive }) => `
            group flex items-center gap-x-3 rounded-lg px-3 py-2.5
            text-sm font-medium transition-all duration-200
            focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2
            ${isActive || routerActive
              ? 'bg-indigo-50 text-indigo-700 shadow-sm'
              : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
            }
            ${isCollapsed && !isMobile ? 'justify-center px-2' : ''}
          `}
          aria-current={isActive ? 'page' : undefined}
          title={isCollapsed && !isMobile ? item.label : undefined}
        >
          <Icon
            className={`
              h-5 w-5 flex-shrink-0 transition-colors duration-200
              ${isActive
                ? 'text-indigo-600'
                : 'text-gray-400 group-hover:text-gray-600'
              }
            `}
            aria-hidden="true"
          />
          {(!isCollapsed || isMobile) && (
            <span className="truncate">{item.label}</span>
          )}
          {/* Active indicator dot for collapsed state */}
          {isCollapsed && !isMobile && isActive && (
            <span 
              className="absolute right-1 h-1.5 w-1.5 rounded-full bg-indigo-600"
              aria-hidden="true"
            />
          )}
        </NavLink>
      </li>
    );
  };

  /**
   * Main sidebar content - shared between mobile and desktop
   */
  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo and Header */}
      <div 
        className={`
          flex h-16 items-center border-b border-gray-200 px-4
          ${isCollapsed && !isMobile ? 'justify-center' : 'justify-between'}
        `}
      >
        {(!isCollapsed || isMobile) ? (
          <div className="flex items-center gap-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <BuildingStorefrontIcon className="h-5 w-5 text-white" aria-hidden="true" />
            </div>
            <span className="text-lg font-semibold text-gray-900">
              RestaurantHub
            </span>
          </div>
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <BuildingStorefrontIcon className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
        )}

        {/* Mobile close button */}
        {isMobile && (
          <button
            type="button"
            onClick={onClose}
            className="
              rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-500
              focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500
            "
            aria-label="Close sidebar"
          >
            <XMarkIcon className="h-5 w-5" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Navigation Menu */}
      <nav 
        className="flex-1 overflow-y-auto px-3 py-4"
        aria-label="Main navigation"
      >
        <ul role="list" className="space-y-1">
          {navigationItems.map(renderNavItem)}
        </ul>
      </nav>

      {/* Collapse Toggle Button (Desktop only) */}
      {!isMobile && (
        <div className="border-t border-gray-200 p-3">
          <button
            type="button"
            onClick={onToggleCollapse}
            className={`
              flex w-full items-center justify-center gap-x-2 rounded-lg
              px-3 py-2 text-sm font-medium text-gray-600
              transition-colors duration-200
              hover:bg-gray-100 hover:text-gray-900
              focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500
              ${isCollapsed ? 'px-2' : ''}
            `}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!isCollapsed}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
            ) : (
              <>
                <ChevronLeftIcon className="h-5 w-5" aria-hidden="true" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Footer with version info */}
      {(!isCollapsed || isMobile) && (
        <div className="border-t border-gray-200 px-4 py-3">
          <p className="text-xs text-gray-500">
            Restaurant Management v1.0
          </p>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar Drawer */}
      {isMobile && (
        <aside
          className={`
            fixed inset-y-0 left-0 z-50 w-72 transform bg-white shadow-xl
            transition-transform duration-300 ease-in-out
            ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
          role="dialog"
          aria-modal="true"
          aria-label="Navigation sidebar"
        >
          {sidebarContent}
        </aside>
      )}

      {/* Desktop Sidebar */}
      {!isMobile && (
        <aside
          className={`
            fixed inset-y-0 left-0 z-30 hidden transform bg-white
            shadow-sm transition-all duration-300 ease-in-out md:block
            ${isCollapsed ? 'w-16' : 'w-64'}
          `}
          aria-label="Navigation sidebar"
        >
          {sidebarContent}
        </aside>
      )}
    </>
  );
}

export default Sidebar;