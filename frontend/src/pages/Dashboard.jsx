import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BuildingStorefrontIcon,
  CurrencyDollarIcon,
  CalendarDaysIcon,
  UsersIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useApiHelpers } from '../hooks/useApi';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Platform Admin Dashboard
 * Displays platform-wide statistics: restaurants, revenue, commissions, trends
 */
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const { get } = useApiHelpers();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await get('/api/admin/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch platform stats:', err);
      setError('Failed to load platform statistics. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (cents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format((cents || 0) / 100);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ChartBarIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">Error Loading Dashboard</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <div className="mt-6">
          <Button onClick={fetchDashboardData}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <header>
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Platform Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your restaurant platform
        </p>
      </header>

      {/* Main Stats Grid */}
      <section>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Total Restaurants */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-indigo-500 p-3">
                  <BuildingStorefrontIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Restaurants</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.total_restaurants || 0}</p>
              </div>
            </div>
            <Link to="/restaurants" className="absolute inset-0 rounded-lg focus:ring-2 focus:ring-indigo-500" />
          </Card>

          {/* Active Restaurants */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-green-500 p-3">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Restaurants</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.active_restaurants || 0}</p>
              </div>
            </div>
            <Link to="/restaurants?status=active" className="absolute inset-0 rounded-lg focus:ring-2 focus:ring-green-500" />
          </Card>

          {/* Trial Restaurants */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-blue-500 p-3">
                  <CalendarDaysIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">On Trial</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.trial_restaurants || 0}</p>
              </div>
            </div>
            <Link to="/restaurants?status=trial" className="absolute inset-0 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </Card>

          {/* Total Customers */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-purple-500 p-3">
                  <UsersIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Customers</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.total_customers || 0}</p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Revenue Section */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Revenue Overview</h2>
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
                  {formatCurrency(stats?.total_revenue_cents)}
                </p>
              </div>
            </div>
          </Card>

          {/* Platform Commission */}
          <Card>
            <div className="flex items-center">
              <div className="rounded-full bg-indigo-100 p-3">
                <ChartBarIcon className="h-6 w-6 text-indigo-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Platform Commission</p>
                <p className="text-2xl font-bold text-indigo-600">
                  {formatCurrency(stats?.platform_commission_cents)}
                </p>
              </div>
            </div>
          </Card>

          {/* Orders & Bookings */}
          <Card>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Orders</span>
                <span className="text-lg font-semibold text-gray-900">{stats?.total_orders || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Bookings</span>
                <span className="text-lg font-semibold text-gray-900">{stats?.total_bookings || 0}</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link to="/restaurants" className="group">
            <Card className="hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <BuildingStorefrontIcon className="h-8 w-8 text-indigo-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Manage Restaurants</p>
                  <p className="text-xs text-gray-500">View and manage all restaurant accounts</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/revenue" className="group">
            <Card className="hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <CurrencyDollarIcon className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Revenue Report</p>
                  <p className="text-xs text-gray-500">View detailed revenue breakdown</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/analytics" className="group">
            <Card className="hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">View Analytics</p>
                  <p className="text-xs text-gray-500">Platform growth and trends</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </section>
    </div>
  );
}
