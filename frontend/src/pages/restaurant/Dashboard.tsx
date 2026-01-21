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
  Phone,
  ArrowRight
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'
import { useState } from 'react'
import LoadingTRex from '../../components/LoadingTRex'

// Custom tooltip for charts - glassmorphism style
const CustomTooltip = ({ active, payload, label, prefix = '' }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3" style={{ minWidth: '80px' }}>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</p>
        <p className="text-lg font-bold" style={{ color: 'var(--accent-cyan)' }}>{prefix}{payload[0].value}</p>
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
    return <LoadingTRex message="Loading dashboard" />
  }

  if (error) {
    return (
      <div className="glass-card text-center py-12 max-w-md mx-auto">
        <div className="icon-box icon-box-lg mx-auto mb-4" style={{ background: 'rgba(239, 68, 68, 0.15)' }}>
          <AlertTriangle className="w-6 h-6 text-red-400" />
        </div>
        <p className="text-red-400 font-semibold">Error loading dashboard</p>
        <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>Please refresh the page</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Setup Warning - Menu Items */}
      {!hasMenuItems && (
        <div className="glass-card" style={{ background: 'linear-gradient(135deg, rgba(255, 184, 108, 0.1) 0%, var(--bg-card) 50%)' }}>
          <div className="flex items-start gap-4">
            <div className="icon-box icon-box-lg icon-box-orange">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-3">Complete Your Setup</h3>
              <div className="glass-card p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MenuIcon className="w-5 h-5" style={{ color: 'var(--accent-orange)' }} />
                  <div>
                    <p className="font-medium text-white">
                      {hasMenus ? 'No Menu Items Yet' : 'No Menu Created'}
                    </p>
                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Add items so customers can order</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/restaurant/menu')}
                  className="btn-primary flex items-center gap-2"
                >
                  {hasMenus ? 'Add Items' : 'Create Menu'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid - Styled like reference image */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Today's Revenue */}
        <div className="stat-card stat-card-mint">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-mint">
              <DollarSign className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-5 h-5" style={{ color: 'var(--accent-mint)' }} />
          </div>
          <p className="stat-label">Today's Revenue</p>
          <p className="stat-value text-white mt-1">${todayRevenue.toFixed(0)}</p>
          <p className="stat-sublabel">From {todayOrders.length} orders</p>
        </div>

        {/* Pending Orders */}
        <div className="stat-card stat-card-orange">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-orange">
              <Clock className="w-5 h-5" />
            </div>
            {pendingOrders > 0 && (
              <span className="w-3 h-3 rounded-full animate-pulse" style={{ background: 'var(--accent-orange)' }} />
            )}
          </div>
          <p className="stat-label">Pending Orders</p>
          <p className="stat-value text-white mt-1">{pendingOrders}</p>
          <p className="stat-sublabel">{pendingOrders > 0 ? 'Needs attention' : 'All clear'}</p>
        </div>

        {/* Completed Today */}
        <div className="stat-card stat-card-cyan">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-cyan">
              <CheckCircle className="w-5 h-5" />
            </div>
            <TrendingUp className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <p className="stat-label">Completed Today</p>
          <p className="stat-value text-white mt-1">{completedToday}</p>
          <p className="stat-sublabel">{todayOrders.length} total orders</p>
        </div>

        {/* Total Revenue */}
        <div className="stat-card stat-card-purple">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md" style={{ background: 'rgba(167, 139, 250, 0.15)', color: 'var(--accent-purple)' }}>
              <TrendingUp className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-5 h-5" style={{ color: 'var(--accent-purple)' }} />
          </div>
          <p className="stat-label">Total Revenue</p>
          <p className="stat-value text-white mt-1">${totalRevenue.toFixed(0)}</p>
          <p className="stat-sublabel">All time</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue Chart */}
        <div className="glass-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Revenue Trend</h2>
            <span className="badge badge-mint">
              ${weekData.reduce((sum, d) => sum + d.revenue, 0).toFixed(0)} this week
            </span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={weekData}>
              <defs>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7dffaf" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#7dffaf" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip prefix="$" />} />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#7dffaf"
                strokeWidth={2}
                fill="url(#revenueGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Orders Chart */}
        <div className="glass-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Orders</h2>
            <span className="badge badge-cyan">
              {weekData.reduce((sum, d) => sum + d.orders, 0)} this week
            </span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weekData}>
              <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="orders" fill="#00d4ff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="glass-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Recent Orders</h2>
          <button
            onClick={() => navigate('/restaurant/orders')}
            className="btn-glass text-sm flex items-center gap-2"
          >
            View All <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>

        {todayOrders.length === 0 ? (
          <div className="text-center py-16 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <div className="icon-box icon-box-lg mx-auto mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
              <Package className="w-8 h-8" style={{ color: 'var(--text-muted)' }} />
            </div>
            <p className="font-medium" style={{ color: 'var(--text-secondary)' }}>No orders yet today</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Orders will appear here as they come in</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayOrders.slice(0, 5).map((order: any) => (
              <div
                key={order.id}
                onClick={() => setSelectedOrder(order)}
                className="flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.01]"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-glass)'
                }}
              >
                <div className="flex items-center gap-4">
                  <div className={`icon-box icon-box-md ${
                    order.status === 'completed' ? 'icon-box-mint' :
                    order.status === 'pending' ? 'icon-box-orange' : ''
                  }`} style={order.status === 'cancelled' ? { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' } : {}}>
                    {order.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : order.status === 'pending' ? (
                      <Clock className="w-5 h-5" />
                    ) : (
                      <ShoppingBag className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold text-white">Order #{order.id}</p>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{order.customer_name || 'Anonymous'}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-white">${(order.total / 100).toFixed(2)}</p>
                  <span className={`badge ${
                    order.status === 'completed' ? 'badge-success' :
                    order.status === 'pending' ? 'badge-warning' :
                    'badge-danger'
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
            className="modal-backdrop"
          />
          <div className="modal-content max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="modal-header">
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-white">Order #{selectedOrder.id}</h2>
                <span className={`badge ${
                  selectedOrder.status === 'completed' ? 'badge-success' :
                  selectedOrder.status === 'pending' ? 'badge-warning' :
                  'badge-danger'
                }`}>
                  {selectedOrder.status}
                </span>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="btn-glass p-2"
              >
                <X className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
              </button>
            </div>

            {/* Content */}
            <div className="modal-body space-y-6">
              {/* Customer Info */}
              <div className="space-y-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <User className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
                  Customer Information
                </h3>
                <div className="glass-card p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <User className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Name:</span>
                    <span className="text-white font-medium">{selectedOrder.customer_name || 'Anonymous'}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Phone className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Phone:</span>
                    <span className="text-white font-medium">{selectedOrder.customer_phone || 'No phone'}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Ordered:</span>
                    <span className="text-white font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Order Items */}
              <div className="space-y-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
                  Order Items
                </h3>
                <div className="glass-card p-4 space-y-3">
                  {(() => {
                    try {
                      const items = typeof selectedOrder.order_items === 'string'
                        ? JSON.parse(selectedOrder.order_items)
                        : selectedOrder.order_items || []
                      return items.map((item: any, idx: number) => (
                        <div key={idx} className="flex items-start justify-between py-2" style={{ borderBottom: idx < items.length - 1 ? '1px solid var(--border-glass)' : 'none' }}>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold" style={{ color: 'var(--accent-cyan)' }}>{item.quantity || 1}x</span>
                              <span className="text-white font-medium">{item.item_name || item.name || 'Item'}</span>
                            </div>
                            {item.modifiers && item.modifiers.length > 0 && (
                              <p className="text-sm ml-6" style={{ color: 'var(--text-muted)' }}>+ {item.modifiers.join(', ')}</p>
                            )}
                          </div>
                          <span style={{ color: 'var(--text-secondary)' }}>${((item.price_cents || 0) / 100).toFixed(2)}</span>
                        </div>
                      ))
                    } catch (e) {
                      return <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No items</p>
                    }
                  })()}
                </div>
              </div>

              {/* Payment */}
              <div className="space-y-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <CreditCard className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
                  Payment
                </h3>
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">Total</span>
                    <span className="text-2xl font-bold" style={{ color: 'var(--accent-cyan)' }}>${(selectedOrder.total / 100).toFixed(2)}</span>
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
