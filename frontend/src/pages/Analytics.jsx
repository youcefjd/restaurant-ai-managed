/**
 * Platform Admin - Analytics & Growth
 *
 * Shows platform growth metrics:
 * - Restaurant signups over time
 * - Orders trend
 * - Bookings trend
 * - Revenue growth
 */

import { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  BuildingStorefrontIcon,
  CalendarDaysIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import { useApiHelpers } from '../hooks/useApi';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState('30');

  const api = useApiHelpers();

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/api/admin/analytics/growth?days=${days}`);
      setAnalyticsData(response.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (cents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format((cents || 0) / 100);
  };

  // Calculate totals from daily data
  const calculateTotals = () => {
    if (!analyticsData) return { signups: 0, orders: 0, bookings: 0, revenue: 0 };

    const signups = analyticsData.restaurant_signups?.reduce((sum, d) => sum + d.count, 0) || 0;
    const orders = analyticsData.daily_orders?.reduce((sum, d) => sum + d.orders, 0) || 0;
    const bookings = analyticsData.daily_bookings?.reduce((sum, d) => sum + d.bookings, 0) || 0;
    const revenue = analyticsData.daily_orders?.reduce((sum, d) => sum + d.revenue_cents, 0) || 0;

    return { signups, orders, bookings, revenue };
  };

  const totals = calculateTotals();

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Platform Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Growth metrics and trends
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2">
          <CalendarDaysIcon className="h-5 w-5 text-gray-400" />
          <select
            value={days}
            onChange={(e) => setDays(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="180">Last 6 months</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {analyticsData && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-indigo-100 p-3">
                  <BuildingStorefrontIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">New Restaurants</p>
                  <p className="text-2xl font-bold text-gray-900">{totals.signups}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-green-100 p-3">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Orders</p>
                  <p className="text-2xl font-bold text-gray-900">{totals.orders}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-blue-100 p-3">
                  <CalendarDaysIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Bookings</p>
                  <p className="text-2xl font-bold text-gray-900">{totals.bookings}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-purple-100 p-3">
                  <CurrencyDollarIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(totals.revenue)}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Restaurant Signups */}
          <Card>
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Restaurant Signups</h2>
              <p className="text-sm text-gray-500">New restaurant accounts over time</p>
            </div>
            <div className="p-4">
              {analyticsData.restaurant_signups?.length > 0 ? (
                <div className="space-y-2">
                  {analyticsData.restaurant_signups.slice(-10).map((day) => (
                    <div key={day.date} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <span className="text-sm text-gray-600">{day.date}</span>
                      <div className="flex items-center gap-2">
                        <div
                          className="h-4 bg-indigo-500 rounded"
                          style={{ width: `${Math.max(day.count * 20, 8)}px` }}
                        />
                        <span className="text-sm font-medium text-gray-900 w-8 text-right">{day.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 py-4 text-center">No signup data available</p>
              )}
            </div>
          </Card>

          {/* Daily Orders & Revenue */}
          <Card>
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Daily Orders & Revenue</h2>
              <p className="text-sm text-gray-500">Order volume and revenue trends</p>
            </div>
            <div className="p-4">
              {analyticsData.daily_orders?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Orders</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Revenue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {analyticsData.daily_orders.slice(-10).map((day) => (
                        <tr key={day.date} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-sm text-gray-600">{day.date}</td>
                          <td className="px-4 py-2 text-sm text-gray-900 text-right">{day.orders}</td>
                          <td className="px-4 py-2 text-sm font-medium text-green-600 text-right">
                            {formatCurrency(day.revenue_cents)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-gray-500 py-4 text-center">No order data available</p>
              )}
            </div>
          </Card>

          {/* Daily Bookings */}
          <Card>
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Daily Bookings</h2>
              <p className="text-sm text-gray-500">Reservation volume over time</p>
            </div>
            <div className="p-4">
              {analyticsData.daily_bookings?.length > 0 ? (
                <div className="space-y-2">
                  {analyticsData.daily_bookings.slice(-10).map((day) => (
                    <div key={day.date} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <span className="text-sm text-gray-600">{day.date}</span>
                      <div className="flex items-center gap-2">
                        <div
                          className="h-4 bg-blue-500 rounded"
                          style={{ width: `${Math.max(day.bookings * 10, 8)}px` }}
                        />
                        <span className="text-sm font-medium text-gray-900 w-8 text-right">{day.bookings}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 py-4 text-center">No booking data available</p>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
