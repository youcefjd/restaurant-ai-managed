/**
 * Restaurant Orders Page
 * Full order history with search, filtering, and pagination
 */

import { useState, useEffect } from 'react';
import {
  CalendarDaysIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ShoppingBagIcon,
  TruckIcon,
  ClockIcon,
  XMarkIcon,
  CurrencyDollarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { useAppContext } from '../../App';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Status configurations
const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  preparing: 'bg-orange-100 text-orange-800',
  ready: 'bg-green-100 text-green-800',
  out_for_delivery: 'bg-purple-100 text-purple-800',
  picked_up: 'bg-gray-100 text-gray-800',
  delivered: 'bg-gray-100 text-gray-800',
  completed: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-red-100 text-red-800',
};

const paymentStatusColors = {
  unpaid: 'bg-red-100 text-red-800',
  pending: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  refunded: 'bg-gray-100 text-gray-800',
  failed: 'bg-red-100 text-red-800',
};

const orderStatuses = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'preparing', label: 'Preparing' },
  { value: 'ready', label: 'Ready' },
  { value: 'out_for_delivery', label: 'Out for Delivery' },
  { value: 'picked_up', label: 'Picked Up' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const paymentStatuses = [
  { value: '', label: 'All Payment Status' },
  { value: 'unpaid', label: 'Unpaid' },
  { value: 'pending', label: 'Pending' },
  { value: 'paid', label: 'Paid' },
  { value: 'refunded', label: 'Refunded' },
];

const orderTypes = [
  { value: '', label: 'All Types' },
  { value: 'takeout', label: 'Takeout' },
  { value: 'delivery', label: 'Delivery' },
];

function formatDateTime(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatCurrency(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

// Order Details Modal (reused from dashboard)
function OrderDetailsModal({ order, onClose, onStatusUpdate, onPaymentUpdate }) {
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (newStatus) => {
    setUpdating(true);
    await onStatusUpdate(order.id, newStatus);
    setUpdating(false);
  };

  const handlePaymentChange = async (newStatus) => {
    setUpdating(true);
    await onPaymentUpdate(order.id, newStatus);
    setUpdating(false);
  };

  const getNextStatuses = () => {
    switch (order.status) {
      case 'pending':
        return ['confirmed', 'cancelled'];
      case 'confirmed':
        return ['preparing', 'cancelled'];
      case 'preparing':
        return ['ready', 'cancelled'];
      case 'ready':
        return order.order_type === 'takeout' ? ['picked_up', 'cancelled'] : ['out_for_delivery', 'cancelled'];
      case 'out_for_delivery':
        return ['delivered', 'cancelled'];
      case 'picked_up':
      case 'delivered':
        return ['completed'];
      default:
        return [];
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex justify-between items-start">
              <h3 className="text-lg font-medium text-gray-900" id="modal-title">
                Order #{order.id}
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              {/* Order Type & Status */}
              <div className="flex items-center gap-2">
                {order.order_type === 'takeout' ? (
                  <ShoppingBagIcon className="h-5 w-5 text-gray-500" />
                ) : (
                  <TruckIcon className="h-5 w-5 text-gray-500" />
                )}
                <span className="font-medium capitalize">{order.order_type}</span>
                <span className={`px-2 py-1 text-xs rounded-full ${statusColors[order.status]}`}>
                  {order.status.replace('_', ' ')}
                </span>
                <span className={`px-2 py-1 text-xs rounded-full ${paymentStatusColors[order.payment_status]}`}>
                  {order.payment_status}
                </span>
              </div>

              {/* Customer Info */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-500">Customer</h4>
                <p className="text-gray-900">{order.customer_name || 'N/A'}</p>
                <p className="text-sm text-gray-500">{order.customer_phone || 'No phone'}</p>
                {order.customer_email && (
                  <p className="text-sm text-gray-500">{order.customer_email}</p>
                )}
              </div>

              {/* Scheduled Time */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-500">
                  {order.order_type === 'takeout' ? 'Pickup Time' : 'Delivery Time'}
                </h4>
                <p className="text-gray-900 font-medium">
                  {order.scheduled_time ? new Date(order.scheduled_time).toLocaleString() : 'ASAP'}
                </p>
              </div>

              {/* Delivery Address (if delivery) */}
              {order.order_type === 'delivery' && order.delivery_address && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-500">Delivery Address</h4>
                  <p className="text-gray-900">{order.delivery_address}</p>
                </div>
              )}

              {/* Order Items */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Items</h4>
                <ul className="space-y-2">
                  {order.order_items?.map((item, index) => (
                    <li key={index} className="flex justify-between text-sm">
                      <span>
                        {item.quantity}x {item.item_name || item.name}
                        {item.modifiers?.length > 0 && (
                          <span className="text-gray-500 ml-1">
                            ({item.modifiers.join(', ')})
                          </span>
                        )}
                      </span>
                      <span>{formatCurrency(item.price_cents * item.quantity)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Special Instructions */}
              {order.special_instructions && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-500">Special Instructions</h4>
                  <p className="text-gray-900 text-sm">{order.special_instructions}</p>
                </div>
              )}

              {/* Totals */}
              <div className="border-t pt-4 space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Subtotal</span>
                  <span>{formatCurrency(order.subtotal)}</span>
                </div>
                {order.tax > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Tax</span>
                    <span>{formatCurrency(order.tax)}</span>
                  </div>
                )}
                {order.delivery_fee > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Delivery Fee</span>
                    <span>{formatCurrency(order.delivery_fee)}</span>
                  </div>
                )}
                <div className="flex justify-between font-medium pt-2 border-t">
                  <span>Total</span>
                  <span>{formatCurrency(order.total)}</span>
                </div>
              </div>

              {/* Order Date */}
              <div className="border-t pt-4 text-sm text-gray-500">
                <p>Ordered: {formatDateTime(order.created_at)}</p>
                <p>Last Updated: {formatDateTime(order.updated_at)}</p>
              </div>

              {/* Actions */}
              <div className="border-t pt-4 space-y-3">
                {/* Status Update */}
                {getNextStatuses().length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 mb-2">Update Status</h4>
                    <div className="flex flex-wrap gap-2">
                      {getNextStatuses().map((status) => (
                        <Button
                          key={status}
                          size="sm"
                          variant={status === 'cancelled' ? 'danger' : 'primary'}
                          onClick={() => handleStatusChange(status)}
                          disabled={updating}
                        >
                          {status.replace('_', ' ')}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Payment Update */}
                {order.payment_status === 'unpaid' && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 mb-2">Mark as Paid</h4>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handlePaymentChange('paid')}
                        disabled={updating}
                      >
                        <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                        Mark Paid
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RestaurantBookings() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [error, setError] = useState(null);

  const appContext = useAppContext();
  const showNotification = appContext?.showNotification || ((msg, type) => console.log(type, msg));

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter, paymentFilter, typeFilter, dateFrom, dateTo]);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('authToken');
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);
      if (paymentFilter) params.append('payment_status', paymentFilter);
      if (typeFilter) params.append('order_type', typeFilter);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await fetch(`${API_BASE}/api/restaurant/orders?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
        setTotal(data.total || 0);
      } else {
        console.error('Failed to fetch orders:', response.status);
        setError(`Failed to load orders (${response.status})`);
      }
    } catch (err) {
      console.error('Failed to fetch orders:', err);
      setError('Failed to connect to server');
      showNotification('Failed to load orders', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchOrders();
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/restaurant/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        const updatedOrder = await response.json();
        setOrders(orders.map(o => o.id === orderId ? updatedOrder : o));
        setSelectedOrder(updatedOrder);
        showNotification(`Order #${orderId} updated to ${newStatus}`, 'success');
      } else {
        showNotification('Failed to update order status', 'error');
      }
    } catch (error) {
      console.error('Failed to update order:', error);
      showNotification('Failed to update order status', 'error');
    }
  };

  const updatePaymentStatus = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/restaurant/orders/${orderId}/payment`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ payment_status: newStatus }),
      });

      if (response.ok) {
        const updatedOrder = await response.json();
        setOrders(orders.map(o => o.id === orderId ? updatedOrder : o));
        setSelectedOrder(updatedOrder);
        showNotification(`Order #${orderId} marked as ${newStatus}`, 'success');
      } else {
        showNotification('Failed to update payment status', 'error');
      }
    } catch (error) {
      console.error('Failed to update payment:', error);
      showNotification('Failed to update payment status', 'error');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <p className="mt-1 text-sm text-gray-500">
          View and manage all orders
        </p>
      </div>

      {/* Search and Filters */}
      <Card>
        <div className="p-4">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by customer name or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <Button type="submit">Search</Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowFilters(!showFilters)}
            >
              <FunnelIcon className="h-5 w-5" />
            </Button>
          </form>

          {/* Expanded Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Order Type</label>
                <select
                  value={typeFilter}
                  onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {orderTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {orderStatuses.map(status => (
                    <option key={status.value} value={status.value}>{status.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment</label>
                <select
                  value={paymentFilter}
                  onChange={(e) => { setPaymentFilter(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {paymentStatuses.map(status => (
                    <option key={status.value} value={status.value}>{status.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Orders Table */}
      <Card>
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading orders...</div>
        ) : error ? (
          <div className="p-8 text-center">
            <CalendarDaysIcon className="h-12 w-12 text-red-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Error Loading Orders</h3>
            <p className="mt-1 text-sm text-red-500">{error}</p>
            <Button onClick={fetchOrders} className="mt-4" variant="secondary">
              Try Again
            </Button>
          </div>
        ) : orders.length === 0 ? (
          <div className="p-8 text-center">
            <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Orders Found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {search || statusFilter || paymentFilter || typeFilter || dateFrom || dateTo
                ? 'Try adjusting your filters.'
                : 'Orders placed through your AI phone will appear here.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.map((order) => (
                  <tr
                    key={order.id}
                    onClick={() => setSelectedOrder(order)}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">#{order.id}</div>
                      <div className="text-xs text-gray-500">{formatDateTime(order.created_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{order.customer_name || 'N/A'}</div>
                      <div className="text-xs text-gray-500">{order.customer_phone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        {order.order_type === 'takeout' ? (
                          <ShoppingBagIcon className="h-4 w-4" />
                        ) : (
                          <TruckIcon className="h-4 w-4" />
                        )}
                        <span className="capitalize">{order.order_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <ClockIcon className="h-4 w-4" />
                        <span>{order.scheduled_time ? formatDateTime(order.scheduled_time) : 'ASAP'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[order.status]}`}>
                        {order.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${paymentStatusColors[order.payment_status]}`}>
                        {order.payment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(order.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} orders
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </Button>
              <span className="px-3 py-1 text-sm text-gray-700">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                <ChevronRightIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Order Details Modal */}
      {selectedOrder && (
        <OrderDetailsModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onStatusUpdate={updateOrderStatus}
          onPaymentUpdate={updatePaymentStatus}
        />
      )}
    </div>
  );
}
