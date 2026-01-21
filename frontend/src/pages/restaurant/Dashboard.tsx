import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import {
  ShoppingBag,
  DollarSign,
  Clock,
  TrendingUp,
  CheckCircle,
  Package,
  ArrowUpRight,
  AlertTriangle,
  Menu as MenuIcon,
  X,
  User,
  CreditCard,
  FileText,
  Phone
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'
import { useState } from 'react'

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label, prefix = '' }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-lg">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-bold text-gray-900">{prefix}{payload[0].value}</p>
      </div>
    )
  }
  return null
}

export default function RestaurantDashboard() {
  const { user } = useAuth()
  const restaurantId = user?.id
  const navigate = useNavigate()
  const [selectedOrder, setSelectedOrder] = useState<any>(null)

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders', restaurantId],
    queryFn: () => restaurantAPI.getOrders(restaurantId!),
    enabled: !!restaurantId,
    refetchInterval: 5000,
    placeholderData: (previousData) => previousData,
    staleTime: 1000,
  })

  const { data: menuData } = useQuery({
    queryKey: ['menu', restaurantId],
    queryFn: async () => {
      const response = await restaurantAPI.getMenu(restaurantId!)
      return response.data
    },
    enabled: !!restaurantId,
    placeholderData: (previousData) => previousData,
    refetchOnMount: 'always',
  })

  const hasMenus = menuData?.menus && menuData.menus.length > 0
  const hasMenuItems = hasMenus &&
    menuData.menus.some((menu: any) =>
      menu.categories && menu.categories.some((cat: any) =>
        cat.items && cat.items.length > 0
      )
    )

  const orderData = orders?.data || []

  // Calculate stats
  const todayOrders = orderData.filter((o: any) => {
    const orderDate = new Date(o.created_at).toDateString()
    const today = new Date().toDateString()
    return orderDate === today
  })

  const pendingOrders = orderData.filter((o: any) => o.status === 'pending').length
  const completedToday = todayOrders.filter((o: any) => o.status === 'completed').length
  const todayRevenue = todayOrders.reduce((sum: number, o: any) => sum + o.total, 0) / 100
  const totalRevenue = orderData.reduce((sum: number, o: any) => sum + o.total, 0) / 100

  // Chart data - last 7 days
  const getLast7Days = () => {
    const days = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      const dayOrders = orderData.filter((o: any) => {
        const orderDate = new Date(o.created_at).toDateString()
        return orderDate === date.toDateString()
      })
      days.push({
        day: date.toLocaleDateString('en-US', { weekday: 'short' }),
        orders: dayOrders.length,
        revenue: dayOrders.reduce((sum: number, o: any) => sum + o.total, 0) / 100
      })
    }
    return days
  }

  const weekData = getLast7Days()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm text-center py-12 max-w-md mx-auto">
        <div className="w-12 h-12 mx-auto rounded-lg bg-red-50 flex items-center justify-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-600" />
        </div>
        <p className="text-red-600 font-semibold">Error loading dashboard</p>
        <p className="text-sm text-gray-500 mt-2">Please refresh the page</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Setup Warning - Menu Items */}
      {!hasMenuItems && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-amber-100">
              <AlertTriangle className="w-6 h-6 text-amber-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Complete Your Setup</h3>
              <div className="flex items-center justify-between bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-3">
                  <MenuIcon className="w-5 h-5 text-amber-600" />
                  <div>
                    <p className="font-medium text-gray-900">
                      {hasMenus ? 'No Menu Items Yet' : 'No Menu Created'}
                    </p>
                    <p className="text-sm text-gray-500">Add items so customers can order</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/restaurant/menu')}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  {hasMenus ? 'Add Items' : 'Create Menu'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Welcome Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Welcome back</h1>
            <p className="text-gray-500">Here's what's happening with your restaurant today</p>
          </div>
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-medium text-green-700">Live Dashboard</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Today's Revenue */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Today's Revenue</p>
              <p className="text-3xl font-bold text-green-600 mt-2">${todayRevenue.toFixed(0)}</p>
              <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                From {todayOrders.length} orders
              </p>
            </div>
            <div className="p-3 rounded-lg bg-green-50">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Pending Orders */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Pending Orders</p>
              <p className="text-3xl font-bold text-amber-600 mt-2">{pendingOrders}</p>
              {pendingOrders > 0 ? (
                <div className="flex items-center gap-2 mt-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-xs text-amber-600 font-medium">Needs attention</span>
                </div>
              ) : (
                <p className="text-xs text-gray-500 mt-2">All clear</p>
              )}
            </div>
            <div className="p-3 rounded-lg bg-amber-50">
              <Clock className="w-6 h-6 text-amber-600" />
            </div>
          </div>
        </div>

        {/* Completed Today */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Completed Today</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{completedToday}</p>
              <p className="text-xs text-gray-500 mt-2">{todayOrders.length} total orders</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50">
              <CheckCircle className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Total Revenue */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Total Revenue</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">${totalRevenue.toFixed(0)}</p>
              <p className="text-xs text-gray-500 mt-2">All time</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-100">
              <TrendingUp className="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue Chart */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Revenue Trend</h2>
            <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full font-medium">
              ${weekData.reduce((sum, d) => sum + d.revenue, 0).toFixed(0)} this week
            </span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={weekData}>
              <defs>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#16a34a" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#16a34a" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip prefix="$" />} />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#16a34a"
                strokeWidth={2}
                fill="url(#revenueGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Orders Chart */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Orders</h2>
            <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium">
              {weekData.reduce((sum, d) => sum + d.orders, 0)} this week
            </span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weekData}>
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="orders" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
          <button
            onClick={() => navigate('/restaurant/orders')}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            View All <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>

        {todayOrders.length === 0 ? (
          <div className="text-center py-16 bg-gray-50 rounded-lg">
            <div className="w-16 h-16 mx-auto rounded-lg bg-gray-200 flex items-center justify-center mb-4">
              <Package className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-gray-500 font-medium">No orders yet today</p>
            <p className="text-gray-400 text-sm mt-1">Orders will appear here as they come in</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayOrders.slice(0, 5).map((order: any) => (
              <div
                key={order.id}
                onClick={() => setSelectedOrder(order)}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/30 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    order.status === 'completed' ? 'bg-green-100' :
                    order.status === 'pending' ? 'bg-amber-100' : 'bg-red-100'
                  }`}>
                    {order.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : order.status === 'pending' ? (
                      <Clock className="w-5 h-5 text-amber-600" />
                    ) : (
                      <ShoppingBag className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Order #{order.id}</p>
                    <p className="text-sm text-gray-500">{order.customer_name || 'Anonymous'}</p>
                    <p className="text-xs text-gray-400">{new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-gray-900">${(order.total / 100).toFixed(2)}</p>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    order.status === 'completed' ? 'bg-green-100 text-green-700' :
                    order.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <>
          <div
            onClick={() => setSelectedOrder(null)}
            className="fixed inset-0 bg-black/50 z-40"
          />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="bg-white rounded-xl shadow-xl max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-gray-900">Order #{selectedOrder.id}</h2>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                    selectedOrder.status === 'completed' ? 'bg-green-100 text-green-700' :
                    selectedOrder.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {selectedOrder.status}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                {/* Customer Info */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    Customer Information
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <div className="flex items-center gap-3">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 text-sm">Name:</span>
                      <span className="text-gray-900 font-medium">{selectedOrder.customer_name || 'Anonymous'}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 text-sm">Phone:</span>
                      <span className="text-gray-900 font-medium">{selectedOrder.customer_phone || 'No phone'}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 text-sm">Ordered:</span>
                      <span className="text-gray-900 font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Order Items */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Order Items
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                    {(() => {
                      try {
                        const items = typeof selectedOrder.order_items === 'string'
                          ? JSON.parse(selectedOrder.order_items)
                          : selectedOrder.order_items || []
                        return items.map((item: any, idx: number) => (
                          <div key={idx} className="flex items-start justify-between py-2 border-b border-gray-200 last:border-0">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-blue-600 font-bold">{item.quantity || 1}x</span>
                                <span className="text-gray-900 font-medium">{item.item_name || item.name || 'Item'}</span>
                              </div>
                              {item.modifiers && item.modifiers.length > 0 && (
                                <p className="text-sm text-gray-500 ml-6">+ {item.modifiers.join(', ')}</p>
                              )}
                            </div>
                            <span className="text-gray-700 font-medium">${((item.price_cents || 0) / 100).toFixed(2)}</span>
                          </div>
                        ))
                      } catch (e) {
                        return <p className="text-sm text-gray-500">No items</p>
                      }
                    })()}
                  </div>
                </div>

                {/* Payment */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-blue-600" />
                    Payment
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between pt-2">
                      <span className="font-bold text-gray-900">Total</span>
                      <span className="text-2xl font-bold text-blue-600">${(selectedOrder.total / 100).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
