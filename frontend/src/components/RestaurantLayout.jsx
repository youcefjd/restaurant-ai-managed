import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  PhoneIcon,
  DocumentTextIcon,
  ShoppingBagIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

/**
 * Navigation items for Restaurant Dashboard
 */
const navigationItems = [
  {
    name: 'Dashboard',
    href: '/restaurant',
    icon: HomeIcon,
    description: 'Overview and statistics',
  },
  {
    name: 'Phone & AI',
    href: '/restaurant/phone',
    icon: PhoneIcon,
    description: 'AI phone settings',
  },
  {
    name: 'Menu',
    href: '/restaurant/menu',
    icon: DocumentTextIcon,
    description: 'Manage your menu',
  },
  {
    name: 'Orders',
    href: '/restaurant/bookings',
    icon: ShoppingBagIcon,
    description: 'Takeout & Delivery',
  },
  {
    name: 'Settings',
    href: '/restaurant/settings',
    icon: Cog6ToothIcon,
    description: 'Account settings',
  },
];

/**
 * Restaurant Layout Component
 * Layout wrapper for restaurant users (not platform admin)
 */
const RestaurantLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  const getUserInfo = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        return JSON.parse(userStr);
      }
      return null;
    } catch {
      return null;
    }
  };

  const user = getUserInfo();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('selectedRestaurant');
    setUserMenuOpen(false);
    window.location.href = '/login';
  };

  const isActiveRoute = (href) => {
    if (href === '/restaurant') {
      return location.pathname === '/restaurant';
    }
    return location.pathname.startsWith(href);
  };

  const getCurrentPageTitle = () => {
    const currentItem = navigationItems.find((item) => isActiveRoute(item.href));
    return currentItem?.name || 'Dashboard';
  };

  const handleNavClick = () => {
    setSidebarOpen(false);
  };

  // Calculate trial status
  const getTrialStatus = () => {
    if (!user?.trial_ends_at) return null;
    const trialEnd = new Date(user.trial_ends_at);
    const now = new Date();
    const daysLeft = Math.ceil((trialEnd - now) / (1000 * 60 * 60 * 24));
    const ordersLeft = (user.trial_order_limit || 10) - (user.trial_orders_used || 0);
    return { daysLeft, ordersLeft };
  };

  const trialStatus = getTrialStatus();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-xl transition-transform duration-300 ease-in-out lg:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <Link to="/restaurant" className="flex items-center space-x-2" onClick={handleNavClick}>
            <PhoneIcon className="h-8 w-8 text-green-600" />
            <span className="text-xl font-bold text-gray-900">RestaurantOS</span>
          </Link>
          <button
            type="button"
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100"
            onClick={() => setSidebarOpen(false)}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-4 px-2">
          <ul className="space-y-1">
            {navigationItems.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    onClick={handleNavClick}
                    className={`group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-green-50 text-green-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <item.icon
                      className={`mr-3 h-5 w-5 flex-shrink-0 ${
                        isActive ? 'text-green-600' : 'text-gray-400 group-hover:text-gray-500'
                      }`}
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
      >
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <Link
            to="/restaurant"
            className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-2'}`}
          >
            <PhoneIcon className="h-8 w-8 flex-shrink-0 text-green-600" />
            {!sidebarCollapsed && (
              <span className="text-xl font-bold text-gray-900">RestaurantOS</span>
            )}
          </Link>
        </div>

        <nav className="mt-4 px-2">
          <ul className="space-y-1">
            {navigationItems.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-green-50 text-green-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    } ${sidebarCollapsed ? 'justify-center' : ''}`}
                    title={sidebarCollapsed ? item.name : undefined}
                  >
                    <item.icon
                      className={`h-5 w-5 flex-shrink-0 ${
                        isActive ? 'text-green-600' : 'text-gray-400 group-hover:text-gray-500'
                      } ${sidebarCollapsed ? '' : 'mr-3'}`}
                    />
                    {!sidebarCollapsed && <span>{item.name}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <button
          type="button"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm hover:bg-gray-50"
        >
          <ChevronLeftIcon
            className={`h-4 w-4 text-gray-400 transition-transform ${
              sidebarCollapsed ? 'rotate-180' : ''
            }`}
          />
        </button>
      </aside>

      {/* Main content area */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'}`}>
        {/* Header */}
        <header className="sticky top-0 z-20 bg-white shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <button
              type="button"
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100 lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>

            <div className="flex-1 lg:flex-none">
              <h1 className="text-lg font-semibold text-gray-900 sm:text-xl lg:text-2xl">
                {getCurrentPageTitle()}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Trial badge */}
              {trialStatus && trialStatus.daysLeft > 0 && (
                <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Trial: {trialStatus.daysLeft} days / {trialStatus.ordersLeft} orders left
                </span>
              )}

              {/* User dropdown */}
              <div className="relative" ref={userMenuRef}>
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-600 text-sm font-medium text-white">
                    {user?.business_name?.[0] || user?.email?.[0]?.toUpperCase() || 'R'}
                  </div>
                  <span className="hidden md:block max-w-[150px] truncate">
                    {user?.business_name || user?.email || 'Restaurant'}
                  </span>
                  <ChevronDownIcon
                    className={`h-4 w-4 text-gray-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                    <div className="py-1">
                      <div className="px-4 py-3 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {user?.business_name || 'Restaurant'}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {user?.email}
                        </p>
                      </div>

                      <div className="py-1">
                        <Link
                          to="/restaurant/settings"
                          onClick={() => setUserMenuOpen(false)}
                          className="flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <Cog6ToothIcon className="mr-3 h-5 w-5 text-gray-400" />
                          Settings
                        </Link>
                      </div>

                      <div className="border-t border-gray-100 py-1">
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                        >
                          <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5 text-red-500" />
                          Sign out
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="min-h-[calc(100vh-4rem)]">
          <div className="px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between space-y-2 text-sm text-gray-500 sm:flex-row sm:space-y-0">
            <p>© {new Date().getFullYear()} RestaurantOS. All rights reserved.</p>
            <p className="text-gray-400">Restaurant Dashboard v1.0</p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default RestaurantLayout;
