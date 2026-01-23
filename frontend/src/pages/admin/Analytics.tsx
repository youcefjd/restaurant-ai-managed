import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminAPI } from '../../services/api'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { TrendingUp, Store, ShoppingBag, Users, DollarSign } from 'lucide-react'
import PageHeader from '../../components/ui/PageHeader'
import StatCard from '../../components/ui/StatCard'
import TimePeriodFilter from '../../components/ui/TimePeriodFilter'

type TimePeriod = 7 | 30 | 90

export default function AdminAnalytics() {
  const [period, setPeriod] = useState<TimePeriod>(30)

  const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
    queryKey: ['admin-analytics', period],
    queryFn: () => adminAPI.getAnalytics(period),
    select: (response) => response.data,
  })

  const { data: restaurants } = useQuery({
    queryKey: ['admin-restaurants'],
    queryFn: () => adminAPI.getRestaurants(),
    select: (response) => response.data || [],
  })


  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminAPI.getStats(),
    select: (response) => response.data,
  })

  const restaurantData = restaurants || []

  // Calculate metrics from real data
  const metrics = useMemo(() => {
    const activeRestaurants = restaurantData.filter((r: any) => r.is_active).length
    const trialRestaurants = restaurantData.filter((r: any) => r.subscription_status === 'trial').length
    const paidRestaurants = restaurantData.filter((r: any) =>
      r.subscription_status === 'active' && r.subscription_tier !== 'FREE'
    ).length
    const conversionRate = restaurantData.length > 0
      ? ((paidRestaurants / restaurantData.length) * 100).toFixed(1)
      : '0'

    return { activeRestaurants, trialRestaurants, paidRestaurants, conversionRate }
  }, [restaurantData])

  // Subscription tier distribution
  const tierDistribution = useMemo(() => {
    const tiers = ['FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE']
    return tiers
      .map(tier => ({
        tier,
        count: restaurantData.filter((r: any) => r.subscription_tier === tier).length,
      }))
      .filter(item => item.count > 0)
  }, [restaurantData])

  // Format growth data from API
  const growthData = useMemo(() => {
    if (!analyticsData?.growth_data) return []
    return analyticsData.growth_data.map((item: any) => ({
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      restaurants: item.restaurant_count,
      orders: item.order_count,
      revenue: (item.revenue_cents || 0) / 100,
    }))
  }, [analyticsData?.growth_data])

  if (analyticsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform Analytics"
        subtitle="Growth trends and platform insights"
        actions={<TimePeriodFilter value={period} onChange={setPeriod} />}
      />

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Restaurants"
          value={metrics.activeRestaurants}
          icon={Store}
        />
        <StatCard
          label="Trial Accounts"
          value={metrics.trialRestaurants}
          icon={Users}
        />
        <StatCard
          label="Paid Subscriptions"
          value={metrics.paidRestaurants}
          icon={TrendingUp}
        />
        <StatCard
          label="Conversion Rate"
          value={`${metrics.conversionRate}%`}
          icon={ShoppingBag}
        />
      </div>

      {/* Revenue Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total Platform Revenue"
          value={`$${((stats?.total_revenue_cents || 0) / 100).toFixed(2)}`}
          icon={DollarSign}
          subtitle="All time"
        />
        <StatCard
          label="Commission Earned"
          value={`$${((stats?.platform_commission_cents || 0) / 100).toFixed(2)}`}
          icon={TrendingUp}
          subtitle="Platform earnings"
        />
        <StatCard
          label="Total Orders"
          value={stats?.total_orders || 0}
          icon={ShoppingBag}
          subtitle="Processed orders"
        />
      </div>

      {/* Growth Chart */}
      <div className="card">
        <h2 className="font-medium mb-4">Platform Growth</h2>
        {growthData.length > 0 ? (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={growthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'var(--text-dim)', fontSize: 12 }}
                />
                <YAxis
                  yAxisId="left"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'var(--text-dim)', fontSize: 12 }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'var(--text-dim)', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'var(--text)' }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="restaurants"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  name="Restaurants"
                  dot={{ fill: 'var(--accent)' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="orders"
                  stroke="var(--success)"
                  strokeWidth={2}
                  name="Orders"
                  dot={{ fill: 'var(--success)' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-dim text-sm py-8 text-center">No growth data available for this period</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscription Tier Distribution */}
        <div className="card">
          <h2 className="font-medium mb-4">Subscription Tiers</h2>
          {tierDistribution.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tierDistribution} layout="vertical">
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-dim)', fontSize: 12 }} />
                  <YAxis type="category" dataKey="tier" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-dim)', fontSize: 12 }} width={100} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: 'var(--text)' }}
                  />
                  <Bar dataKey="count" fill="var(--accent)" name="Restaurants" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-dim text-sm py-8 text-center">No subscription data</p>
          )}
        </div>

        {/* Key Insights */}
        <div className="card">
          <h2 className="font-medium mb-4">Key Insights</h2>
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="w-5 h-5 text-accent" />
                <p className="font-medium">Growth Status</p>
              </div>
              <p className="text-sm text-dim">
                {restaurantData.length} total restaurants on the platform
              </p>
            </div>

            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <div className="flex items-center gap-3 mb-2">
                <ShoppingBag className="w-5 h-5 text-success" />
                <p className="font-medium">Order Activity</p>
              </div>
              <p className="text-sm text-dim">
                {stats?.total_orders || 0} orders processed across all restaurants
              </p>
            </div>

            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
              <div className="flex items-center gap-3 mb-2">
                <Users className="w-5 h-5 text-warning" />
                <p className="font-medium">Trial Conversion</p>
              </div>
              <p className="text-sm text-dim">
                {metrics.conversionRate}% of restaurants have converted to paid plans
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Restaurant List */}
      <div className="card">
        <h2 className="font-medium mb-4">All Restaurants</h2>
        {restaurantData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Restaurant</th>
                  <th>Email</th>
                  <th>Tier</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {restaurantData.slice(0, 10).map((restaurant: any) => (
                  <tr key={restaurant.id}>
                    <td className="font-medium">{restaurant.business_name}</td>
                    <td className="text-dim">{restaurant.owner_email}</td>
                    <td className="capitalize">{restaurant.subscription_tier?.toLowerCase()}</td>
                    <td>
                      <span className={`badge ${
                        restaurant.subscription_status === 'active' ? 'badge-success' :
                        restaurant.subscription_status === 'trial' ? 'badge-info' : 'badge-danger'
                      }`}>
                        {restaurant.subscription_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-dim text-sm py-8 text-center">No restaurants registered yet</p>
        )}
      </div>
    </div>
  )
}
