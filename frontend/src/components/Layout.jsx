import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  BuildingStorefrontIcon,
  TableCellsIcon,
  CalendarDaysIcon,
  UsersIcon,
  ChevronLeftIcon,
} from '@heroicons/react/24/outline';

/**
 * Navigation items configuration
 * Each item defines a route in the sidebar navigation
 */
const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: HomeIcon,
    description: 'Overview and statistics',
  },
  {
    name: 'Restaurants',
    href: '/restaurants',
    icon: BuildingStorefrontIcon,
    description: 'Manage restaurants',
  },
  {
    name: 'Tables',
    href: '/tables',
    icon: TableCellsIcon,
    description: 'Manage tables',
  },
  {
    name: 'Bookings',
    href: '/bookings',
    icon: CalendarDaysIcon,
    description: 'Manage reservations',
  },
  {
    name: 'Customers',
    href: '/customers',
    icon: UsersIcon,
    description: 'Customer database',
  },
];

/**
 * Layout Component
 * Main layout wrapper providing sidebar navigation and header
 * Features:
 * - Responsive sidebar (collapsible on mobile)
 * - Collapsible sidebar on desktop
 * - Active route highlighting
 * - Accessible navigation
 */
const Layout = () => {
  const location = useLocation();
  
  // Mobile sidebar open/close state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Desktop sidebar collapsed state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  /**
   * Check if a navigation item is currently active
   * @param {string} href - The route path to check
   * @returns {boolean} - Whether the route is active
   */
  const isActiveRoute = (href) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  /**
   * Get the current page title based on the active route
   * @returns {string} - The page title
   */
  const getCurrentPageTitle = () => {
    const currentItem = navigationItems.find((item) => isActiveRoute(item.href));
    return currentItem?.name || 'Dashboard';
  };

  /**
   * Close mobile sidebar when a navigation link is clicked
   */
  const handleNavClick = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-xl transition-transform duration-300 ease-in-out lg:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Mobile navigation sidebar"
      >
        {/* Mobile sidebar header */}
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <Link
            to="/"
            className="flex items-center space-x-2"
            onClick={handleNavClick}
          >
            <BuildingStorefrontIcon className="h-8 w-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900">RestaurantOS</span>
          </Link>
          <button
            type="button"
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Mobile navigation */}
        <nav className="mt-4 px-2" aria-label="Mobile main navigation">
          <ul className="space-y-1" role="list">
            {navigationItems.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    onClick={handleNavClick}
                    className={`group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <item.icon
                      className={`mr-3 h-5 w-5 flex-shrink-0 ${
                        isActive
                          ? 'text-indigo-600'
                          : 'text-gray-400 group-hover:text-gray-500'
                      }`}
                      aria-hidden="true"
                    />
                    <span>{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden transform bg-white shadow-lg transition-all duration-300 ease-in-out lg:block ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        }`}
        aria-label="Desktop navigation sidebar"
      >
        {/* Desktop sidebar header */}
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <Link
            to="/"
            className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-2'}`}
          >
            <BuildingStorefrontIcon className="h-8 w-8 flex-shrink-0 text-indigo-600" />
            {!sidebarCollapsed && (
              <span className="text-xl font-bold text-gray-900">RestaurantOS</span>
            )}
          </Link>
        </div>

        {/* Desktop navigation */}
        <nav className="mt-4 px-2" aria-label="Desktop main navigation">
          <ul className="space-y-1" role="list">
            {navigationItems.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    } ${sidebarCollapsed ? 'justify-center' : ''}`}
                    aria-current={isActive ? 'page' : undefined}
                    title={sidebarCollapsed ? item.name : undefined}
                  >
                    <item.icon
                      className={`h-5 w-5 flex-shrink-0 ${
                        isActive
                          ? 'text-indigo-600'
                          : 'text-gray-400 group-hover:text-gray-500'
                      } ${sidebarCollapsed ? '' : 'mr-3'}`}
                      aria-hidden="true"
                    />
                    {!sidebarCollapsed && <span>{item.name}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Collapse toggle button */}
        <button
          type="button"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeftIcon
            className={`h-4 w-4 text-gray-400 transition-transform ${
              sidebarCollapsed ? 'rotate-180' : ''
            }`}
          />
        </button>
      </aside>

      {/* Main content area */}
      <div
        className={`transition-all duration-300 ${
          sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        }`}
      >
        {/* Header */}
        <header className="sticky top-0 z-20 bg-white shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            {/* Mobile menu button */}
            <button
              type="button"
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 lg:hidden"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
              aria-expanded={sidebarOpen}
              aria-controls="mobile-sidebar"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>

            {/* Page title */}
            <div className="flex-1 lg:flex-none">
              <h1 className="text-lg font-semibold text-gray-900 sm:text-xl lg:text-2xl">
                {getCurrentPageTitle()}
              </h1>
            </div>

            {/* Header right section - can be extended with user menu, notifications, etc. */}
            <div className="flex items-center space-x-4">
              {/* Current date display */}
              <span className="hidden text-sm text-gray-500 sm:block">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>

              {/* User avatar placeholder */}
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-medium text-white"
                aria-label="User menu"
              >
                A
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="min-h-[calc(100vh-4rem)]">
          <div className="px-4 py-6 sm:px-6 lg:px-8">
            {/* React Router outlet for nested routes */}
            <Outlet />
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between space-y-2 text-sm text-gray-500 sm:flex-row sm:space-y-0">
            <p>© {new Date().getFullYear()} RestaurantOS. All rights reserved.</p>
            <p className="text-gray-400">Restaurant Management System v1.0</p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;