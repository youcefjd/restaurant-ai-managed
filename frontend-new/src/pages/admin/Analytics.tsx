import { useQuery } from '@tanstack/react-query'
import { adminAPI } from '../../services/api'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, Store, ShoppingBag, Users } from 'lucide-react'
import { useState } from 'react'

export default function AdminAnalytics() {
  const [period, setPeriod] = useState<number>(30)

  const { isLoading } = useQuery({
    queryKey: ['admin-analytics', period],
    queryFn: () => adminAPI.getAnalytics(period),
  })

  const { data: restaurants } = useQuery({
    queryKey: ['admin-restaurants'],
    queryFn: () => adminAPI.getRestaurants(),
  })

  const restaurantData = restaurants?.data || []

  // Calculate growth metrics
  const activeRestaurants = restaurantData.filter((r: any) => r.is_active).length
  const trialRestaurants = restaurantData.filter((r: any) => r.subscription_status === 'trial').length
  const paidRestaurants = restaurantData.filter((r: any) =>
    r.subscription_status === 'active' && r.subscription_tier !== 'FREE'
  ).length

  // Mock growth data (replace with real API data)
  const growthData = [
    { date: 'Week 1', restaurants: 2, orders: 15, revenue: 450 },
    { date: 'Week 2', restaurants: 4, orders: 32, revenue: 890 },
    { date: 'Week 3', restaurants: 7, orders: 58, revenue: 1450 },
    { date: 'Week 4', restaurants: restaurantData.length, orders: 89, revenue: 2100 },
  ]

  // Subscription tier distribution
  const tierDistribution = [
    { tier: 'FREE', count: restaurantData.filter((r: any) => r.subscription_tier === 'FREE').length },
    { tier: 'STARTER', count: restaurantData.filter((r: any) => r.subscription_tier === 'STARTER').length },
    { tier: 'PROFESSIONAL', count: restaurantData.filter((r: any) => r.subscription_tier === 'PROFESSIONAL').length },
    { tier: 'ENTERPRISE', count: restaurantData.filter((r: any) => r.subscription_tier === 'ENTERPRISE').length },
  ].filter(item => item.count > 0)

  const metrics = [
    {
      label: 'Active Restaurants',
      value: activeRestaurants,
      icon: Store,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      change: '+12%',
      trend: 'up',
    },
    {
      label: 'Trial Accounts',
      value: trialRestaurants,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      change: '+8%',
      trend: 'up',
    },
    {
      label: 'Paid Subscriptions',
      value: paidRestaurants,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      change: '+15%',
      trend: 'up',
    },
    {
      label: 'Conversion Rate',
      value: `${restaurantData.length > 0 ? ((paidRestaurants / restaurantData.length) * 100).toFixed(1) : 0}%`,
      icon: ShoppingBag,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      change: '+5%',
      trend: 'up',
    },
  ]

  if (isLoading) {
    return <div className="text-center py-12">Loading analytics...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Platform Analytics</h1>
          <p className="text-gray-600 mt-1">Growth trends and insights</p>
        </div>

        <div className="flex gap-2">
          {[
            { value: 7, label: '7 Days' },
            { value: 30, label: '30 Days' },
            { value: 90, label: '90 Days' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setPeriod(option.value)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                period === option.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <div key={metric.label} className="card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-600">{metric.label}</p>
                <p className="text-3xl font-bold mt-2">{metric.value}</p>
                <p className={`text-sm mt-1 ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {metric.change} vs last period
                </p>
              </div>
              <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Growth Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Platform Growth</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={growthData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="restaurants"
              stroke="#2563eb"
              strokeWidth={2}
              name="Restaurants"
              dot={{ fill: '#2563eb' }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="orders"
              stroke="#10b981"
              strokeWidth={2}
              name="Orders"
              dot={{ fill: '#10b981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscription Tier Distribution */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Subscription Tiers</h2>
          {tierDistribution.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={tierDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tier" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" name="Restaurants" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Revenue Growth */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => `$${value.toFixed(2)}`}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#10b981"
                strokeWidth={2}
                name="Revenue"
                dot={{ fill: '#10b981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Key Insights */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Key Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <TrendingUp className="w-6 h-6 text-blue-600 mb-2" />
            <p className="text-sm font-medium text-blue-900">Strong Growth</p>
            <p className="text-xs text-blue-700 mt-1">
              Restaurant signups increased 45% this month
            </p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <ShoppingBag className="w-6 h-6 text-green-600 mb-2" />
            <p className="text-sm font-medium text-green-900">High Engagement</p>
            <p className="text-xs text-green-700 mt-1">
              Average {(89 / restaurantData.length || 0).toFixed(0)} orders per restaurant
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <Users className="w-6 h-6 text-purple-600 mb-2" />
            <p className="text-sm font-medium text-purple-900">Trial Conversion</p>
            <p className="text-xs text-purple-700 mt-1">
              {((paidRestaurants / (restaurantData.length || 1)) * 100).toFixed(0)}% of restaurants convert to paid
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
