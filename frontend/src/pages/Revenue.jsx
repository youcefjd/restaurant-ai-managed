/**
 * Platform Admin - Revenue & Commission Report
 *
 * Shows platform revenue breakdown:
 * - Total gross revenue
 * - Platform commissions
 * - Per-restaurant breakdown
 * - Date range filtering
 */

import { useState, useEffect } from 'react';
import {
  CurrencyDollarIcon,
  CalendarDaysIcon,
  BuildingStorefrontIcon,
} from '@heroicons/react/24/outline';
import { useApiHelpers } from '../hooks/useApi';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Revenue() {
  const [revenueData, setRevenueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('30'); // days

  const api = useApiHelpers();

  useEffect(() => {
    fetchRevenueData();
  }, [dateRange]);

  const fetchRevenueData = async () => {
    try {
      setLoading(true);
      setError(null);

      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - parseInt(dateRange) * 24 * 60 * 60 * 1000).toISOString();

      const response = await api.get(`/api/admin/revenue?start_date=${startDate}&end_date=${endDate}`);
      setRevenueData(response.data);
    } catch (err) {
      console.error('Failed to fetch revenue data:', err);
      setError('Failed to load revenue data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (cents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format((cents || 0) / 100);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

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
          <h1 className="text-2xl font-bold text-gray-900">Revenue & Commissions</h1>
          <p className="mt-1 text-sm text-gray-500">
            Platform revenue breakdown and commission tracking
          </p>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-2">
          <CalendarDaysIcon className="h-5 w-5 text-gray-400" />
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {revenueData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Gross Revenue */}
            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-green-100 p-3">
                  <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Gross Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(revenueData.gross_revenue_cents)}
                  </p>
                </div>
              </div>
            </Card>

            {/* Platform Commission */}
            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-indigo-100 p-3">
                  <CurrencyDollarIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Platform Commission</p>
                  <p className="text-2xl font-bold text-indigo-600">
                    {formatCurrency(revenueData.platform_commission_cents)}
                  </p>
                </div>
              </div>
            </Card>

            {/* Restaurant Payouts */}
            <Card>
              <div className="flex items-center">
                <div className="rounded-full bg-blue-100 p-3">
                  <BuildingStorefrontIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Restaurant Payouts</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(revenueData.restaurant_payout_cents)}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Period Info */}
          <Card>
            <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Report Period</p>
                <p className="text-sm font-medium text-gray-900">
                  {formatDate(revenueData.period_start)} - {formatDate(revenueData.period_end)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Orders</p>
                <p className="text-lg font-semibold text-gray-900">{revenueData.total_orders}</p>
              </div>
            </div>
          </Card>

          {/* Per-Restaurant Breakdown */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Revenue by Restaurant</h2>

            {revenueData.by_restaurant && revenueData.by_restaurant.length > 0 ? (
              <div className="overflow-hidden bg-white shadow ring-1 ring-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Restaurant
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Orders
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Revenue
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Commission Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Commission
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {revenueData.by_restaurant.map((restaurant) => (
                      <tr key={restaurant.account_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                              <BuildingStorefrontIcon className="h-5 w-5 text-indigo-600" />
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {restaurant.business_name}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {restaurant.orders}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(restaurant.revenue_cents)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {restaurant.commission_rate}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                          {formatCurrency(restaurant.commission_cents)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Card>
                <div className="p-8 text-center">
                  <CurrencyDollarIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No Revenue Data</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No orders have been placed in this time period.
                  </p>
                </div>
              </Card>
            )}
          </div>
        </>
      )}
    </div>
  );
}
