/**
 * Login Page Component
 * Handles admin and restaurant login
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BuildingStorefrontIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../hooks/useApi';

export default function Login() {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let response;

      if (isAdmin) {
        // Admin login
        response = await apiClient.post('/api/auth/admin/login', {
          email,
          password,
        });
      } else {
        // Restaurant login (uses form data)
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        response = await apiClient.post('/api/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
      }

      const { access_token, user } = response.data;

      // Store auth data
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Redirect to dashboard
      navigate('/');
      window.location.reload();
    } catch (err) {
      console.error('Login error:', err);
      const message = err.response?.data?.detail || err.response?.data?.message || 'Login failed. Please check your credentials.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-100 via-white to-purple-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Title */}
        <div className="text-center">
          <div className="flex justify-center">
            <BuildingStorefrontIcon className="h-16 w-16 text-indigo-600" />
          </div>
          <h2 className="mt-4 text-3xl font-extrabold text-gray-900">
            RestaurantOS
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>

        {/* Login Type Toggle */}
        <div className="flex justify-center">
          <div className="inline-flex rounded-lg border border-gray-200 p-1 bg-white">
            <button
              type="button"
              onClick={() => setIsAdmin(true)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                isAdmin
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => setIsAdmin(false)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                !isAdmin
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Restaurant
            </button>
          </div>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          {/* Demo credentials hint */}
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              {isAdmin ? (
                <>Demo: admin@restaurantai.com / admin123</>
              ) : (
                <>Use your restaurant account credentials</>
              )}
            </p>
          </div>

          {/* Signup Link for restaurants */}
          {!isAdmin && (
            <div className="mt-4 text-center border-t border-gray-200 pt-4">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <Link to="/signup" className="font-medium text-indigo-600 hover:text-indigo-500">
                  Start your free trial
                </Link>
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
