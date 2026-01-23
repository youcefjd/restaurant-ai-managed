import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { DollarSign, ShoppingBag, TrendingUp, Users, Clock } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import PageHeader from '../../components/ui/PageHeader'
import StatCard from '../../components/ui/StatCard'
import TimePeriodFilter from '../../components/ui/TimePeriodFilter'

type TimePeriod = 7 | 30 | 90

export default function RestaurantAnalytics() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>(30)

  const { data: analyticsData, isLoading } = useQuery({
    queryKey: ['analytics-summary', timePeriod],
    queryFn: () => restaurantAPI.getAnalyticsSummary(timePeriod),
    staleTime: 60000,
    select: (response) => response.data,
  })

  const { data: trendsData } = useQuery({
    queryKey: ['analytics-trends', timePeriod],
    queryFn: () => restaurantAPI.getOrderTrends(timePeriod),
    staleTime: 60000,
    select: (response) => response.data,
  })

  const { data: popularItemsData } = useQuery({
    queryKey: ['analytics-popular-items', timePeriod],
    queryFn: () => restaurantAPI.getPopularItems(timePeriod, 10),
    staleTime: 60000,
    select: (response) => response.data,
  })

  const formatCurrency = (cents: number) => `$${(cents / 100).toFixed(2)}`

  // Calculate peak hour
  const peakHourData = useMemo(() => {
    if (!analyticsData?.peak_hours) return null
    const entries = Object.entries(analyticsData.peak_hours)
    if (entries.length === 0) return null
    return entries.reduce(
      (max, [hour, count]) => (count as number > max.count ? { hour: parseInt(hour), count: count as number } : max),
      { hour: 0, count: 0 }
    )
  }, [analyticsData?.peak_hours])

  const formatHour = (hour: number) => {
    const h = hour % 12 || 12
    return `${h}${hour < 12 ? 'am' : 'pm'}`
  }

  // Generate heatmap data for peak hours
  const peakHoursGrid = useMemo(() => {
    if (!analyticsData?.peak_hours) return []
    const hours = Array.from({ length: 24 }, (_, i) => i)
    const maxCount = Math.max(...Object.values(analyticsData.peak_hours as Record<string, number>), 1)
    return hours.map(hour => ({
      hour,
      count: (analyticsData.peak_hours as Record<string, number>)[hour] || 0,
      intensity: ((analyticsData.peak_hours as Record<string, number>)[hour] || 0) / maxCount,
    }))
  }, [analyticsData?.peak_hours])

  // Format trends for chart
  const chartData = useMemo(() => {
    if (!trendsData || trendsData.length === 0) return []
    return trendsData.map((day: any) => ({
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      revenue: day.revenue_cents / 100,
      orders: day.order_count,
    }))
  }, [trendsData])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        subtitle={`Performance over the last ${timePeriod} days`}
        actions={<TimePeriodFilter value={timePeriod} onChange={setTimePeriod} />}
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Revenue"
          value={formatCurrency(analyticsData?.total_revenue_cents || 0)}
          icon={DollarSign}
        />
        <StatCard
          label="Orders"
          value={analyticsData?.total_orders || 0}
          icon={ShoppingBag}
        />
        <StatCard
          label="Avg Order"
          value={formatCurrency(analyticsData?.avg_order_value_cents || 0)}
          icon={TrendingUp}
        />
        <StatCard
          label="Repeat Rate"
          value={`${analyticsData?.repeat_customer_rate || 0}%`}
          icon={Users}
        />
      </div>

      {/* Revenue Chart */}
      {chartData.length > 0 && (
        <div className="card">
          <h3 className="font-medium mb-4">Revenue Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'var(--text-dim)', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'var(--text-dim)', fontSize: 12 }}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'var(--text)' }}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  fill="url(#colorRevenue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Peak Hours Heatmap */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Peak Hours
            </h3>
            {peakHourData && peakHourData.count > 0 && (
              <span className="text-sm text-dim">
                Busiest: {formatHour(peakHourData.hour)} ({peakHourData.count} orders)
              </span>
            )}
          </div>
          {peakHoursGrid.length > 0 ? (
            <div className="grid grid-cols-12 gap-1">
              {peakHoursGrid.map(({ hour, count, intensity }) => (
                <div
                  key={hour}
                  className="aspect-square rounded flex items-center justify-center text-xs"
                  style={{
                    backgroundColor: intensity > 0 ? `rgba(59, 130, 246, ${0.2 + intensity * 0.6})` : 'rgba(255,255,255,0.05)',
                  }}
                  title={`${formatHour(hour)}: ${count} orders`}
                >
                  {hour % 6 === 0 && (
                    <span className="text-[10px] text-dim">{formatHour(hour)}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-dim text-sm py-4 text-center">No data</p>
          )}
          <p className="text-xs text-dim mt-3 text-center">24-hour view (hover for details)</p>
        </div>

        {/* Order Types */}
        <div className="card">
          <h3 className="font-medium mb-4">Order Types</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">Takeout</span>
                <span className="font-medium">{analyticsData?.takeout_orders || 0}</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full"
                  style={{
                    width: `${analyticsData?.total_orders ? (analyticsData.takeout_orders / analyticsData.total_orders) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">Delivery</span>
                <span className="font-medium">{analyticsData?.delivery_orders || 0}</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full bg-success rounded-full"
                  style={{
                    width: `${analyticsData?.total_orders ? (analyticsData.delivery_orders / analyticsData.total_orders) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Popular Items */}
      <div className="card">
        <h3 className="font-medium mb-4">Top Selling Items</h3>
        {popularItemsData && popularItemsData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Item</th>
                  <th className="text-right">Qty Sold</th>
                  <th className="text-right">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {popularItemsData.slice(0, 10).map((item: any, idx: number) => (
                  <tr key={item.item_name}>
                    <td className="text-dim">{idx + 1}</td>
                    <td className="font-medium">{item.item_name}</td>
                    <td className="text-right">{item.quantity_sold}</td>
                    <td className="text-right text-success">{formatCurrency(item.revenue_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-dim text-sm py-8 text-center">No items sold in this period</p>
        )}
      </div>
    </div>
  )
}
