import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { CheckCircle, XCircle, X, DollarSign, CreditCard } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

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
      <div className="flex gap-2">
        {['all', 'pending', 'completed', 'cancelled'].map((status) => (
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
                <th>Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orderData.map((order: any) => (
                  <tr key={order.id}>
                    <td className="font-medium">#{order.id}</td>
                    <td>{order.customer_name || 'Guest'}</td>
                    <td className="text-dim">
                      {order.order_items.length > 0
                        ? `${order.order_items.length} item${order.order_items.length > 1 ? 's' : ''}`
                        : '-'}
                    </td>
                    <td>${(order.total / 100).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${
                        order.status === 'completed' ? 'badge-success' :
                        order.status === 'pending' ? 'badge-warning' : 'badge-danger'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        order.payment_status === 'paid' ? 'badge-success' :
                        order.payment_status === 'pending' ? 'badge-warning' : 'badge-danger'
                      }`}>
                        {order.payment_status || 'pending'}
                      </span>
                    </td>
                    <td className="text-dim">
                      {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                <span className={`badge ${
                  selectedOrder.status === 'completed' ? 'badge-success' :
                  selectedOrder.status === 'pending' ? 'badge-warning' : 'badge-danger'
                }`}>
                  {selectedOrder.status}
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

              {/* Special Instructions */}
              {selectedOrder.special_instructions && (
                <div className="p-3 rounded bg-yellow-500/10 border border-yellow-500/20">
                  <p className="text-xs text-dim uppercase mb-1">Note</p>
                  <p className="text-sm text-yellow-400">{selectedOrder.special_instructions}</p>
                </div>
              )}

              {/* Actions */}
              {selectedOrder.status === 'pending' && (
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'completed' })}
                    className="btn btn-success flex-1 flex items-center justify-center gap-2"
                    disabled={updateStatusMutation.isPending}
                  >
                    <CheckCircle className="w-4 h-4" />
                    Complete
                  </button>
                  <button
                    onClick={() => updateStatusMutation.mutate({ id: selectedOrder.id, status: 'cancelled' })}
                    className="btn btn-danger flex-1 flex items-center justify-center gap-2"
                    disabled={updateStatusMutation.isPending}
                  >
                    <XCircle className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
