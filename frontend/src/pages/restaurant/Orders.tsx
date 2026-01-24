import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { X, DollarSign, CreditCard, MessageSquare, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

// Order status flow: pending -> preparing -> ready -> completed
// Can be cancelled from any state except completed
const ORDER_STATUSES = ['pending', 'preparing', 'ready', 'completed', 'cancelled'] as const
type OrderStatus = typeof ORDER_STATUSES[number]

const STATUS_CONFIG: Record<OrderStatus, { label: string; color: string; badgeClass: string }> = {
  pending: { label: 'Pending', color: 'text-yellow-400', badgeClass: 'badge-warning' },
  preparing: { label: 'Preparing', color: 'text-blue-400', badgeClass: 'bg-blue-500/20 text-blue-400' },
  ready: { label: 'Ready', color: 'text-green-400', badgeClass: 'bg-green-500/20 text-green-400' },
  completed: { label: 'Completed', color: 'text-emerald-400', badgeClass: 'badge-success' },
  cancelled: { label: 'Cancelled', color: 'text-red-400', badgeClass: 'badge-danger' },
}

// Parse order items once when data is fetched
const parseOrderItems = (items: any) => {
  if (!items) return []
  if (typeof items === 'string') {
    try {
      return JSON.parse(items)
    } catch {
      return []
    }
  }
  return items
}

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
    refetchInterval: 60000,
    staleTime: 30000,
    select: (response) => ({
      ...response,
      data: response.data.map((order: any) => ({
        ...order,
        order_items: parseOrderItems(order.order_items),
      })),
    }),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      restaurantAPI.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      setSelectedOrder(null)
    },
  })

  const updatePaymentMutation = useMutation({
    mutationFn: ({ id, payment_status, payment_method }: { id: number; payment_status: string; payment_method?: string }) =>
      restaurantAPI.updatePaymentStatus(id, payment_status, payment_method),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      // Update the selected order in place
      if (selectedOrder) {
        setSelectedOrder({ ...selectedOrder, payment_status: variables.payment_status, payment_method: variables.payment_method })
      }
    },
  })

  const orderData = orders?.data || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'pending', 'preparing', 'ready', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`btn btn-sm ${statusFilter === status ? 'btn-primary' : 'btn-secondary'}`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Orders Table */}
      <div className="card p-0">
        {orderData.length === 0 ? (
          <p className="text-dim text-sm p-8 text-center">No orders found</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Items</th>
                <th>Total</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Date/Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orderData.map((order: any) => (
                  <tr key={order.id}>
                    <td className="font-medium">#{order.id}</td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <span>{order.customer_name || 'Guest'}</span>
                        {order.special_instructions && (
                          <MessageSquare className="w-3.5 h-3.5 text-yellow-400" title="Has special instructions" />
                        )}
                      </div>
                    </td>
                    <td className="text-dim">
                      {order.order_items.length > 0
                        ? `${order.order_items.length} item${order.order_items.length > 1 ? 's' : ''}`
                        : '-'}
                    </td>
                    <td>${(order.total / 100).toFixed(2)}</td>
                    <td>
                      {order.status === 'completed' || order.status === 'cancelled' ? (
                        <span className={`badge ${STATUS_CONFIG[order.status as OrderStatus]?.badgeClass || 'badge-secondary'}`}>
                          {STATUS_CONFIG[order.status as OrderStatus]?.label || order.status}
                        </span>
                      ) : (
                        <div className="relative inline-block">
                          <select
                            value={order.status}
                            onChange={(e) => updateStatusMutation.mutate({ id: order.id, status: e.target.value })}
                            disabled={updateStatusMutation.isPending}
                            className={`appearance-none cursor-pointer rounded px-2 py-1 pr-6 text-xs font-medium border-0 focus:ring-1 focus:ring-accent ${STATUS_CONFIG[order.status as OrderStatus]?.badgeClass || 'bg-gray-500/20'}`}
                          >
                            {ORDER_STATUSES.filter(s => s !== 'cancelled').map((s) => (
                              <option key={s} value={s} className="bg-[--card] text-white">
                                {STATUS_CONFIG[s].label}
                              </option>
                            ))}
                          </select>
                          <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none opacity-60" />
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${
                        order.payment_status === 'paid' ? 'badge-success' :
                        order.payment_status === 'pending' ? 'badge-warning' : 'badge-danger'
                      }`}>
                        {order.payment_status || 'pending'}
                      </span>
                    </td>
                    <td className="text-dim text-sm">
                      <div>{new Date(order.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}</div>
                      <div>{new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </td>
                    <td>
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="text-accent text-sm hover:underline"
                      >
                        View
                      </button>
                    </td>
                  </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Order Modal */}
      {selectedOrder && (
        <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-[--border]">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold">Order #{selectedOrder.id}</h3>
                <span className={`badge ${STATUS_CONFIG[selectedOrder.status as OrderStatus]?.badgeClass || 'badge-secondary'}`}>
                  {STATUS_CONFIG[selectedOrder.status as OrderStatus]?.label || selectedOrder.status}
                </span>
              </div>
              <button onClick={() => setSelectedOrder(null)} className="text-dim hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Customer */}
              <div>
                <p className="text-xs text-dim uppercase mb-1">Customer</p>
                <p>{selectedOrder.customer_name || 'Guest'}</p>
                {selectedOrder.customer_phone && (
                  <p className="text-sm text-dim">{selectedOrder.customer_phone}</p>
                )}
              </div>

              {/* Items */}
              <div>
                <p className="text-xs text-dim uppercase mb-2">Items</p>
                <div className="space-y-2">
                  {selectedOrder.order_items.length > 0 ? (
                    selectedOrder.order_items.map((item: any, idx: number) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span>{item.quantity || 1}x {item.item_name || item.name || 'Item'}</span>
                        <span className="text-dim">${((item.price_cents || 0) / 100).toFixed(2)}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-dim">No items</p>
                  )}
                </div>
              </div>

              {/* Total */}
              <div className="pt-3 border-t border-[--border] flex justify-between font-semibold">
                <span>Total</span>
                <span>${(selectedOrder.total / 100).toFixed(2)}</span>
              </div>

              {/* Payment Status */}
              <div className="pt-3 border-t border-[--border]">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-dim uppercase">Payment</p>
                  <span className={`badge ${
                    selectedOrder.payment_status === 'paid' ? 'badge-success' :
                    selectedOrder.payment_status === 'pending' ? 'badge-warning' : 'badge-danger'
                  }`}>
                    {selectedOrder.payment_status || 'pending'}
                  </span>
                </div>
                {selectedOrder.payment_method && (
                  <p className="text-sm text-dim">Method: {selectedOrder.payment_method}</p>
                )}
                {selectedOrder.payment_status !== 'paid' && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => updatePaymentMutation.mutate({
                        id: selectedOrder.id,
                        payment_status: 'paid',
                        payment_method: 'cash'
                      })}
                      className="btn btn-sm btn-secondary flex items-center gap-1"
                      disabled={updatePaymentMutation.isPending}
                    >
                      <DollarSign className="w-3 h-3" />
                      Cash
                    </button>
                    <button
                      onClick={() => updatePaymentMutation.mutate({
                        id: selectedOrder.id,
                        payment_status: 'paid',
                        payment_method: 'card'
                      })}
                      className="btn btn-sm btn-secondary flex items-center gap-1"
                      disabled={updatePaymentMutation.isPending}
                    >
                      <CreditCard className="w-3 h-3" />
                      Card
                    </button>
                  </div>
                )}
              </div>

              {/* Pickup Time */}
              {selectedOrder.scheduled_time && (
                <div>
                  <p className="text-xs text-dim uppercase mb-1">Pickup Time</p>
                  <p>
                    {new Date(selectedOrder.scheduled_time).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
                    {' at '}
                    {new Date(selectedOrder.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              )}

              {/* Special Instructions / Requests */}
              {selectedOrder.special_instructions && (
                <div className="p-3 rounded bg-yellow-500/10 border border-yellow-500/20">
                  <p className="text-xs text-yellow-400 uppercase mb-1 font-medium">Special Instructions</p>
                  <p className="text-sm text-yellow-300 whitespace-pre-line">{selectedOrder.special_instructions}</p>
                </div>
              )}

              {/* Status Actions */}
              {selectedOrder.status !== 'completed' && selectedOrder.status !== 'cancelled' && (
                <div className="pt-3 border-t border-[--border]">
                  <p className="text-xs text-dim uppercase mb-2">Update Status</p>
                  <div className="flex gap-2 flex-wrap">
                    {selectedOrder.status === 'pending' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'preparing' })}
                        className="btn btn-sm bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                        disabled={updateStatusMutation.isPending}
                      >
                        Start Preparing
                      </button>
                    )}
                    {(selectedOrder.status === 'pending' || selectedOrder.status === 'preparing') && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'ready' })}
                        className="btn btn-sm bg-green-500/20 text-green-400 hover:bg-green-500/30"
                        disabled={updateStatusMutation.isPending}
                      >
                        Mark Ready
                      </button>
                    )}
                    {selectedOrder.status === 'ready' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'completed' })}
                        className="btn btn-sm btn-success"
                        disabled={updateStatusMutation.isPending}
                      >
                        Complete Order
                      </button>
                    )}
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'cancelled' })}
                      className="btn btn-sm btn-danger"
                      disabled={updateStatusMutation.isPending}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
