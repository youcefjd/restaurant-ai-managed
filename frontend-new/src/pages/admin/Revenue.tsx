import { useQuery } from '@tanstack/react-query'
import { adminAPI } from '../../services/api'
import { DollarSign, TrendingUp, Percent } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useState } from 'react'

export default function AdminRevenue() {
  const [dateRange, setDateRange] = useState<'7d' | '30d' | 'all'>('30d')

  const { data: revenue, isLoading } = useQuery({
    queryKey: ['admin-revenue', dateRange],
    queryFn: () => {
      if (dateRange === 'all') {
        return adminAPI.getRevenue()
      }
      const days = dateRange === '7d' ? 7 : 30
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - days)

      return adminAPI.getRevenue({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      })
    },
  })

  const revenueData = revenue?.data || []

  // Calculate totals
  const totalProcessed = revenueData.reduce(
    (sum: number, item: any) => sum + item.total_revenue_cents,
    0
  )
  const totalCommission = revenueData.reduce(
    (sum: number, item: any) => sum + item.platform_commission_cents,
    0
  )
  const restaurantEarnings = totalProcessed - totalCommission
  const avgCommissionRate = totalProcessed > 0 ? (totalCommission / totalProcessed) * 100 : 0

  // Prepare chart data
  const chartData = revenueData.map((item: any) => ({
    name: item.business_name,
    revenue: item.total_revenue_cents / 100,
    commission: item.platform_commission_cents / 100,
    restaurant: (item.total_revenue_cents - item.platform_commission_cents) / 100,
  }))

  const metrics = [
    {
      label: 'Total Revenue Processed',
      value: `$${(totalProcessed / 100).toFixed(2)}`,
      icon: DollarSign,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      subtext: 'All transactions',
    },
    {
      label: 'Platform Commission',
      value: `$${(totalCommission / 100).toFixed(2)}`,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      subtext: 'Your earnings',
    },
    {
      label: 'Restaurant Earnings',
      value: `$${(restaurantEarnings / 100).toFixed(2)}`,
      icon: DollarSign,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      subtext: 'Paid to restaurants',
    },
    {
      label: 'Avg Commission Rate',
      value: `${avgCommissionRate.toFixed(1)}%`,
      icon: Percent,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      subtext: 'Platform fee',
    },
  ]

  if (isLoading) {
    return <div className="text-center py-12">Loading revenue data...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Revenue</h1>
          <p className="text-gray-600 mt-1">Track commission and payouts</p>
        </div>

        <div className="flex gap-2">
          {[
            { value: '7d', label: 'Last 7 Days' },
            { value: '30d', label: 'Last 30 Days' },
            { value: 'all', label: 'All Time' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setDateRange(option.value as any)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                dateRange === option.value
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
                <p className="text-xs text-gray-500 mt-1">{metric.subtext}</p>
              </div>
              <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Revenue by Restaurant Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Revenue by Restaurant</h2>
        {chartData.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No revenue data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => `$${value.toFixed(2)}`}
              />
              <Legend />
              <Bar dataKey="revenue" fill="#2563eb" name="Total Revenue" />
              <Bar dataKey="commission" fill="#10b981" name="Platform Commission" />
              <Bar dataKey="restaurant" fill="#8b5cf6" name="Restaurant Earnings" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Revenue Details Table */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Revenue Details</h2>
        {revenueData.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No revenue data yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Restaurant</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Orders</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Total Revenue</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Commission Rate</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Commission</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Restaurant Gets</th>
                </tr>
              </thead>
              <tbody>
                {revenueData.map((item: any) => (
                  <tr key={item.restaurant_id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{item.business_name}</td>
                    <td className="text-right py-3 px-4">{item.order_count}</td>
                    <td className="text-right py-3 px-4 font-medium">
                      ${(item.total_revenue_cents / 100).toFixed(2)}
                    </td>
                    <td className="text-right py-3 px-4">{item.commission_rate}%</td>
                    <td className="text-right py-3 px-4 text-green-600 font-medium">
                      ${(item.platform_commission_cents / 100).toFixed(2)}
                    </td>
                    <td className="text-right py-3 px-4 text-purple-600 font-medium">
                      ${((item.total_revenue_cents - item.platform_commission_cents) / 100).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
