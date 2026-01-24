import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { ShoppingBag, DollarSign, Clock, CheckCircle, UtensilsCrossed, ArrowRight, AlertCircle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/ui/PageHeader'
import StatCard from '../../components/ui/StatCard'

export default function RestaurantDashboard() {
  const { user } = useAuth()
  const restaurantId = user?.id
  const navigate = useNavigate()

  // Use dedicated endpoint for today's orders (much faster than fetching all)
  const { data: todayOrdersData, isLoading: todayLoading } = useQuery({
    queryKey: ['orders-today'],
    queryFn: () => restaurantAPI.getTodayOrders(),
    refetchInterval: 30000, // Refresh every 30s for dashboard
    staleTime: 15000,
  })

  // Use dedicated endpoint for active orders
  const { data: activeOrdersData } = useQuery({
    queryKey: ['orders-active'],
    queryFn: () => restaurantAPI.getActiveOrders(),
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: menuData } = useQuery({
    queryKey: ['menu', restaurantId],
    queryFn: () => restaurantAPI.getMenu(restaurantId!),
    enabled: !!restaurantId,
    staleTime: 300000, // Menu changes infrequently, cache for 5 min
  })

  const todayOrders = todayOrdersData?.data || []
  const activeOrders = activeOrdersData?.data || []
  const menu = menuData?.data

  // Filter pending from active orders for the list (shows ALL pending orders needing attention)
  const allPendingOrders = useMemo(() =>
    activeOrders.filter((o: any) => o.status === 'pending'),
    [activeOrders]
  )

  // Calculate today's stats - all stats should be consistent (today only)
  const { pendingToday, completedToday, todayRevenue } = useMemo(() => {
    const pendingToday = todayOrders.filter((o: any) => o.status === 'pending').length
    const completedToday = todayOrders.filter((o: any) => o.status === 'completed').length
    const todayRevenue = todayOrders.reduce((sum: number, o: any) => sum + (o.total || 0), 0) / 100
    return { pendingToday, completedToday, todayRevenue }
  }, [todayOrders])

  // Memoized menu stats
  const { menuCount, itemCount } = useMemo(() => {
    const menuCount = menu?.menus?.length || 0
    const itemCount = menu?.menus?.reduce((sum: number, m: any) =>
      sum + (m.categories?.reduce((catSum: number, c: any) => catSum + (c.items?.length || 0), 0) || 0), 0) || 0
    return { menuCount, itemCount }
  }, [menu])

  if (todayLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back${user?.business_name ? `, ${user.business_name}` : ''}`}
        subtitle="Here's what's happening today"
      />

      {/* Main Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Orders Today"
          value={todayOrders.length}
          icon={ShoppingBag}
        />
        <StatCard
          label="Pending"
          value={pendingToday}
          icon={Clock}
        />
        <StatCard
          label="Completed"
          value={completedToday}
          icon={CheckCircle}
        />
        <StatCard
          label="Revenue"
          value={`$${todayRevenue.toFixed(0)}`}
          icon={DollarSign}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Orders - Needs Attention */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium flex items-center gap-2">
              {allPendingOrders.length > 0 && <AlertCircle className="w-4 h-4 text-warning" />}
              Pending Orders
            </h3>
            <button onClick={() => navigate('/restaurant/orders')} className="text-sm text-accent flex items-center gap-1 hover:underline">
              View All <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {allPendingOrders.length === 0 ? (
            <div className="py-8 text-center">
              <CheckCircle className="w-10 h-10 text-success mx-auto mb-2" />
              <p className="text-dim">All caught up!</p>
            </div>
          ) : (
            <div className="space-y-2">
              {allPendingOrders.slice(0, 4).map((order: any) => (
                <div
                  key={order.id}
                  onClick={() => navigate('/restaurant/orders')}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer"
                >
                  <div>
                    <p className="font-medium">Order #{order.id}</p>
                    <p className="text-xs text-dim">{order.customer_name || 'Guest'}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${((order.total || 0) / 100).toFixed(2)}</p>
                    <p className="text-xs text-dim">
                      {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              {allPendingOrders.length > 4 && (
                <p className="text-xs text-dim text-center pt-2">+{allPendingOrders.length - 4} more</p>
              )}
            </div>
          )}
        </div>

        {/* Quick Actions / Menu Summary */}
        <div className="card">
          <h3 className="font-medium mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/restaurant/orders')}
              className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 text-left"
            >
              <div className="flex items-center gap-3">
                <ShoppingBag className="w-5 h-5 text-accent" />
                <span>Manage Orders</span>
              </div>
              <ArrowRight className="w-4 h-4 text-dim" />
            </button>

            <button
              onClick={() => navigate('/restaurant/menu')}
              className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 text-left"
            >
              <div className="flex items-center gap-3">
                <UtensilsCrossed className="w-5 h-5 text-accent" />
                <div>
                  <span>Edit Menu</span>
                  <p className="text-xs text-dim">{menuCount} menu{menuCount !== 1 ? 's' : ''}, {itemCount} items</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-dim" />
            </button>

            <button
              onClick={() => navigate('/restaurant/analytics')}
              className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 text-left"
            >
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-accent" />
                <span>View Analytics</span>
              </div>
              <ArrowRight className="w-4 h-4 text-dim" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
