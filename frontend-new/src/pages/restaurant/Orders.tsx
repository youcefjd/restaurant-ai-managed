import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Clock, CheckCircle, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

export default function RestaurantOrders() {
  const { user } = useAuth()
  const accountId = user?.id
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const queryClient = useQueryClient()

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', accountId, statusFilter],
    queryFn: () => {
      const params = statusFilter !== 'all' ? { status_filter: statusFilter } : undefined
      return restaurantAPI.getOrders(accountId!, params)
    },
    enabled: !!accountId,
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      restaurantAPI.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })

  const orderData = orders?.data || []

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700'
      case 'pending':
        return 'bg-orange-100 text-orange-700'
      case 'cancelled':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-blue-100 text-blue-700'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-orange-600" />
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading orders...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Orders</h1>
          <p className="text-gray-600 mt-1">Manage incoming orders</p>
        </div>

        <div className="flex gap-2">
          {['all', 'pending', 'completed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                statusFilter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {orderData.length === 0 ? (
        <div className="card text-center py-12">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No orders found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {orderData.map((order: any) => (
            <div key={order.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  {getStatusIcon(order.status)}
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-lg">Order #{order.id}</h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(order.status)}`}>
                        {order.status}
                      </span>
                      {order.payment_status && (
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                          order.payment_status === 'paid'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {order.payment_status === 'paid' ? '✓ Paid' : '⏳ Unpaid'}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {order.customer_name || 'Anonymous'} • {order.customer_phone || 'No phone'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(order.created_at).toLocaleString()}
                    </p>

                    {/* Order Items */}
                    <div className="mt-3 space-y-1">
                      {(() => {
                        try {
                          const items = typeof order.order_items === 'string'
                            ? JSON.parse(order.order_items)
                            : order.order_items || []
                          return items.map((item: any, idx: number) => (
                            <div key={idx} className="text-sm text-gray-700 flex items-center gap-2">
                              <span className="font-medium">{item.quantity || 1}x</span>
                              <span>{item.item_name || item.name || 'Item'}</span>
                              <span className="text-gray-500">
                                ${((item.price_cents || 0) / 100).toFixed(2)}
                              </span>
                              {item.modifiers && item.modifiers.length > 0 && (
                                <span className="text-xs text-gray-500">
                                  ({item.modifiers.join(', ')})
                                </span>
                              )}
                            </div>
                          ))
                        } catch (e) {
                          return <p className="text-sm text-gray-500">No items</p>
                        }
                      })()}
                    </div>

                    {/* Delivery/Pickup Info */}
                    {order.delivery_address && (
                      <p className="text-sm text-gray-600 mt-2">
                        <span className="font-medium">
                          {order.delivery_address === 'Pickup' ? '🏪 Pickup' : '🚚 Delivery:'}
                        </span>
                        {order.delivery_address !== 'Pickup' && ` ${order.delivery_address}`}
                      </p>
                    )}

                    {/* Payment Info */}
                    {order.payment_method && (
                      <div className="flex items-center gap-2 mt-2">
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">💳 Payment:</span> {order.payment_method}
                        </p>
                        {order.payment_status && (
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            order.payment_status === 'paid'
                              ? 'bg-green-100 text-green-700 border border-green-300'
                              : 'bg-amber-100 text-amber-700 border border-amber-300'
                          }`}>
                            {order.payment_status === 'paid' ? '✓ PAID' : '⏳ UNPAID'}
                          </span>
                        )}
                      </div>
                    )}

                    {order.special_instructions && (
                      <p className="text-sm text-gray-700 mt-2 bg-yellow-50 p-2 rounded border border-yellow-200">
                        <span className="font-medium">📝 Note:</span> {order.special_instructions}
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-600">
                    ${(order.total / 100).toFixed(2)}
                  </p>
                  {order.status === 'pending' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() =>
                          updateStatusMutation.mutate({ id: order.id, status: 'completed' })
                        }
                        className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Complete
                      </button>
                      <button
                        onClick={() =>
                          updateStatusMutation.mutate({ id: order.id, status: 'cancelled' })
                        }
                        className="text-sm px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
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
    </div>
  )
}
