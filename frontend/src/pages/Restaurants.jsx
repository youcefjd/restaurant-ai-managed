/**
 * Platform Admin - Restaurant Accounts Management
 *
 * This page allows platform admins to:
 * 1. View all restaurant accounts on the platform
 * 2. Create new restaurant accounts
 * 3. Manage subscription tiers and status
 * 4. Set commission rates
 * 5. Suspend/activate accounts
 */

import { useState, useEffect, useCallback } from 'react';
import {
  PlusIcon,
  PencilIcon,
  BuildingStorefrontIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useApiHelpers } from '../hooks/useApi';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Restaurants() {
  // State for restaurant accounts
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail view modal
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [restaurantDetails, setRestaurantDetails] = useState(null);

  // Create modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    business_name: '',
    owner_name: '',
    owner_email: '',
    owner_phone: '',
    subscription_tier: 'professional',
  });
  const [createErrors, setCreateErrors] = useState({});
  const [isCreating, setIsCreating] = useState(false);

  // Commission modal state
  const [commissionModalOpen, setCommissionModalOpen] = useState(false);
  const [commissionRestaurant, setCommissionRestaurant] = useState(null);
  const [commissionRate, setCommissionRate] = useState(10);
  const [isSavingCommission, setIsSavingCommission] = useState(false);

  // Filter state
  const [statusFilter, setStatusFilter] = useState('');

  const api = useApiHelpers();

  // Fetch restaurant accounts
  const fetchRestaurants = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      let url = '/api/admin/restaurants';
      if (statusFilter) {
        url += `?status_filter=${statusFilter}`;
      }
      const response = await api.get(url);
      setRestaurants(response.data || []);
    } catch (err) {
      console.error('Failed to fetch restaurants:', err);
      setError('Failed to load restaurant accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [api, statusFilter]);

  useEffect(() => {
    fetchRestaurants();
  }, [statusFilter]);

  // Fetch restaurant details
  const fetchRestaurantDetails = async (accountId) => {
    try {
      setDetailLoading(true);
      const response = await api.get(`/api/admin/restaurants/${accountId}/details`);
      setRestaurantDetails(response.data);
    } catch (err) {
      console.error('Failed to fetch details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // Handle view details
  const handleViewDetails = (restaurant) => {
    setSelectedRestaurant(restaurant);
    fetchRestaurantDetails(restaurant.id);
  };

  // Handle create form
  const handleCreateInputChange = (e) => {
    const { name, value } = e.target;
    setCreateFormData((prev) => ({ ...prev, [name]: value }));
    if (createErrors[name]) {
      setCreateErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validateCreateForm = () => {
    const errors = {};
    if (!createFormData.business_name.trim()) errors.business_name = 'Required';
    if (!createFormData.owner_name.trim()) errors.owner_name = 'Required';
    if (!createFormData.owner_email.trim()) errors.owner_email = 'Required';
    if (createFormData.owner_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(createFormData.owner_email)) {
      errors.owner_email = 'Invalid email';
    }
    setCreateErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!validateCreateForm()) return;

    setIsCreating(true);
    try {
      await api.post('/api/admin/restaurants', {
        ...createFormData,
        subscription_status: 'trial',
      });
      await fetchRestaurants();
      setIsCreateModalOpen(false);
      setCreateFormData({
        business_name: '',
        owner_name: '',
        owner_email: '',
        owner_phone: '',
        subscription_tier: 'professional',
      });
    } catch (err) {
      setCreateErrors({
        submit: err.response?.data?.detail || 'Failed to create restaurant',
      });
    } finally {
      setIsCreating(false);
    }
  };

  // Handle commission update
  const handleOpenCommissionModal = (restaurant) => {
    setCommissionRestaurant(restaurant);
    setCommissionRate(10); // Default, would come from restaurant data
    setCommissionModalOpen(true);
  };

  const handleSaveCommission = async () => {
    if (!commissionRestaurant) return;
    setIsSavingCommission(true);
    try {
      await api.put(`/api/admin/restaurants/${commissionRestaurant.id}/commission`, {
        platform_commission_rate: commissionRate,
        commission_enabled: true,
      });
      await fetchRestaurants();
      setCommissionModalOpen(false);
    } catch (err) {
      console.error('Failed to update commission:', err);
    } finally {
      setIsSavingCommission(false);
    }
  };

  // Handle suspend/activate
  const handleToggleStatus = async (restaurant) => {
    try {
      if (restaurant.is_active) {
        await api.post(`/api/admin/restaurants/${restaurant.id}/suspend`);
      } else {
        await api.post(`/api/admin/restaurants/${restaurant.id}/activate`);
      }
      await fetchRestaurants();
    } catch (err) {
      console.error('Failed to toggle status:', err);
    }
  };

  // Format currency
  const formatCurrency = (cents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100);
  };

  // Get status badge styles
  const getStatusBadge = (status, isActive) => {
    if (!isActive) {
      return 'bg-red-100 text-red-800';
    }
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trial':
        return 'bg-blue-100 text-blue-800';
      case 'suspended':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Restaurant Accounts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage restaurant accounts, subscriptions, and commissions
          </p>
        </div>

        <Button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Add Restaurant</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="block w-full max-w-xs rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="suspended">Suspended</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </Card>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Restaurant List */}
      {restaurants.length === 0 ? (
        <Card>
          <div className="p-8 text-center">
            <BuildingStorefrontIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Restaurants</h3>
            <p className="mt-1 text-sm text-gray-500">
              No restaurant accounts found.
            </p>
          </div>
        </Card>
      ) : (
        <div className="overflow-hidden bg-white shadow ring-1 ring-gray-200 rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Restaurant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Revenue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Commission Owed
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {restaurants.map((restaurant) => (
                <tr key={restaurant.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          <BuildingStorefrontIcon className="h-5 w-5 text-indigo-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {restaurant.business_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {restaurant.owner_email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(restaurant.subscription_status, restaurant.is_active)}`}>
                      {restaurant.is_active ? restaurant.subscription_status : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                    {restaurant.subscription_tier}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(restaurant.total_revenue_cents)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                    {formatCurrency(restaurant.commission_owed_cents)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleViewDetails(restaurant)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="View Details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleOpenCommissionModal(restaurant)}
                        className="text-green-600 hover:text-green-900"
                        title="Set Commission"
                      >
                        <CurrencyDollarIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleToggleStatus(restaurant)}
                        className={restaurant.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                        title={restaurant.is_active ? 'Suspend' : 'Activate'}
                      >
                        {restaurant.is_active ? (
                          <XCircleIcon className="h-5 w-5" />
                        ) : (
                          <CheckCircleIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail View Modal */}
      <Modal
        isOpen={!!selectedRestaurant}
        onClose={() => {
          setSelectedRestaurant(null);
          setRestaurantDetails(null);
        }}
        title={selectedRestaurant?.business_name || 'Restaurant Details'}
      >
        {detailLoading ? (
          <div className="py-8 flex justify-center">
            <LoadingSpinner size="lg" />
          </div>
        ) : restaurantDetails ? (
          <div className="space-y-6">
            {/* Account Info */}
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">Account Information</h4>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <p><span className="font-medium">Owner:</span> {restaurantDetails.account.owner_name}</p>
                <p><span className="font-medium">Email:</span> {restaurantDetails.account.owner_email}</p>
                <p><span className="font-medium">Phone:</span> {restaurantDetails.account.owner_phone || 'N/A'}</p>
                <p><span className="font-medium">Commission Rate:</span> {restaurantDetails.account.platform_commission_rate}%</p>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-blue-600">Total Orders</p>
                <p className="text-2xl font-bold text-blue-900">{restaurantDetails.order_stats.total_orders}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-green-600">Total Revenue</p>
                <p className="text-2xl font-bold text-green-900">
                  {formatCurrency(restaurantDetails.order_stats.total_revenue_cents)}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-purple-600">Commission Owed</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatCurrency(restaurantDetails.order_stats.commission_owed_cents)}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-sm text-orange-600">Total Bookings</p>
                <p className="text-2xl font-bold text-orange-900">{restaurantDetails.booking_stats.total_bookings}</p>
              </div>
            </div>

            {/* Locations */}
            {restaurantDetails.locations.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">Locations ({restaurantDetails.locations.length})</h4>
                <div className="space-y-2">
                  {restaurantDetails.locations.map((loc) => (
                    <div key={loc.id} className="bg-gray-50 rounded-lg p-3">
                      <p className="font-medium">{loc.name}</p>
                      <p className="text-sm text-gray-500">{loc.address}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500">No details available</p>
        )}
      </Modal>

      {/* Create Restaurant Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add New Restaurant Account"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Business Name *</label>
            <input
              type="text"
              name="business_name"
              value={createFormData.business_name}
              onChange={handleCreateInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${createErrors.business_name ? 'border-red-300' : 'border-gray-300'}`}
              placeholder="Restaurant Name"
            />
            {createErrors.business_name && <p className="mt-1 text-sm text-red-600">{createErrors.business_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Owner Name *</label>
            <input
              type="text"
              name="owner_name"
              value={createFormData.owner_name}
              onChange={handleCreateInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${createErrors.owner_name ? 'border-red-300' : 'border-gray-300'}`}
              placeholder="John Doe"
            />
            {createErrors.owner_name && <p className="mt-1 text-sm text-red-600">{createErrors.owner_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Owner Email *</label>
            <input
              type="email"
              name="owner_email"
              value={createFormData.owner_email}
              onChange={handleCreateInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${createErrors.owner_email ? 'border-red-300' : 'border-gray-300'}`}
              placeholder="owner@restaurant.com"
            />
            {createErrors.owner_email && <p className="mt-1 text-sm text-red-600">{createErrors.owner_email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Phone</label>
            <input
              type="tel"
              name="owner_phone"
              value={createFormData.owner_phone}
              onChange={handleCreateInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm"
              placeholder="(555) 123-4567"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Subscription Tier</label>
            <select
              name="subscription_tier"
              value={createFormData.subscription_tier}
              onChange={handleCreateInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm"
            >
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {createErrors.submit && (
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-700">{createErrors.submit}</p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isCreating}>
              {isCreating ? <LoadingSpinner size="sm" /> : 'Create Account'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Commission Modal */}
      <Modal
        isOpen={commissionModalOpen}
        onClose={() => setCommissionModalOpen(false)}
        title={`Set Commission - ${commissionRestaurant?.business_name}`}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Commission Rate (%)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              step="0.5"
              value={commissionRate}
              onChange={(e) => setCommissionRate(parseFloat(e.target.value) || 0)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <p className="mt-1 text-sm text-gray-500">
              Platform will receive {commissionRate}% of all orders from this restaurant
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="secondary" onClick={() => setCommissionModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveCommission} disabled={isSavingCommission}>
              {isSavingCommission ? <LoadingSpinner size="sm" /> : 'Save Commission'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
