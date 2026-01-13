import { Routes, Route, Navigate } from 'react-router-dom'
import RestaurantDashboard from './pages/restaurant/Dashboard'
import RestaurantOrders from './pages/restaurant/Orders'
import RestaurantMenu from './pages/restaurant/Menu'
import RestaurantAnalytics from './pages/restaurant/Analytics'
import RestaurantSettings from './pages/restaurant/Settings'
import AdminDashboard from './pages/admin/Dashboard'
import AdminRestaurants from './pages/admin/Restaurants'
import AdminRevenue from './pages/admin/Revenue'
import AdminAnalytics from './pages/admin/Analytics'
import RestaurantLayout from './components/layouts/RestaurantLayout'
import AdminLayout from './components/layouts/AdminLayout'
import LandingPage from './pages/LandingPage'
import RestaurantLogin from './pages/auth/RestaurantLogin'
import AdminLogin from './pages/auth/AdminLogin'
import Signup from './pages/auth/Signup'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<RestaurantLogin />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/admin-login" element={<AdminLogin />} />

      {/* Restaurant Dashboard (Protected) */}
      <Route
        path="/restaurant"
        element={
          <ProtectedRoute requireRestaurant>
            <RestaurantLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/restaurant/dashboard" replace />} />
        <Route path="dashboard" element={<RestaurantDashboard />} />
        <Route path="orders" element={<RestaurantOrders />} />
        <Route path="menu" element={<RestaurantMenu />} />
        <Route path="analytics" element={<RestaurantAnalytics />} />
        <Route path="settings" element={<RestaurantSettings />} />
      </Route>

      {/* Platform Admin Dashboard (Protected) */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireAdmin>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="restaurants" element={<AdminRestaurants />} />
        <Route path="revenue" element={<AdminRevenue />} />
        <Route path="analytics" element={<AdminAnalytics />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
