import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import {
  Clock,
  CheckCircle,
  XCircle,
  X,
  Phone,
  User,
  MapPin,
  CreditCard,
  FileText,
  ShoppingBag,
  DollarSign,
  Package
} from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import LoadingTRex from '../../components/LoadingTRex'

export default function RestaurantOrders() {
  const { user } = useAuth()
  const accountId = user?.id
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const queryClient = useQueryClient()

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', accountId, statusFilter],
    queryFn: () => {
      const params = statusFilter !== 'all' ? { status_filter: statusFilter } : undefined
      return restaurantAPI.getOrders(accountId!, params)
    },
    enabled: !!accountId,
    refetchInterval: 5000,
    staleTime: 0,
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      restaurantAPI.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })

  const orderData = orders?.data || []

  // Calculate stats
  const pendingCount = orderData.filter((o: any) => o.status === 'pending').length
  const completedToday = orderData.filter((o: any) => {
    const today = new Date().toDateString()
    return o.status === 'completed' && new Date(o.created_at).toDateString() === today
  }).length
  const totalRevenue = orderData
    .filter((o: any) => o.status === 'completed')
    .reduce((sum: number, o: any) => sum + (o.total || 0), 0)

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return 'badge-success'
      case 'pending':
        return 'badge-warning'
      case 'cancelled':
        return 'badge-danger'
      default:
        return 'badge-purple'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5" />
      case 'cancelled':
        return <XCircle className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  const getIconBox = (status: string) => {
    switch (status) {
      case 'completed':
        return 'icon-box-mint'
      case 'pending':
        return 'icon-box-orange'
      default:
        return ''
    }
  }

  if (isLoading) {
    return <LoadingTRex message="Loading orders" />
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pending Orders */}
        <div className="stat-card stat-card-orange">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-orange">
              <Package className="w-5 h-5" />
            </div>
            {pendingCount > 0 && (
              <span className="w-3 h-3 rounded-full animate-pulse" style={{ background: 'var(--accent-orange)' }} />
            )}
          </div>
          <p className="stat-label">Pending Orders</p>
          <p className="stat-value text-white mt-1">{pendingCount}</p>
          <p className="stat-sublabel">{pendingCount > 0 ? 'Needs attention' : 'All clear'}</p>
        </div>

        {/* Completed Today */}
        <div className="stat-card stat-card-mint">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-mint">
              <CheckCircle className="w-5 h-5" />
            </div>
          </div>
          <p className="stat-label">Completed Today</p>
          <p className="stat-value text-white mt-1">{completedToday}</p>
          <p className="stat-sublabel">Orders fulfilled</p>
        </div>

        {/* Revenue */}
        <div className="stat-card stat-card-cyan">
          <div className="flex items-center justify-between mb-4">
            <div className="icon-box icon-box-md icon-box-cyan">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <p className="stat-label">Total Revenue</p>
          <p className="stat-value text-white mt-1">${(totalRevenue / 100).toFixed(0)}</p>
          <p className="stat-sublabel">From completed orders</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        {['all', 'pending', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={statusFilter === status ? 'filter-tab-active' : 'filter-tab'}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Orders List */}
      {orderData.length === 0 ? (
        <div className="glass-card text-center py-16">
          <div className="icon-box icon-box-lg mx-auto mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <ShoppingBag className="w-8 h-8" style={{ color: 'var(--text-muted)' }} />
          </div>
          <p className="font-medium" style={{ color: 'var(--text-secondary)' }}>No orders found</p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Orders will appear here when customers place them</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orderData.map((order: any) => (
            <div
              key={order.id}
              onClick={() => setSelectedOrder(order)}
              className="glass-card cursor-pointer transition-all hover:scale-[1.01]"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {/* Status Icon */}
                  <div className={`icon-box icon-box-md ${getIconBox(order.status)}`}
                    style={order.status === 'cancelled' ? { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' } : {}}>
                    {getStatusIcon(order.status)}
                  </div>

                  {/* Order Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-bold text-white text-lg">
                        Order #{order.id}
                      </h3>
                      <span className={`badge ${getStatusBadge(order.status)}`}>
                        {order.status}
                      </span>
                      {order.payment_status && (
                        <span className={`badge ${order.payment_status === 'paid' ? 'badge-success' : 'badge-warning'}`}>
                          {order.payment_status === 'paid' ? 'Paid' : 'Unpaid'}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      <span className="flex items-center gap-1.5">
                        <User className="w-4 h-4" />
                        {order.customer_name || 'Anonymous'}
                      </span>
                      {order.customer_phone && (
                        <span className="flex items-center gap-1.5">
                          <Phone className="w-4 h-4" />
                          {order.customer_phone}
                        </span>
                      )}
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    {/* Order Items Preview */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(() => {
                        try {
                          const items = typeof order.order_items === 'string'
                            ? JSON.parse(order.order_items)
                            : order.order_items || []
                          return items.slice(0, 3).map((item: any, idx: number) => (
                            <span key={idx} className="px-2 py-1 rounded text-xs" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                              {item.quantity || 1}x {item.item_name || item.name || 'Item'}
                            </span>
                          ))
                        } catch (e) {
                          return null
                        }
                      })()}
                      {(() => {
                        try {
                          const items = typeof order.order_items === 'string'
                            ? JSON.parse(order.order_items)
                            : order.order_items || []
                          if (items.length > 3) {
                            return (
                              <span className="px-2 py-1 rounded text-xs" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
                                +{items.length - 3} more
                              </span>
                            )
                          }
                        } catch (e) {
                          return null
                        }
                      })()}
                    </div>

                    {order.special_instructions && (
                      <div className="mt-3 px-3 py-2 rounded-lg" style={{ background: 'rgba(255, 184, 108, 0.1)', border: '1px solid rgba(255, 184, 108, 0.3)' }}>
                        <p className="text-xs font-medium" style={{ color: 'var(--accent-orange)' }}>Note: {order.special_instructions}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Price & Actions */}
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold text-white">
                    ${(order.total / 100).toFixed(2)}
                  </p>
                  {order.status === 'pending' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateStatusMutation.mutate({ id: order.id, status: 'completed' })
                        }}
                        className="btn-success text-xs"
                      >
                        Complete
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateStatusMutation.mutate({ id: order.id, status: 'cancelled' })
                        }}
                        className="btn-danger text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

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
                <span className={`badge ${getStatusBadge(selectedOrder.status)}`}>
                  {selectedOrder.status}
                </span>
                {selectedOrder.payment_status && (
                  <span className={`badge ${selectedOrder.payment_status === 'paid' ? 'badge-success' : 'badge-warning'}`}>
                    {selectedOrder.payment_status === 'paid' ? 'Paid' : 'Unpaid'}
                  </span>
                )}
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
              {/* Customer Information */}
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

              {/* Delivery/Pickup */}
              <div className="space-y-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <MapPin className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
                  Delivery Information
                </h3>
                <div className="glass-card p-4">
                  {selectedOrder.delivery_address === 'Pickup' ? (
                    <div className="flex items-center gap-3">
                      <div className="icon-box icon-box-md" style={{ background: 'rgba(167, 139, 250, 0.15)', color: 'var(--accent-purple)' }}>
                        <Package className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-medium text-white">Pickup Order</p>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Customer will pick up at restaurant</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <div className="icon-box icon-box-md icon-box-orange">
                        <MapPin className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-medium text-white">Delivery Order</p>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{selectedOrder.delivery_address}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Payment */}
              <div className="space-y-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <CreditCard className="w-5 h-5" style={{ color: 'var(--accent-cyan)' }} />
                  Payment
                </h3>
                <div className="glass-card p-4 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span style={{ color: 'var(--text-muted)' }}>Subtotal</span>
                    <span className="text-white">${(selectedOrder.subtotal / 100).toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span style={{ color: 'var(--text-muted)' }}>Tax</span>
                    <span className="text-white">${(selectedOrder.tax / 100).toFixed(2)}</span>
                  </div>
                  {selectedOrder.delivery_fee > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span style={{ color: 'var(--text-muted)' }}>Delivery Fee</span>
                      <span className="text-white">${(selectedOrder.delivery_fee / 100).toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-3" style={{ borderTop: '1px solid var(--border-glass)' }}>
                    <span className="font-bold text-white">Total</span>
                    <span className="text-2xl font-bold" style={{ color: 'var(--accent-cyan)' }}>${(selectedOrder.total / 100).toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Special Instructions */}
              {selectedOrder.special_instructions && (
                <div className="space-y-3">
                  <h3 className="font-semibold text-white">Special Instructions</h3>
                  <div className="p-4 rounded-xl" style={{ background: 'rgba(255, 184, 108, 0.1)', border: '1px solid rgba(255, 184, 108, 0.3)' }}>
                    <p className="text-sm" style={{ color: 'var(--accent-orange)' }}>{selectedOrder.special_instructions}</p>
                  </div>
                </div>
              )}

              {/* Actions */}
              {selectedOrder.status === 'pending' && (
                <div className="flex gap-3 pt-4" style={{ borderTop: '1px solid var(--border-glass)' }}>
                  <button
                    onClick={() => {
                      updateStatusMutation.mutate({ id: selectedOrder.id, status: 'completed' })
                      setSelectedOrder(null)
                    }}
                    className="btn-success flex-1 py-3 inline-flex items-center justify-center gap-2"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Mark as Completed
                  </button>
                  <button
                    onClick={() => {
                      updateStatusMutation.mutate({ id: selectedOrder.id, status: 'cancelled' })
                      setSelectedOrder(null)
                    }}
                    className="btn-danger flex-1 py-3 inline-flex items-center justify-center gap-2"
                  >
                    <XCircle className="w-5 h-5" />
                    Cancel Order
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
