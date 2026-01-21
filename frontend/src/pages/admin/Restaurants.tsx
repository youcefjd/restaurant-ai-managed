import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminAPI } from '../../services/api'
import { Store, DollarSign, CheckCircle, XCircle, AlertCircle, Plus, X } from 'lucide-react'
import { useState } from 'react'

export default function AdminRestaurants() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [selectedRestaurant, setSelectedRestaurant] = useState<any>(null)
  const [commissionRate, setCommissionRate] = useState(10)
  const [commissionEnabled, setCommissionEnabled] = useState(true)
  const [newRestaurant, setNewRestaurant] = useState({
    business_name: '',
    owner_email: '',
    owner_name: '',
    owner_phone: '',
    subscription_tier: 'professional',
  })

  const { data: restaurants, isLoading } = useQuery({
    queryKey: ['admin-restaurants', statusFilter],
    queryFn: () => {
      const params = statusFilter !== 'all' ? { status_filter: statusFilter } : undefined
      return adminAPI.getRestaurants(params)
    },
  })

  const suspendMutation = useMutation({
    mutationFn: (id: number) => adminAPI.suspendRestaurant(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-restaurants'] })
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: number) => adminAPI.activateRestaurant(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-restaurants'] })
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminAPI.createRestaurant(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-restaurants'] })
      setShowAddModal(false)
      setNewRestaurant({
        business_name: '',
        owner_email: '',
        owner_name: '',
        owner_phone: '',
        subscription_tier: 'professional',
      })
    },
  })

  const updateCommissionMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: any }) =>
      adminAPI.updateCommission(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-restaurants'] })
      // Close modal and refresh
      setShowDetailsModal(false)
      setSelectedRestaurant(null)
    },
  })

  const handleCreateRestaurant = () => {
    createMutation.mutate(newRestaurant)
  }

  const handleUpdateCommission = () => {
    if (selectedRestaurant) {
      // Validate commission rate
      const validRate = Math.min(Math.max(commissionRate, 0), 30)

      updateCommissionMutation.mutate({
        id: selectedRestaurant.id,
        data: {
          platform_commission_rate: validRate,
          commission_enabled: commissionEnabled
        }
      })
    }
  }

  const restaurantData = restaurants?.data || []

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'trial':
        return <AlertCircle className="w-5 h-5 text-blue-600" />
      default:
        return <XCircle className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700'
      case 'trial':
        return 'bg-blue-100 text-blue-700'
      case 'suspended':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading restaurants...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Restaurants</h1>
          <p className="text-gray-600 mt-1">Manage all restaurant accounts</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Restaurant
          </button>
          <div className="flex gap-2">
          {['all', 'active', 'trial', 'suspended'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                statusFilter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {status}
            </button>
          ))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-600">Total Restaurants</p>
          <p className="text-2xl font-bold mt-1">{restaurantData.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Active</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {restaurantData.filter((r: any) => r.subscription_status === 'active').length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Trial</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">
            {restaurantData.filter((r: any) => r.subscription_status === 'trial').length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Suspended</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {restaurantData.filter((r: any) => !r.is_active).length}
          </p>
        </div>
      </div>

      {/* Restaurant List */}
      {restaurantData.length === 0 ? (
        <div className="card text-center py-12">
          <Store className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No restaurants found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {restaurantData.map((restaurant: any) => (
            <div key={restaurant.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  {getStatusIcon(restaurant.subscription_status)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{restaurant.business_name}</h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(restaurant.subscription_status)}`}>
                        {restaurant.subscription_status}
                      </span>
                      {!restaurant.is_active && (
                        <span className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-700">
                          Suspended
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-600 mt-1">{restaurant.owner_email}</p>

                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span>Tier: <span className="font-medium">{restaurant.subscription_tier}</span></span>
                      <span>Commission: <span className="font-medium">{restaurant.platform_commission_rate}%</span></span>
                      {restaurant.total_revenue_cents > 0 && (
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          Revenue: <span className="font-medium">${(restaurant.total_revenue_cents / 100).toFixed(2)}</span>
                        </span>
                      )}
                    </div>

                    {restaurant.stripe_account_id && (
                      <p className="text-xs text-green-600 mt-2">
                        ✓ Stripe Connected
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {restaurant.is_active ? (
                    <button
                      onClick={() => suspendMutation.mutate(restaurant.id)}
                      className="text-sm px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                      disabled={suspendMutation.isPending}
                    >
                      Suspend
                    </button>
                  ) : (
                    <button
                      onClick={() => activateMutation.mutate(restaurant.id)}
                      className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                      disabled={activateMutation.isPending}
                    >
                      Activate
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setSelectedRestaurant(restaurant)
                      setCommissionRate(restaurant.platform_commission_rate || 10)
                      setCommissionEnabled(restaurant.commission_enabled ?? true)
                      setShowDetailsModal(true)
                    }}
                    className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Restaurant Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Add New Restaurant</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Business Name</label>
                <input
                  type="text"
                  className="input"
                  value={newRestaurant.business_name}
                  onChange={(e) => setNewRestaurant({ ...newRestaurant, business_name: e.target.value })}
                  placeholder="Mario's Pizza"
                />
              </div>

              <div>
                <label className="label">Owner Name</label>
                <input
                  type="text"
                  className="input"
                  value={newRestaurant.owner_name}
                  onChange={(e) => setNewRestaurant({ ...newRestaurant, owner_name: e.target.value })}
                  placeholder="Mario Rossi"
                />
              </div>

              <div>
                <label className="label">Owner Email</label>
                <input
                  type="email"
                  className="input"
                  value={newRestaurant.owner_email}
                  onChange={(e) => setNewRestaurant({ ...newRestaurant, owner_email: e.target.value })}
                  placeholder="mario@restaurant.com"
                />
              </div>

              <div>
                <label className="label">Owner Phone</label>
                <input
                  type="tel"
                  className="input"
                  value={newRestaurant.owner_phone}
                  onChange={(e) => setNewRestaurant({ ...newRestaurant, owner_phone: e.target.value })}
                  placeholder="+1234567890"
                />
              </div>

              <div>
                <label className="label">Subscription Tier</label>
                <select
                  className="input"
                  value={newRestaurant.subscription_tier}
                  onChange={(e) => setNewRestaurant({ ...newRestaurant, subscription_tier: e.target.value })}
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="professional">Professional</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCreateRestaurant}
                  disabled={createMutation.isPending}
                  className="btn btn-primary flex-1"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Restaurant'}
                </button>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>

              {createMutation.isError && (
                <p className="text-sm text-red-600 mt-2">
                  Error: {String(createMutation.error)}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Restaurant Details Modal */}
      {showDetailsModal && selectedRestaurant && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">{selectedRestaurant.business_name}</h2>
              <button
                onClick={() => {
                  setShowDetailsModal(false)
                  setSelectedRestaurant(null)
                }}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <span className={`text-xs px-3 py-1 rounded-full font-semibold ${getStatusColor(selectedRestaurant.subscription_status)}`}>
                  {selectedRestaurant.subscription_status}
                </span>
                {selectedRestaurant.is_active ? (
                  <span className="text-xs px-3 py-1 rounded-full bg-green-100 text-green-700 font-semibold">
                    Active
                  </span>
                ) : (
                  <span className="text-xs px-3 py-1 rounded-full bg-red-100 text-red-700 font-semibold">
                    Suspended
                  </span>
                )}
              </div>

              {/* Owner Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Owner Name</p>
                  <p className="font-medium">{selectedRestaurant.owner_name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Owner Email</p>
                  <p className="font-medium">{selectedRestaurant.owner_email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Subscription Tier</p>
                  <p className="font-medium capitalize">{selectedRestaurant.subscription_tier}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Created</p>
                  <p className="font-medium">{new Date(selectedRestaurant.created_at).toLocaleDateString()}</p>
                </div>
              </div>

              {/* Revenue Stats */}
              <div className="border-t pt-4">
                <h3 className="font-semibold mb-3">Revenue Statistics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 mb-1">Total Orders</p>
                    <p className="text-2xl font-bold text-blue-600">{selectedRestaurant.total_orders}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 mb-1">Total Revenue</p>
                    <p className="text-2xl font-bold text-green-600">
                      ${(selectedRestaurant.total_revenue_cents / 100).toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 mb-1">Commission Owed</p>
                    <p className="text-2xl font-bold text-purple-600">
                      ${(selectedRestaurant.commission_owed_cents / 100).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Commission Settings - Editable */}
              <div className="border-t pt-4">
                <h3 className="font-semibold mb-3">Commission Settings</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Enable Commission</label>
                      <p className="text-xs text-gray-500">
                        When enabled, platform takes a percentage of each order
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={commissionEnabled}
                        onChange={(e) => setCommissionEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div>
                    <label className="label">Commission Rate (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="30"
                      step="0.1"
                      value={commissionRate}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0
                        // Clamp value between 0 and 30
                        setCommissionRate(Math.min(Math.max(value, 0), 30))
                      }}
                      className="input"
                      disabled={!commissionEnabled}
                      placeholder="10.0"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {commissionRate > 30 ? (
                        <span className="text-red-600 font-medium">Rate must be between 0% and 30%</span>
                      ) : (
                        <>Example: At {commissionRate}%, a $10.00 order means ${(10 * (commissionRate / 100)).toFixed(2)} to platform, ${(10 * (1 - commissionRate / 100)).toFixed(2)} to restaurant</>
                      )}
                    </p>
                  </div>

                  <button
                    onClick={handleUpdateCommission}
                    disabled={updateCommissionMutation.isPending}
                    className="btn btn-primary w-full"
                  >
                    {updateCommissionMutation.isPending ? 'Saving...' : 'Update Commission Settings'}
                  </button>

                  {updateCommissionMutation.isError && (
                    <p className="text-sm text-red-600">
                      Error updating commission: {String(updateCommissionMutation.error)}
                    </p>
                  )}

                  {updateCommissionMutation.isSuccess && (
                    <p className="text-sm text-green-600">
                      Commission settings updated successfully!
                    </p>
                  )}
                </div>
              </div>

              {/* Stripe Status */}
              {selectedRestaurant.stripe_account_id && (
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-3">Payment Integration</h3>
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-5 h-5" />
                    <span>Stripe Connected</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Account ID: {selectedRestaurant.stripe_account_id}</p>
                </div>
              )}

              {/* Actions */}
              <div className="border-t pt-4 flex gap-3">
                {selectedRestaurant.is_active ? (
                  <button
                    onClick={() => {
                      suspendMutation.mutate(selectedRestaurant.id)
                      setShowDetailsModal(false)
                    }}
                    className="btn bg-red-600 text-white hover:bg-red-700"
                  >
                    Suspend Restaurant
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      activateMutation.mutate(selectedRestaurant.id)
                      setShowDetailsModal(false)
                    }}
                    className="btn bg-green-600 text-white hover:bg-green-700"
                  >
                    Activate Restaurant
                  </button>
                )}
                <button
                  onClick={() => {
                    setShowDetailsModal(false)
                    setSelectedRestaurant(null)
                  }}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
