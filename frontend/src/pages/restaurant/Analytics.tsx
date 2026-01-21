import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Area, AreaChart
} from 'recharts'
import {
  TrendingUp, DollarSign, ShoppingBag, Clock, Users, Star
} from 'lucide-react'
import LoadingTRex from '../../components/LoadingTRex'

type TimePeriod = 7 | 30 | 90

interface PopularItem {
  item_name: string
  quantity_sold: number
  revenue_cents: number
  order_count: number
}

interface DailyTrend {
  date: string
  order_count: number
  revenue_cents: number
  avg_order_value_cents: number
}

interface AnalyticsSummary {
  period_start: string
  period_end: string
  total_orders: number
  total_revenue_cents: number
  avg_order_value_cents: number
  takeout_orders: number
  delivery_orders: number
  popular_items: PopularItem[]
  daily_trends: DailyTrend[]
  peak_hours: Record<number, number>
  repeat_customer_rate: number
}

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#0891b2', '#4f46e5', '#c026d3']

export default function RestaurantAnalytics() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>(30)

  const { data: analyticsData, isLoading, error } = useQuery({
    queryKey: ['analytics-summary', timePeriod],
    queryFn: () => restaurantAPI.getAnalyticsSummary(timePeriod),
  })

  const analytics: AnalyticsSummary | undefined = analyticsData?.data

  // Format currency
  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100)
  }

  // Format date for chart
  const formatChartDate = (dateStr: string) => {
    const date = new Date(dateStr)
    if (timePeriod <= 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    } else if (timePeriod <= 30) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  // Prepare chart data
  const chartData = analytics?.daily_trends.map(d => ({
    date: formatChartDate(d.date),
    fullDate: d.date,
    orders: d.order_count,
    revenue: d.revenue_cents / 100,
    avgOrder: d.avg_order_value_cents / 100,
  })) || []

  // Only show every Nth label to avoid crowding
  const skipLabels = timePeriod > 30 ? 7 : timePeriod > 14 ? 3 : 1

  // Prepare peak hours data
  const peakHoursData = analytics ? Object.entries(analytics.peak_hours)
    .map(([hour, count]) => ({
      hour: parseInt(hour),
      hourLabel: `${parseInt(hour) % 12 || 12}${parseInt(hour) < 12 ? 'am' : 'pm'}`,
      orders: count,
    }))
    .sort((a, b) => a.hour - b.hour) : []

  // Order type distribution for pie chart
  const orderTypeData = analytics ? [
    { name: 'Takeout', value: analytics.takeout_orders, color: '#2563eb' },
    { name: 'Delivery', value: analytics.delivery_orders, color: '#7c3aed' },
  ].filter(d => d.value > 0) : []

  if (isLoading) {
    return <LoadingTRex message="Loading analytics" />
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        Failed to load analytics. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Insights and performance metrics</p>
        </div>

        {/* Time Period Selector */}
        <div className="flex gap-2">
          {([7, 30, 90] as TimePeriod[]).map((days) => (
            <button
              key={days}
              onClick={() => setTimePeriod(days)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timePeriod === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {days === 7 ? '7 Days' : days === 30 ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Revenue</p>
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(analytics?.total_revenue_cents || 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Last {timePeriod} days</p>
            </div>
            <div className="p-3 rounded-lg bg-green-50">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Orders</p>
              <p className="text-2xl font-bold mt-1">{analytics?.total_orders || 0}</p>
              <p className="text-xs text-gray-500 mt-1">Last {timePeriod} days</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50">
              <ShoppingBag className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Order Value</p>
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(analytics?.avg_order_value_cents || 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Per order</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-50">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Repeat Customers</p>
              <p className="text-2xl font-bold mt-1">{analytics?.repeat_customer_rate || 0}%</p>
              <p className="text-xs text-gray-500 mt-1">Return rate</p>
            </div>
            <div className="p-3 rounded-lg bg-orange-50">
              <Users className="w-5 h-5 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Revenue Trend Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                interval={skipLabels - 1}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#2563eb"
                strokeWidth={2}
                fill="url(#colorRevenue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-gray-500">
            No order data available for this period
          </div>
        )}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Popular Items */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-5 h-5 text-yellow-500" />
            <h2 className="text-lg font-semibold">Popular Items</h2>
          </div>
          {analytics?.popular_items && analytics.popular_items.length > 0 ? (
            <div className="space-y-3">
              {analytics.popular_items.slice(0, 8).map((item, index) => (
                <div key={item.item_name} className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold`}
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}>
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.item_name}</p>
                    <p className="text-sm text-gray-500">
                      {item.quantity_sold} sold · {item.order_count} orders
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">
                      {formatCurrency(item.revenue_cents)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No items sold in this period
            </div>
          )}
        </div>

        {/* Order Distribution */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <ShoppingBag className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold">Order Types</h2>
          </div>
          {orderTypeData.length > 0 ? (
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={orderTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {orderTypeData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [value, 'Orders']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {orderTypeData.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm">{entry.name}: {entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No orders in this period
            </div>
          )}
        </div>
      </div>

      {/* Peak Hours */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-purple-500" />
          <h2 className="text-lg font-semibold">Peak Hours</h2>
        </div>
        {peakHoursData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={peakHoursData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="hourLabel" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => [value, 'Orders']}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Bar dataKey="orders" fill="#7c3aed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No order timing data available
          </div>
        )}
      </div>

      {/* Daily Orders Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Daily Orders</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                interval={skipLabels - 1}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === 'orders' ? value : `$${value.toFixed(2)}`,
                  name === 'orders' ? 'Orders' : 'Avg Order'
                ]}
              />
              <Bar dataKey="orders" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No order data available
          </div>
        )}
      </div>
    </div>
  )
}
