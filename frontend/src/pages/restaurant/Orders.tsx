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

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700'
      case 'pending':
        return 'bg-amber-100 text-amber-700'
      case 'cancelled':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-amber-600" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pending Orders */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Pending Orders</p>
              <p className="text-3xl font-bold text-amber-600 mt-2">{pendingCount}</p>
              <p className="text-xs text-gray-500 mt-2">Awaiting confirmation</p>
            </div>
            <div className="p-3 rounded-lg bg-amber-50">
              <Package className="w-6 h-6 text-amber-600" />
            </div>
          </div>
          {pendingCount > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span className="text-xs text-amber-600 font-medium">Needs attention</span>
              </div>
            </div>
          )}
        </div>

        {/* Completed Today */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Completed Today</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{completedToday}</p>
              <p className="text-xs text-gray-500 mt-2">Orders fulfilled</p>
            </div>
            <div className="p-3 rounded-lg bg-green-50">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Revenue */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Total Revenue</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">${(totalRevenue / 100).toFixed(0)}</p>
              <p className="text-xs text-gray-500 mt-2">From completed orders</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        {['all', 'pending', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors capitalize ${
              statusFilter === status
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Orders List */}
      {orderData.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm text-center py-16">
          <div className="w-16 h-16 mx-auto rounded-lg bg-gray-100 flex items-center justify-center mb-4">
            <ShoppingBag className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 font-medium">No orders found</p>
          <p className="text-gray-400 text-sm mt-1">Orders will appear here when customers place them</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orderData.map((order: any) => (
            <div
              key={order.id}
              onClick={() => setSelectedOrder(order)}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {/* Status Icon */}
                  <div className={`p-3 rounded-lg ${
                    order.status === 'completed' ? 'bg-green-50' :
                    order.status === 'pending' ? 'bg-amber-50' :
                    'bg-red-50'
                  }`}>
                    {getStatusIcon(order.status)}
                  </div>

                  {/* Order Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-bold text-gray-900 text-lg">
                        Order #{order.id}
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusBadgeClass(order.status)}`}>
                        {order.status}
                      </span>
                      {order.payment_status && (
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${order.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                          {order.payment_status === 'paid' ? 'Paid' : 'Unpaid'}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
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
                            <span key={idx} className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
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
                              <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-500">
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
                      <div className="mt-3 px-3 py-2 bg-amber-50 rounded-lg border border-amber-200">
                        <p className="text-xs text-amber-700 font-medium">Note: {order.special_instructions}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Price & Actions */}
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold text-gray-900">
                    ${(order.total / 100).toFixed(2)}
                  </p>
                  {order.status === 'pending' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateStatusMutation.mutate({ id: order.id, status: 'completed' })
                        }}
                        className="px-3 py-1.5 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                      >
                        Complete
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateStatusMutation.mutate({ id: order.id, status: 'cancelled' })
                        }}
                        className="px-3 py-1.5 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
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
          {/* Backdrop */}
          <div
            onClick={() => setSelectedOrder(null)}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Modal */}
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="bg-white rounded-xl shadow-xl max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-gray-900">Order #{selectedOrder.id}</h2>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${getStatusBadgeClass(selectedOrder.status)}`}>
                    {selectedOrder.status}
                  </span>
                  {selectedOrder.payment_status && (
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${selectedOrder.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                      {selectedOrder.payment_status === 'paid' ? 'Paid' : 'Unpaid'}
                    </span>
                  )}
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
                {/* Customer Information */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    Customer Information
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-3">
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

                {/* Delivery/Pickup */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    Delivery Information
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    {selectedOrder.delivery_address === 'Pickup' ? (
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-purple-100">
                          <Package className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Pickup Order</p>
                          <p className="text-sm text-gray-500">Customer will pick up at restaurant</p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-orange-100">
                          <MapPin className="w-5 h-5 text-orange-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Delivery Order</p>
                          <p className="text-sm text-gray-500">{selectedOrder.delivery_address}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Payment */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-blue-600" />
                    Payment
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Subtotal</span>
                      <span className="text-gray-900">${(selectedOrder.subtotal / 100).toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Tax</span>
                      <span className="text-gray-900">${(selectedOrder.tax / 100).toFixed(2)}</span>
                    </div>
                    {selectedOrder.delivery_fee > 0 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Delivery Fee</span>
                        <span className="text-gray-900">${(selectedOrder.delivery_fee / 100).toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                      <span className="font-bold text-gray-900">Total</span>
                      <span className="text-2xl font-bold text-blue-600">${(selectedOrder.total / 100).toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Special Instructions */}
                {selectedOrder.special_instructions && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-gray-900">Special Instructions</h3>
                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                      <p className="text-amber-700 text-sm">{selectedOrder.special_instructions}</p>
                    </div>
                  </div>
                )}

                {/* Actions */}
                {selectedOrder.status === 'pending' && (
                  <div className="flex gap-3 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => {
                        updateStatusMutation.mutate({ id: selectedOrder.id, status: 'completed' })
                        setSelectedOrder(null)
                      }}
                      className="flex-1 py-3 px-4 font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors inline-flex items-center justify-center gap-2"
                    >
                      <CheckCircle className="w-5 h-5" />
                      Mark as Completed
                    </button>
                    <button
                      onClick={() => {
                        updateStatusMutation.mutate({ id: selectedOrder.id, status: 'cancelled' })
                        setSelectedOrder(null)
                      }}
                      className="flex-1 py-3 px-4 font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors inline-flex items-center justify-center gap-2"
                    >
                      <XCircle className="w-5 h-5" />
                      Cancel Order
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
