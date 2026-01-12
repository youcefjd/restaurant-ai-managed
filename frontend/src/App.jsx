import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';

// Layout Components
import Layout from './components/Layout';

// Page Components
import Dashboard from './pages/Dashboard';
import Restaurants from './pages/Restaurants';
import Tables from './pages/Tables';
import Bookings from './pages/Bookings';
import Customers from './pages/Customers';

// Create a context for global app state (selected restaurant, notifications, etc.)
const AppContext = createContext(null);

/**
 * Custom hook to access app-wide state and functions
 * @returns {Object} App context value containing selected restaurant, notifications, etc.
 */
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

/**
 * App Provider component that wraps the application with global state
 * Manages selected restaurant, notifications, and other app-wide state
 */
function AppProvider({ children }) {
  // Currently selected restaurant for filtering tables and bookings
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  
  // Global notification state for showing success/error messages
  const [notification, setNotification] = useState(null);
  
  // Loading state for initial app data
  const [isInitialized, setIsInitialized] = useState(false);

  /**
   * Show a notification message
   * @param {string} message - The message to display
   * @param {string} type - The type of notification ('success', 'error', 'info', 'warning')
   * @param {number} duration - How long to show the notification in ms (default: 5000)
   */
  const showNotification = (message, type = 'info', duration = 5000) => {
    setNotification({ message, type, id: Date.now() });
    
    // Auto-dismiss notification after duration
    if (duration > 0) {
      setTimeout(() => {
        setNotification(null);
      }, duration);
    }
  };

  /**
   * Clear the current notification
   */
  const clearNotification = () => {
    setNotification(null);
  };

  // Initialize app on mount
  useEffect(() => {
    // Restore selected restaurant from localStorage if available
    const savedRestaurant = localStorage.getItem('selectedRestaurant');
    if (savedRestaurant) {
      try {
        setSelectedRestaurant(JSON.parse(savedRestaurant));
      } catch (e) {
        localStorage.removeItem('selectedRestaurant');
      }
    }
    setIsInitialized(true);
  }, []);

  // Persist selected restaurant to localStorage
  useEffect(() => {
    if (selectedRestaurant) {
      localStorage.setItem('selectedRestaurant', JSON.stringify(selectedRestaurant));
    } else {
      localStorage.removeItem('selectedRestaurant');
    }
  }, [selectedRestaurant]);

  const contextValue = {
    selectedRestaurant,
    setSelectedRestaurant,
    notification,
    showNotification,
    clearNotification,
    isInitialized,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

/**
 * Notification component that displays global notifications
 * Renders as a toast in the top-right corner
 */
function NotificationToast() {
  const { notification, clearNotification } = useAppContext();

  if (!notification) return null;

  // Determine notification styles based on type
  const typeStyles = {
    success: 'bg-green-50 border-green-500 text-green-800',
    error: 'bg-red-50 border-red-500 text-red-800',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-800',
    info: 'bg-blue-50 border-blue-500 text-blue-800',
  };

  const iconPaths = {
    success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-sm w-full border-l-4 p-4 rounded-md shadow-lg ${typeStyles[notification.type] || typeStyles.info}`}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d={iconPaths[notification.type] || iconPaths.info}
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">{notification.message}</p>
        </div>
        <div className="ml-4 flex-shrink-0">
          <button
            type="button"
            className="inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2"
            onClick={clearNotification}
            aria-label="Dismiss notification"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Loading screen shown while app is initializing
 */
function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading application...</p>
      </div>
    </div>
  );
}

/**
 * 404 Not Found page component
 */
function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <p className="mt-2 text-gray-500">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <a
          href="/"
          className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Go back home
        </a>
      </div>
    </div>
  );
}

/**
 * Main App component
 * Sets up routing and global providers
 */
function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

/**
 * App content component that uses the AppContext
 * Separated to allow useAppContext hook usage
 */
function AppContent() {
  const { isInitialized } = useAppContext();

  // Show loading screen while initializing
  if (!isInitialized) {
    return <LoadingScreen />;
  }

  return (
    <Router>
      {/* Global notification toast */}
      <NotificationToast />
      
      <Routes>
        {/* Main layout wrapper for all authenticated routes */}
        <Route path="/" element={<Layout />}>
          {/* Dashboard - main landing page */}
          <Route index element={<Dashboard />} />
          
          {/* Restaurants management */}
          <Route path="restaurants" element={<Restaurants />} />
          
          {/* Tables management - can be filtered by restaurant */}
          <Route path="tables" element={<Tables />} />
          
          {/* Bookings management - can be filtered by restaurant, date, status */}
          <Route path="bookings" element={<Bookings />} />
          
          {/* Customers management */}
          <Route path="customers" element={<Customers />} />
          
          {/* Redirect old routes if any */}
          <Route path="dashboard" element={<Navigate to="/" replace />} />
        </Route>
        
        {/* 404 Not Found - catch all unmatched routes */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;