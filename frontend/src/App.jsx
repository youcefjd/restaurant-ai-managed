import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';

// Layout Components
import Layout from './components/Layout';
import RestaurantLayout from './components/RestaurantLayout';

// Admin Page Components
import Dashboard from './pages/Dashboard';
import Restaurants from './pages/Restaurants';
import Revenue from './pages/Revenue';
import Analytics from './pages/Analytics';

// Restaurant Page Components
import RestaurantDashboard from './pages/restaurant/RestaurantDashboard';
import PhoneSettings from './pages/restaurant/PhoneSettings';
import MenuManagement from './pages/restaurant/MenuManagement';
import RestaurantBookings from './pages/restaurant/RestaurantBookings';
import RestaurantSettings from './pages/restaurant/RestaurantSettings';

// Auth Pages
import Login from './pages/Login';
import Signup from './pages/Signup';

// Create a context for global app state
const AppContext = createContext(null);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

function AppProvider({ children }) {
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [notification, setNotification] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const showNotification = (message, type = 'info', duration = 5000) => {
    setNotification({ message, type, id: Date.now() });
    if (duration > 0) {
      setTimeout(() => setNotification(null), duration);
    }
  };

  const clearNotification = () => setNotification(null);

  useEffect(() => {
    const savedRestaurant = localStorage.getItem('selectedRestaurant');
    if (savedRestaurant) {
      try {
        setSelectedRestaurant(JSON.parse(savedRestaurant));
      } catch {
        localStorage.removeItem('selectedRestaurant');
      }
    }
    setIsInitialized(true);
  }, []);

  useEffect(() => {
    if (selectedRestaurant) {
      localStorage.setItem('selectedRestaurant', JSON.stringify(selectedRestaurant));
    } else {
      localStorage.removeItem('selectedRestaurant');
    }
  }, [selectedRestaurant]);

  return (
    <AppContext.Provider value={{
      selectedRestaurant,
      setSelectedRestaurant,
      notification,
      showNotification,
      clearNotification,
      isInitialized,
    }}>
      {children}
    </AppContext.Provider>
  );
}

function NotificationToast() {
  const { notification, clearNotification } = useAppContext();
  if (!notification) return null;

  const typeStyles = {
    success: 'bg-green-50 border-green-500 text-green-800',
    error: 'bg-red-50 border-red-500 text-red-800',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-800',
    info: 'bg-blue-50 border-blue-500 text-blue-800',
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-sm w-full border-l-4 p-4 rounded-md shadow-lg ${typeStyles[notification.type] || typeStyles.info}`}
      role="alert"
    >
      <div className="flex items-start">
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">{notification.message}</p>
        </div>
        <button onClick={clearNotification} className="ml-4">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <a href="/" className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700">
          Go back home
        </a>
      </div>
    </div>
  );
}

// Auth helpers
function isAuthenticated() {
  return !!localStorage.getItem('authToken');
}

function getUserRole() {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return user.role || 'restaurant';
    }
  } catch {
    // ignore
  }
  return null;
}

// Protected route that checks authentication
function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// Root redirect based on user role
function RootRedirect() {
  const role = getUserRole();
  if (role === 'admin') {
    return <Navigate to="/admin" replace />;
  }
  return <Navigate to="/restaurant" replace />;
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

function AppContent() {
  const { isInitialized } = useAppContext();

  if (!isInitialized) {
    return <LoadingScreen />;
  }

  return (
    <>
      <NotificationToast />

      <Routes>
        {/* Public routes */}
        <Route path="/login" element={
          isAuthenticated() ? <RootRedirect /> : <Login />
        } />
        <Route path="/signup" element={
          isAuthenticated() ? <RootRedirect /> : <Signup />
        } />

        {/* Root redirect based on role */}
        <Route path="/" element={
          <ProtectedRoute>
            <RootRedirect />
          </ProtectedRoute>
        } />

        {/* Admin routes */}
        <Route path="/admin" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="restaurants" element={<Restaurants />} />
          <Route path="revenue" element={<Revenue />} />
          <Route path="analytics" element={<Analytics />} />
        </Route>

        {/* Restaurant routes */}
        <Route path="/restaurant" element={
          <ProtectedRoute>
            <RestaurantLayout />
          </ProtectedRoute>
        }>
          <Route index element={<RestaurantDashboard />} />
          <Route path="phone" element={<PhoneSettings />} />
          <Route path="menu" element={<MenuManagement />} />
          <Route path="bookings" element={<RestaurantBookings />} />
          <Route path="settings" element={<RestaurantSettings />} />
        </Route>

        {/* Legacy redirects */}
        <Route path="/restaurants" element={<Navigate to="/admin/restaurants" replace />} />
        <Route path="/revenue" element={<Navigate to="/admin/revenue" replace />} />
        <Route path="/analytics" element={<Navigate to="/admin/analytics" replace />} />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default App;
