/**
 * Restaurant Signup Page
 *
 * Allows restaurants to create trial accounts with:
 * - 30 days OR 10 orders trial (whichever comes first)
 * - Auto-provisioned Twilio phone number
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BuildingStorefrontIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../hooks/useApi';

export default function Signup() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    business_name: '',
    owner_email: '',
    password: '',
    confirmPassword: '',
    phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.business_name.trim()) {
      setError('Restaurant name is required');
      return false;
    }
    if (!formData.owner_email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.owner_email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (!formData.phone.trim()) {
      setError('Phone number is required');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) return;

    setLoading(true);

    try {
      const response = await apiClient.post('/api/auth/signup', {
        business_name: formData.business_name.trim(),
        owner_email: formData.owner_email.trim().toLowerCase(),
        password: formData.password,
        phone: formData.phone.trim(),
      });

      const { access_token, user } = response.data;

      // Store auth data
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Redirect to restaurant dashboard
      navigate('/');
      window.location.reload();
    } catch (err) {
      console.error('Signup error:', err);
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to create account. Please try again.';
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
            Start Your Free Trial
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Get your AI-powered restaurant phone in minutes
          </p>
        </div>

        {/* Trial Benefits */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Your trial includes:</h3>
          <ul className="space-y-2">
            <li className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              30 days free trial
            </li>
            <li className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              Dedicated AI phone number
            </li>
            <li className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              Up to 10 orders included
            </li>
            <li className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              No credit card required
            </li>
          </ul>
        </div>

        {/* Signup Form */}
        <form className="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* Restaurant Name */}
            <div>
              <label htmlFor="business_name" className="block text-sm font-medium text-gray-700">
                Restaurant Name
              </label>
              <input
                id="business_name"
                name="business_name"
                type="text"
                required
                value={formData.business_name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Your Restaurant Name"
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="owner_email" className="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <input
                id="owner_email"
                name="owner_email"
                type="email"
                autoComplete="email"
                required
                value={formData.owner_email}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="you@restaurant.com"
              />
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                Phone Number
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required
                value={formData.phone}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="(555) 123-4567"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Min. 6 characters"
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Confirm your password"
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
                  Creating your account...
                </span>
              ) : (
                'Start Free Trial'
              )}
            </button>
          </div>

          {/* Login Link */}
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                Sign in
              </Link>
            </p>
          </div>

          {/* Terms */}
          <p className="mt-2 text-xs text-center text-gray-500">
            By signing up, you agree to our Terms of Service and Privacy Policy
          </p>
        </form>
      </div>
    </div>
  );
}
