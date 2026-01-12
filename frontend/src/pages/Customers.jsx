import { useState, useEffect, useMemo } from 'react';
import {
  MagnifyingGlassIcon,
  UserGroupIcon,
  PhoneIcon,
  EnvelopeIcon,
  CalendarDaysIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { format, parseISO } from 'date-fns';
import useApi from '../hooks/useApi';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Customers page component
 * Displays a list of customers with search functionality and booking history
 */
export default function Customers() {
  // State for search and filtering
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCustomerId, setExpandedCustomerId] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showBookingModal, setShowBookingModal] = useState(false);

  // Fetch customers data
  const {
    data: customers,
    loading: customersLoading,
    error: customersError,
    refetch: refetchCustomers,
  } = useApi('/api/customers/');

  // Fetch all bookings for customer history
  const {
    data: bookings,
    loading: bookingsLoading,
    error: bookingsError,
  } = useApi('/api/bookings/');

  // Fetch restaurants for booking details
  const { data: restaurants } = useApi('/api/');

  // Filter customers based on search term
  const filteredCustomers = useMemo(() => {
    if (!customers) return [];
    
    const term = searchTerm.toLowerCase().trim();
    if (!term) return customers;

    return customers.filter((customer) => {
      const name = customer.name?.toLowerCase() || '';
      const email = customer.email?.toLowerCase() || '';
      const phone = customer.phone?.toLowerCase() || '';
      
      return (
        name.includes(term) ||
        email.includes(term) ||
        phone.includes(term)
      );
    });
  }, [customers, searchTerm]);

  // Get bookings for a specific customer
  const getCustomerBookings = (customerId) => {
    if (!bookings) return [];
    return bookings.filter((booking) => booking.customer_id === customerId);
  };

  // Get restaurant name by ID
  const getRestaurantName = (restaurantId) => {
    if (!restaurants) return 'Unknown Restaurant';
    const restaurant = restaurants.find((r) => r.id === restaurantId);
    return restaurant?.name || 'Unknown Restaurant';
  };

  // Calculate customer statistics
  const getCustomerStats = (customerId) => {
    const customerBookings = getCustomerBookings(customerId);
    const totalBookings = customerBookings.length;
    const confirmedBookings = customerBookings.filter(
      (b) => b.status === 'confirmed'
    ).length;
    const cancelledBookings = customerBookings.filter(
      (b) => b.status === 'cancelled'
    ).length;
    const totalGuests = customerBookings.reduce(
      (sum, b) => sum + (b.party_size || 0),
      0
    );

    return {
      totalBookings,
      confirmedBookings,
      cancelledBookings,
      totalGuests,
    };
  };

  // Toggle expanded customer row
  const toggleExpanded = (customerId) => {
    setExpandedCustomerId(
      expandedCustomerId === customerId ? null : customerId
    );
  };

  // Open booking history modal
  const openBookingModal = (customer) => {
    setSelectedCustomer(customer);
    setShowBookingModal(true);
  };

  // Close booking history modal
  const closeBookingModal = () => {
    setSelectedCustomer(null);
    setShowBookingModal(false);
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), 'MMM d, yyyy');
    } catch {
      return dateString;
    }
  };

  // Format time for display
  const formatTime = (timeString) => {
    if (!timeString) return '';
    try {
      // Handle HH:mm:ss format
      const [hours, minutes] = timeString.split(':');
      const date = new Date();
      date.setHours(parseInt(hours, 10));
      date.setMinutes(parseInt(minutes, 10));
      return format(date, 'h:mm a');
    } catch {
      return timeString;
    }
  };

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Handle keyboard navigation for search
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Escape') {
      setSearchTerm('');
    }
  };

  // Loading state
  if (customersLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading customers...</span>
      </div>
    );
  }

  // Error state
  if (customersError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-medium text-red-800 mb-2">
          Failed to load customers
        </h3>
        <p className="text-red-600 mb-4">{customersError}</p>
        <Button onClick={refetchCustomers} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your customers and view their booking history
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <UserGroupIcon className="h-5 w-5" />
          <span>{customers?.length || 0} total customers</span>
        </div>
      </div>

      {/* Search Bar */}
      <Card>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon
              className="h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search by name, email, or phone..."
            className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg 
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                     placeholder-gray-400 text-gray-900"
            aria-label="Search customers"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
        {searchTerm && (
          <p className="mt-2 text-sm text-gray-500">
            Found {filteredCustomers.length} customer
            {filteredCustomers.length !== 1 ? 's' : ''} matching "{searchTerm}"
          </p>
        )}
      </Card>

      {/* Customers List */}
      {filteredCustomers.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {searchTerm ? 'No customers found' : 'No customers yet'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Customers will appear here when they make bookings'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          {/* Desktop Table View */}
          <div className="hidden md:block overflow-x-auto">
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
                    Contact
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Bookings
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Total Guests
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCustomers.map((customer) => {
                  const stats = getCustomerStats(customer.id);
                  const isExpanded = expandedCustomerId === customer.id;
                  const customerBookings = getCustomerBookings(customer.id);

                  return (
                    <>
                      <tr
                        key={customer.id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                              <span className="text-blue-600 font-medium text-sm">
                                {customer.name?.charAt(0)?.toUpperCase() || '?'}
                              </span>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {customer.name}
                              </div>
                              <div className="text-sm text-gray-500">
                                ID: {customer.id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col gap-1">
                            {customer.email && (
                              <div className="flex items-center text-sm text-gray-600">
                                <EnvelopeIcon className="h-4 w-4 mr-2 text-gray-400" />
                                <a
                                  href={`mailto:${customer.email}`}
                                  className="hover:text-blue-600"
                                >
                                  {customer.email}
                                </a>
                              </div>
                            )}
                            {customer.phone && (
                              <div className="flex items-center text-sm text-gray-600">
                                <PhoneIcon className="h-4 w-4 mr-2 text-gray-400" />
                                <a
                                  href={`tel:${customer.phone}`}
                                  className="hover:text-blue-600"
                                >
                                  {customer.phone}
                                </a>
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col gap-1">
                            <span className="text-sm font-medium text-gray-900">
                              {stats.totalBookings} total
                            </span>
                            <div className="flex gap-2 text-xs">
                              <span className="text-green-600">
                                {stats.confirmedBookings} confirmed
                              </span>
                              {stats.cancelledBookings > 0 && (
                                <span className="text-red-600">
                                  {stats.cancelledBookings} cancelled
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-900">
                            {stats.totalGuests} guests
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => openBookingModal(customer)}
                              aria-label={`View booking history for ${customer.name}`}
                            >
                              <CalendarDaysIcon className="h-4 w-4 mr-1" />
                              History
                            </Button>
                            <button
                              onClick={() => toggleExpanded(customer.id)}
                              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                              aria-expanded={isExpanded}
                              aria-label={
                                isExpanded
                                  ? 'Collapse details'
                                  : 'Expand details'
                              }
                            >
                              {isExpanded ? (
                                <ChevronUpIcon className="h-5 w-5" />
                              ) : (
                                <ChevronDownIcon className="h-5 w-5" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                      {/* Expanded Row - Recent Bookings */}
                      {isExpanded && (
                        <tr key={`${customer.id}-expanded`}>
                          <td colSpan={5} className="px-6 py-4 bg-gray-50">
                            <div className="space-y-3">
                              <h4 className="text-sm font-medium text-gray-900">
                                Recent Bookings
                              </h4>
                              {customerBookings.length === 0 ? (
                                <p className="text-sm text-gray-500">
                                  No bookings found
                                </p>
                              ) : (
                                <div className="grid gap-2">
                                  {customerBookings.slice(0, 5).map((booking) => (
                                    <div
                                      key={booking.id}
                                      className="flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200"
                                    >
                                      <div className="flex items-center gap-4">
                                        <span
                                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                            booking.status
                                          )}`}
                                        >
                                          {booking.status}
                                        </span>
                                        <span className="text-sm text-gray-900">
                                          {getRestaurantName(
                                            booking.restaurant_id
                                          )}
                                        </span>
                                        <span className="text-sm text-gray-500">
                                          {formatDate(booking.booking_date)} at{' '}
                                          {formatTime(booking.booking_time)}
                                        </span>
                                      </div>
                                      <span className="text-sm text-gray-600">
                                        {booking.party_size} guests
                                      </span>
                                    </div>
                                  ))}
                                  {customerBookings.length > 5 && (
                                    <button
                                      onClick={() => openBookingModal(customer)}
                                      className="text-sm text-blue-600 hover:text-blue-800"
                                    >
                                      View all {customerBookings.length} bookings
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="md:hidden divide-y divide-gray-200">
            {filteredCustomers.map((customer) => {
              const stats = getCustomerStats(customer.id);

              return (
                <div key={customer.id} className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-medium text-sm">
                          {customer.name?.charAt(0)?.toUpperCase() || '?'}
                        </span>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {customer.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {stats.totalBookings} bookings • {stats.totalGuests}{' '}
                          guests
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1">
                    {customer.email && (
                      <div className="flex items-center text-sm text-gray-600">
                        <EnvelopeIcon className="h-4 w-4 mr-2 text-gray-400" />
                        <a
                          href={`mailto:${customer.email}`}
                          className="hover:text-blue-600 truncate"
                        >
                          {customer.email}
                        </a>
                      </div>
                    )}
                    {customer.phone && (
                      <div className="flex items-center text-sm text-gray-600">
                        <PhoneIcon className="h-4 w-4 mr-2 text-gray-400" />
                        <a
                          href={`tel:${customer.phone}`}
                          className="hover:text-blue-600"
                        >
                          {customer.phone}
                        </a>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openBookingModal(customer)}
                      className="flex-1"
                    >
                      <CalendarDaysIcon className="h-4 w-4 mr-1" />
                      View History
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Booking History Modal */}
      {showBookingModal && selectedCustomer && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto"
          aria-labelledby="booking-history-title"
          role="dialog"
          aria-modal="true"
        >
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              aria-hidden="true"
              onClick={closeBookingModal}
            />

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3
                      className="text-lg font-medium text-gray-900"
                      id="booking-history-title"
                    >
                      Booking History
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {selectedCustomer.name}
                    </p>
                  </div>
                  <button
                    onClick={closeBookingModal}
                    className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label="Close modal"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  {bookingsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <LoadingSpinner size="md" />
                      <span className="ml-2 text-gray-600">
                        Loading bookings...
                      </span>
                    </div>
                  ) : bookingsError ? (
                    <div className="text-center py-8 text-red-600">
                      Failed to load bookings
                    </div>
                  ) : (
                    (() => {
                      const customerBookings = getCustomerBookings(
                        selectedCustomer.id
                      );
                      if (customerBookings.length === 0) {
                        return (
                          <div className="text-center py-8 text-gray-500">
                            No bookings found for this customer
                          </div>
                        );
                      }
                      return (
                        <div className="space-y-3">
                          {customerBookings.map((booking) => (
                            <div
                              key={booking.id}
                              className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                            >
                              <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                        booking.status
                                      )}`}
                                    >
                                      {booking.status}
                                    </span>
                                    <span className="text-sm font-medium text-gray-900">
                                      {getRestaurantName(booking.restaurant_id)}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600">
                                    {formatDate(booking.booking_date)} at{' '}
                                    {formatTime(booking.booking_time)}
                                  </p>
                                  <p className="text-sm text-gray-500">
                                    Table {booking.table_id} •{' '}
                                    {booking.party_size} guests
                                  </p>
                                  {booking.special_requests && (
                                    <p className="text-sm text-gray-500 italic">
                                      "{booking.special_requests}"
                                    </p>
                                  )}
                                </div>
                                <span className="text-xs text-gray-400">
                                  #{booking.id}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    })()
                  )}
                </div>
              </div>

              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <Button variant="secondary" onClick={closeBookingModal}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}