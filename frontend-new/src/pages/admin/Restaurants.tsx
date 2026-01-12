import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminAPI } from '../../services/api'
import { Store, DollarSign, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { useState } from 'react'

export default function AdminRestaurants() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('all')

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
                  <button className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
