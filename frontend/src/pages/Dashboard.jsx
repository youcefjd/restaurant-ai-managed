import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BuildingStorefrontIcon,
  TableCellsIcon,
  CalendarDaysIcon,
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import { format, parseISO, isToday, isTomorrow, startOfDay, endOfDay } from 'date-fns';
import useApi from '../hooks/useApi';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Dashboard page component
 * Displays overview statistics, recent bookings, and key metrics
 * for the restaurant management system
 */
export default function Dashboard() {
  // State for dashboard data
  const [stats, setStats] = useState({
    totalRestaurants: 0,
    totalTables: 0,
    totalBookings: 0,
    totalCustomers: 0,
    todayBookings: 0,
    upcomingBookings: 0,
  });
  const [recentBookings, setRecentBookings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // API hooks for data fetching
  const { get } = useApi();

  // Fetch all dashboard data on mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

  /**
   * Fetches all data needed for the dashboard
   * Aggregates data from multiple API endpoints
   */
  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel for better performance
      const [restaurantsRes, bookingsRes, customersRes] = await Promise.all([
        get('/api/'),
        get('/api/bookings/'),
        get('/api/customers/'),
      ]);

      const restaurants = restaurantsRes || [];
      const bookings = bookingsRes || [];
      const customers = customersRes || [];

      // Calculate total tables across all restaurants
      let totalTables = 0;
      for (const restaurant of restaurants) {
        try {
          const tablesRes = await get(`/api/${restaurant.id}/tables`);
          totalTables += (tablesRes || []).length;
        } catch {
          // Continue if tables fetch fails for a restaurant
          console.warn(`Failed to fetch tables for restaurant ${restaurant.id}`);
        }
      }

      // Calculate today's and upcoming bookings
      const today = new Date();
      const todayStart = startOfDay(today);
      const todayEnd = endOfDay(today);

      const todayBookings = bookings.filter((booking) => {
        const bookingDate = parseISO(booking.booking_time || booking.date);
        return bookingDate >= todayStart && bookingDate <= todayEnd;
      });

      const upcomingBookings = bookings.filter((booking) => {
        const bookingDate = parseISO(booking.booking_time || booking.date);
        return bookingDate > todayEnd && booking.status !== 'cancelled';
      });

      // Update stats
      setStats({
        totalRestaurants: restaurants.length,
        totalTables,
        totalBookings: bookings.length,
        totalCustomers: customers.length,
        todayBookings: todayBookings.length,
        upcomingBookings: upcomingBookings.length,
      });

      // Get recent bookings (last 10, sorted by date)
      const sortedBookings = [...bookings]
        .sort((a, b) => {
          const dateA = new Date(a.booking_time || a.date);
          const dateB = new Date(b.booking_time || b.date);
          return dateB - dateA;
        })
        .slice(0, 10);

      setRecentBookings(sortedBookings);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Formats a booking date for display
   * Shows "Today", "Tomorrow", or the formatted date
   */
  const formatBookingDate = (dateString) => {
    try {
      const date = parseISO(dateString);
      if (isToday(date)) {
        return `Today at ${format(date, 'h:mm a')}`;
      }
      if (isTomorrow(date)) {
        return `Tomorrow at ${format(date, 'h:mm a')}`;
      }
      return format(date, 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  /**
   * Returns the appropriate status badge styling
   */
  const getStatusBadge = (status) => {
    const statusStyles = {
      confirmed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-red-100 text-red-800',
      completed: 'bg-blue-100 text-blue-800',
    };
    return statusStyles[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  /**
   * Returns the appropriate status icon
   */
  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return <CheckCircleIcon className="h-4 w-4 text-green-600" aria-hidden="true" />;
      case 'cancelled':
        return <XCircleIcon className="h-4 w-4 text-red-600" aria-hidden="true" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-600" aria-hidden="true" />;
      default:
        return null;
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96" role="status" aria-label="Loading dashboard">
        <LoadingSpinner size="lg" />
        <span className="sr-only">Loading dashboard data...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-12" role="alert">
        <XCircleIcon className="mx-auto h-12 w-12 text-red-400" aria-hidden="true" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">Error Loading Dashboard</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <div className="mt-6">
          <Button onClick={fetchDashboardData} variant="primary">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <header>
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your restaurant management system
        </p>
      </header>

      {/* Stats Grid */}
      <section aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          Statistics
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Restaurants Stat Card */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-indigo-500 p-3">
                  <BuildingStorefrontIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Restaurants</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalRestaurants}</p>
              </div>
            </div>
            <Link
              to="/restaurants"
              className="absolute inset-0 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-lg"
              aria-label={`View all ${stats.totalRestaurants} restaurants`}
            >
              <span className="sr-only">View restaurants</span>
            </Link>
          </Card>

          {/* Tables Stat Card */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-green-500 p-3">
                  <TableCellsIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Tables</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalTables}</p>
              </div>
            </div>
            <Link
              to="/tables"
              className="absolute inset-0 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 rounded-lg"
              aria-label={`View all ${stats.totalTables} tables`}
            >
              <span className="sr-only">View tables</span>
            </Link>
          </Card>

          {/* Bookings Stat Card */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-blue-500 p-3">
                  <CalendarDaysIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Bookings</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalBookings}</p>
              </div>
            </div>
            <Link
              to="/bookings"
              className="absolute inset-0 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg"
              aria-label={`View all ${stats.totalBookings} bookings`}
            >
              <span className="sr-only">View bookings</span>
            </Link>
          </Card>

          {/* Customers Stat Card */}
          <Card className="relative overflow-hidden">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="rounded-md bg-purple-500 p-3">
                  <UsersIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Customers</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalCustomers}</p>
              </div>
            </div>
            <Link
              to="/customers"
              className="absolute inset-0 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 rounded-lg"
              aria-label={`View all ${stats.totalCustomers} customers`}
            >
              <span className="sr-only">View customers</span>
            </Link>
          </Card>
        </div>
      </section>

      {/* Quick Stats Row */}
      <section aria-labelledby="quick-stats-heading">
        <h2 id="quick-stats-heading" className="sr-only">
          Quick Statistics
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Today's Bookings */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="rounded-full bg-orange-100 p-2">
                  <ClockIcon className="h-5 w-5 text-orange-600" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Today&apos;s Bookings</p>
                  <p className="text-xl font-semibold text-gray-900">{stats.todayBookings}</p>
                </div>
              </div>
              <Link
                to="/bookings?filter=today"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
              >
                View all
              </Link>
            </div>
          </Card>

          {/* Upcoming Bookings */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="rounded-full bg-teal-100 p-2">
                  <ArrowTrendingUpIcon className="h-5 w-5 text-teal-600" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Upcoming Bookings</p>
                  <p className="text-xl font-semibold text-gray-900">{stats.upcomingBookings}</p>
                </div>
              </div>
              <Link
                to="/bookings?filter=upcoming"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
              >
                View all
              </Link>
            </div>
          </Card>
        </div>
      </section>

      {/* Recent Bookings Table */}
      <section aria-labelledby="recent-bookings-heading">
        <Card>
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 id="recent-bookings-heading" className="text-lg font-medium text-gray-900">
                  Recent Bookings
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Latest booking activity across all restaurants
                </p>
              </div>
              <Link to="/bookings">
                <Button variant="outline" size="sm">
                  View All
                </Button>
              </Link>
            </div>
          </div>

          {recentBookings.length === 0 ? (
            // Empty state
            <div className="text-center py-12">
              <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">No bookings yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first booking.
              </p>
              <div className="mt-6">
                <Link to="/bookings">
                  <Button variant="primary">
                    Create Booking
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            // Bookings table
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Customer
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Date & Time
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Party Size
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Status
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentBookings.map((booking) => (
                    <tr key={booking.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-600">
                                {booking.customer_name?.[0]?.toUpperCase() || 'G'}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {booking.customer_name || 'Guest'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {booking.customer_email || booking.customer_phone || 'No contact info'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatBookingDate(booking.booking_time || booking.date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {booking.party_size || booking.guests || 'N/A'} guests
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(
                            booking.status
                          )}`}
                        >
                          {getStatusIcon(booking.status)}
                          {booking.status || 'Pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link
                          to={`/bookings/${booking.id}`}
                          className="text-indigo-600 hover:text-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </section>

      {/* Quick Actions */}
      <section aria-labelledby="quick-actions-heading">
        <h2 id="quick-actions-heading" className="text-lg font-medium text-gray-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link to="/restaurants" className="group">
            <Card className="hover:shadow-md transition-shadow duration-200 group-focus:ring-2 group-focus:ring-indigo-500 group-focus:ring-offset-2">
              <div className="flex items-center">
                <BuildingStorefrontIcon className="h-8 w-8 text-indigo-500" aria-hidden="true" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Add Restaurant</p>
                  <p className="text-xs text-gray-500">Create a new restaurant</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/tables" className="group">
            <Card className="hover:shadow-md transition-shadow duration-200 group-focus:ring-2 group-focus:ring-green-500 group-focus:ring-offset-2">
              <div className="flex items-center">
                <TableCellsIcon className="h-8 w-8 text-green-500" aria-hidden="true" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Manage Tables</p>
                  <p className="text-xs text-gray-500">Add or edit tables</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/bookings" className="group">
            <Card className="hover:shadow-md transition-shadow duration-200 group-focus:ring-2 group-focus:ring-blue-500 group-focus:ring-offset-2">
              <div className="flex items-center">
                <CalendarDaysIcon className="h-8 w-8 text-blue-500" aria-hidden="true" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">New Booking</p>
                  <p className="text-xs text-gray-500">Create a reservation</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/customers" className="group">
            <Card className="hover:shadow-md transition-shadow duration-200 group-focus:ring-2 group-focus:ring-purple-500 group-focus:ring-offset-2">
              <div className="flex items-center">
                <UsersIcon className="h-8 w-8 text-purple-500" aria-hidden="true" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">View Customers</p>
                  <p className="text-xs text-gray-500">Manage customer list</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </section>
    </div>
  );
}