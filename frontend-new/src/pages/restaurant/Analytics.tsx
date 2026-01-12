import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { TrendingUp, DollarSign, ShoppingBag } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function RestaurantAnalytics() {
  const { user } = useAuth()
  const restaurantId = user?.id

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', restaurantId],
    queryFn: () => restaurantAPI.getOrders(restaurantId!),
    enabled: !!restaurantId,
  })

  const orderData = orders?.data || []

  // Calculate daily revenue for last 7 days
  const getLast7Days = () => {
    const days = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      days.push({
        date: date.toISOString().split('T')[0],
        label: date.toLocaleDateString('en-US', { weekday: 'short' }),
      })
    }
    return days
  }

  const dailyRevenue = getLast7Days().map((day) => {
    const dayOrders = orderData.filter((o: any) => {
      const orderDate = new Date(o.created_at).toISOString().split('T')[0]
      return orderDate === day.date
    })
    return {
      day: day.label,
      revenue: dayOrders.reduce((sum: number, o: any) => sum + o.total, 0) / 100,
      orders: dayOrders.length,
    }
  })

  const totalRevenue = orderData.reduce((sum: number, o: any) => sum + o.total, 0) / 100
  const avgOrderValue = orderData.length > 0 ? totalRevenue / orderData.length : 0

  if (isLoading) {
    return <div className="text-center py-12">Loading analytics...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-gray-600 mt-1">Insights and performance metrics</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Revenue</p>
              <p className="text-3xl font-bold mt-2">${totalRevenue.toFixed(2)}</p>
              <p className="text-sm text-green-600 mt-1">All time</p>
            </div>
            <div className="p-3 rounded-lg bg-green-50">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Orders</p>
              <p className="text-3xl font-bold mt-2">{orderData.length}</p>
              <p className="text-sm text-blue-600 mt-1">All time</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50">
              <ShoppingBag className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Order Value</p>
              <p className="text-3xl font-bold mt-2">${avgOrderValue.toFixed(2)}</p>
              <p className="text-sm text-purple-600 mt-1">Per order</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-50">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Revenue Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Daily Revenue (Last 7 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dailyRevenue}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ fill: '#2563eb' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Orders Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Daily Orders (Last 7 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dailyRevenue}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="orders" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
