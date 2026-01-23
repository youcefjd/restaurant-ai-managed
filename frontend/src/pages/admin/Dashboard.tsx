import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { adminAPI } from '../../services/api'
import { Store, ShoppingBag, DollarSign, TrendingUp, ArrowRight } from 'lucide-react'
import PageHeader from '../../components/ui/PageHeader'
import StatCard from '../../components/ui/StatCard'

export default function AdminDashboard() {
  const navigate = useNavigate()

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminAPI.getStats(),
  })

  const { data: restaurants, isLoading: restaurantsLoading } = useQuery({
    queryKey: ['admin-restaurants'],
    queryFn: () => adminAPI.getRestaurants(),
  })

  const statsData = stats?.data
  const restaurantData = restaurants?.data || []

  // Memoized calculations
  const { activeRestaurants, trialRestaurants, activeSubscriptions } = useMemo(() => ({
    activeRestaurants: restaurantData.filter((r: any) => r.is_active).length,
    trialRestaurants: restaurantData.filter((r: any) => r.subscription_status === 'trial').length,
    activeSubscriptions: restaurantData.filter((r: any) => r.subscription_status === 'active').length,
  }), [restaurantData])

  if (isLoading || restaurantsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 rounded-lg bg-danger/10 border border-danger/20 max-w-md mx-auto mt-12">
        <p className="text-danger font-medium">Error loading dashboard</p>
        <p className="text-sm text-dim mt-1">{String(error)}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform Dashboard"
        subtitle="Overview of all restaurants and orders"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Restaurants"
          value={statsData?.total_restaurants || 0}
          icon={Store}
          subtitle={`${activeRestaurants} active`}
        />
        <StatCard
          label="Total Orders"
          value={statsData?.total_orders || 0}
          icon={ShoppingBag}
        />
        <StatCard
          label="Platform Revenue"
          value={`$${((statsData?.total_revenue_cents || 0) / 100).toFixed(2)}`}
          icon={DollarSign}
        />
        <StatCard
          label="Commission Earned"
          value={`$${((statsData?.platform_commission_cents || 0) / 100).toFixed(2)}`}
          icon={TrendingUp}
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Restaurant Status Summary */}
        <div className="card">
          <h2 className="font-medium mb-4">Restaurant Status</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-success"></span>
                <span className="text-sm">Active</span>
              </div>
              <span className="font-medium">{activeSubscriptions}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent"></span>
                <span className="text-sm">Trial</span>
              </div>
              <span className="font-medium">{trialRestaurants}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-danger"></span>
                <span className="text-sm">Inactive</span>
              </div>
              <span className="font-medium">{restaurantData.length - activeRestaurants}</span>
            </div>
          </div>
        </div>

        {/* Recent Restaurants */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-medium">Recent Restaurant Signups</h2>
            <button
              onClick={() => navigate('/admin/restaurants')}
              className="text-sm text-accent flex items-center gap-1 hover:underline"
            >
              View All <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {restaurantData.length === 0 ? (
            <div className="py-8 text-center">
              <Store className="w-10 h-10 text-dim mx-auto mb-2" />
              <p className="text-dim">No restaurants yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {restaurantData.slice(0, 5).map((restaurant: any) => (
                <div
                  key={restaurant.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer"
                  onClick={() => navigate('/admin/restaurants')}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-accent font-medium text-sm">
                      {restaurant.business_name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{restaurant.business_name}</p>
                      <p className="text-xs text-dim">{restaurant.owner_email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${
                      restaurant.subscription_status === 'active' ? 'badge-success' :
                      restaurant.subscription_status === 'trial' ? 'badge-info' : 'badge-danger'
                    }`}>
                      {restaurant.subscription_status}
                    </span>
                    <p className="text-xs text-dim mt-1 capitalize">{restaurant.subscription_tier}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => navigate('/admin/restaurants')}
          className="card flex items-center gap-4 hover:bg-white/5 text-left"
        >
          <Store className="w-8 h-8 text-accent" />
          <div>
            <p className="font-medium">Manage Restaurants</p>
            <p className="text-sm text-dim">View and manage all accounts</p>
          </div>
        </button>

        <button
          onClick={() => navigate('/admin/revenue')}
          className="card flex items-center gap-4 hover:bg-white/5 text-left"
        >
          <DollarSign className="w-8 h-8 text-success" />
          <div>
            <p className="font-medium">Revenue Analytics</p>
            <p className="text-sm text-dim">Track earnings and payouts</p>
          </div>
        </button>

        <button
          onClick={() => navigate('/admin/analytics')}
          className="card flex items-center gap-4 hover:bg-white/5 text-left"
        >
          <TrendingUp className="w-8 h-8 text-warning" />
          <div>
            <p className="font-medium">Growth Analytics</p>
            <p className="text-sm text-dim">Platform growth trends</p>
          </div>
        </button>
      </div>
    </div>
  )
}
