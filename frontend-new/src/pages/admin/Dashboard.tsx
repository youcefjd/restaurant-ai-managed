import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { adminAPI } from '../../services/api'
import { Store, ShoppingBag, DollarSign, TrendingUp, ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react'
import { AreaChart, Area, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

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

  const activeRestaurants = restaurantData.filter((r: any) => r.is_active).length
  const trialRestaurants = restaurantData.filter((r: any) => r.subscription_status === 'trial').length
  const activeSubscriptions = restaurantData.filter((r: any) => r.subscription_status === 'active').length

  // Mock trend data for mini charts
  const trendData = [
    { value: 20 }, { value: 35 }, { value: 28 }, { value: 45 }, { value: 38 }, { value: 52 }, { value: 60 }
  ]

  // Pie chart data for restaurant status
  const pieData = [
    { name: 'Active', value: activeSubscriptions, color: '#22c55e' },
    { name: 'Trial', value: trialRestaurants, color: '#3b82f6' },
    { name: 'Inactive', value: restaurantData.length - activeRestaurants, color: '#ef4444' }
  ]

  const metrics = [
    {
      label: 'Total Restaurants',
      value: statsData?.total_restaurants || 0,
      icon: Store,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'bg-gradient-to-br from-blue-50 to-blue-100',
      iconBg: 'bg-blue-500',
      change: '+12%',
      trend: 'up',
      subtext: `${activeRestaurants} active`,
    },
    {
      label: 'Total Orders',
      value: statsData?.total_orders || 0,
      icon: ShoppingBag,
      gradient: 'from-green-500 to-emerald-600',
      bgGradient: 'bg-gradient-to-br from-green-50 to-emerald-100',
      iconBg: 'bg-green-500',
      change: '+8%',
      trend: 'up',
      subtext: 'This month',
    },
    {
      label: 'Platform Revenue',
      value: `$${((statsData?.total_revenue_cents || 0) / 100).toFixed(2)}`,
      icon: DollarSign,
      gradient: 'from-purple-500 to-purple-600',
      bgGradient: 'bg-gradient-to-br from-purple-50 to-purple-100',
      iconBg: 'bg-purple-500',
      change: '+23%',
      trend: 'up',
      subtext: 'Total processed',
    },
    {
      label: 'Commission Earned',
      value: `$${((statsData?.platform_commission_cents || 0) / 100).toFixed(2)}`,
      icon: TrendingUp,
      gradient: 'from-orange-500 to-amber-600',
      bgGradient: 'bg-gradient-to-br from-orange-50 to-amber-100',
      iconBg: 'bg-orange-500',
      change: '+15%',
      trend: 'up',
      subtext: 'Your earnings',
    },
  ]

  if (isLoading || restaurantsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-200 border-t-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md mx-auto">
          <p className="text-red-600 font-semibold">Error loading dashboard</p>
          <p className="text-sm text-red-500 mt-2">{String(error)}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Platform Dashboard</h1>
            <p className="text-blue-100">Welcome back! Here's your platform overview</p>
          </div>
          <div className="hidden md:flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
            <Activity className="w-5 h-5" />
            <span className="font-semibold">All Systems Operational</span>
          </div>
        </div>
      </div>

      {/* Stats Grid with Modern Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <div
            key={metric.label}
            className="relative group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover transition-all duration-300 cursor-pointer border border-gray-100 overflow-hidden"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {/* Background gradient decoration */}
            <div className={`absolute top-0 right-0 w-32 h-32 ${metric.bgGradient} rounded-full blur-3xl opacity-30 group-hover:opacity-50 transition-opacity`}></div>

            <div className="relative">
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${metric.iconBg} shadow-lg`}>
                  <metric.icon className="w-6 h-6 text-white" />
                </div>
                <div className={`flex items-center gap-1 text-sm font-semibold ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {metric.trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  {metric.change}
                </div>
              </div>

              <div>
                <p className="text-gray-600 text-sm font-medium mb-1">{metric.label}</p>
                <p className="text-3xl font-bold text-gray-900 mb-1">{metric.value}</p>
                <p className="text-xs text-gray-500">{metric.subtext}</p>
              </div>

              {/* Mini trend chart */}
              <div className="mt-4 -mb-2">
                <ResponsiveContainer width="100%" height={40}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id={`gradient-${index}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={metric.iconBg.replace('bg-', '#')} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={metric.iconBg.replace('bg-', '#')} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke={metric.iconBg.replace('bg-', '#')}
                      strokeWidth={2}
                      fill={`url(#gradient-${index})`}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Restaurant Status Chart */}
        <div className="lg:col-span-1 bg-white rounded-2xl p-6 shadow-card border border-gray-100">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Restaurant Status</h2>
          <div className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 mt-4">
            {pieData.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="text-gray-600">{item.name}</span>
                </div>
                <span className="font-semibold text-gray-900">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Restaurants */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-card border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900">Recent Restaurant Signups</h2>
            <button
              onClick={() => navigate('/admin/restaurants')}
              className="text-sm text-primary-600 hover:text-primary-700 font-semibold"
            >
              View All →
            </button>
          </div>

          {restaurantData.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-xl">
              <Store className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500">No restaurants yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {restaurantData.slice(0, 4).map((restaurant: any) => (
                <div
                  key={restaurant.id}
                  className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-100 hover:border-primary-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-sm">
                      {restaurant.business_name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">{restaurant.business_name}</p>
                      <p className="text-sm text-gray-500">{restaurant.owner_email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-flex items-center text-xs px-3 py-1 rounded-full font-semibold ${
                        restaurant.subscription_status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : restaurant.subscription_status === 'trial'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {restaurant.subscription_status}
                    </span>
                    <p className="text-xs text-gray-500 mt-1 capitalize">
                      {restaurant.subscription_tier}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions with Modern Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => navigate('/admin/restaurants')}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-8 text-white shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer group transform hover:-translate-y-1"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Store className="w-8 h-8" />
            </div>
            <ArrowUpRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <h3 className="text-xl font-bold mb-2">Manage Restaurants</h3>
          <p className="text-blue-100 text-sm">
            View and manage all restaurant accounts, subscriptions, and settings
          </p>
        </div>

        <div
          onClick={() => navigate('/admin/revenue')}
          className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-8 text-white shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer group transform hover:-translate-y-1"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <DollarSign className="w-8 h-8" />
            </div>
            <ArrowUpRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <h3 className="text-xl font-bold mb-2">Revenue Analytics</h3>
          <p className="text-green-100 text-sm">
            Track commission earnings, payouts, and financial insights
          </p>
        </div>

        <div
          onClick={() => navigate('/admin/analytics')}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-8 text-white shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer group transform hover:-translate-y-1"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <TrendingUp className="w-8 h-8" />
            </div>
            <ArrowUpRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <h3 className="text-xl font-bold mb-2">Growth Analytics</h3>
          <p className="text-purple-100 text-sm">
            Monitor platform growth trends and performance metrics
          </p>
        </div>
      </div>
    </div>
  )
}
