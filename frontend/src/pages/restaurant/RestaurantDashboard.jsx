/**
 * Restaurant Dashboard
 * Main dashboard for restaurant users showing active orders and quick actions
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  PhoneIcon,
  DocumentTextIcon,
  CalendarDaysIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShoppingBagIcon,
  TruckIcon,
  XMarkIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { useAppContext } from '../../App';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Order status badge colors
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

function formatTime(dateString) {
  if (!dateString) return 'ASAP';
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function formatCurrency(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

// Order Details Modal
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

// Order Card Component
function OrderCard({ order, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          {order.order_type === 'takeout' ? (
            <ShoppingBagIcon className="h-5 w-5 text-blue-500" />
          ) : (
            <TruckIcon className="h-5 w-5 text-purple-500" />
          )}
          <span className="font-medium">#{order.id}</span>
        </div>
        <div className="flex gap-1">
          <span className={`px-2 py-0.5 text-xs rounded-full ${statusColors[order.status]}`}>
            {order.status.replace('_', ' ')}
          </span>
          <span className={`px-2 py-0.5 text-xs rounded-full ${paymentStatusColors[order.payment_status]}`}>
            {order.payment_status}
          </span>
        </div>
      </div>

      <div className="text-sm text-gray-600 mb-2">
        {order.customer_name || 'Customer'}
        {order.customer_phone && ` - ${order.customer_phone}`}
      </div>

      <div className="flex justify-between items-center text-sm">
        <div className="flex items-center gap-1 text-gray-500">
          <ClockIcon className="h-4 w-4" />
          <span>{formatTime(order.scheduled_time)}</span>
        </div>
        <span className="font-medium">{formatCurrency(order.total)}</span>
      </div>

      <div className="mt-2 text-xs text-gray-500">
        {order.order_items?.length || 0} item{(order.order_items?.length || 0) !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

export default function RestaurantDashboard() {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  const appContext = useAppContext();
  const showNotification = appContext?.showNotification || ((msg, type) => console.log(type, msg));

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      setUser(JSON.parse(userStr));
    }
  }, []);

  // Fetch active orders
  useEffect(() => {
    fetchOrders();
    // Poll for new orders every 30 seconds
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/restaurant/orders/active`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(Array.isArray(data) ? data : []);
      } else {
        console.error('Failed to fetch orders:', response.status);
        setOrders([]);
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      setOrders([]);
    } finally {
      setLoading(false);
    }
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
        setOrders(orders.map(o => o.id === orderId ? updatedOrder : o).filter(o =>
          !['completed', 'cancelled', 'picked_up', 'delivered'].includes(o.status)
        ));
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

  // Calculate trial status
  const getTrialInfo = () => {
    if (!user?.trial_ends_at) return null;
    const trialEnd = new Date(user.trial_ends_at);
    const now = new Date();
    const daysLeft = Math.ceil((trialEnd - now) / (1000 * 60 * 60 * 24));
    const ordersLeft = (user.trial_order_limit || 10) - (user.trial_orders_used || 0);
    const isExpired = daysLeft <= 0 || ordersLeft <= 0;
    return { daysLeft: Math.max(0, daysLeft), ordersLeft: Math.max(0, ordersLeft), isExpired };
  };

  const trialInfo = getTrialInfo();

  // Group orders by status
  const pendingOrders = orders.filter(o => o.status === 'pending');
  const preparingOrders = orders.filter(o => ['confirmed', 'preparing'].includes(o.status));
  const readyOrders = orders.filter(o => ['ready', 'out_for_delivery'].includes(o.status));

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user?.business_name || 'Restaurant'}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your orders and AI phone assistant
          </p>
        </div>
        <Link to="/restaurant/bookings">
          <Button variant="secondary" size="sm">View All Orders</Button>
        </Link>
      </div>

      {/* Trial Status Banner */}
      {trialInfo && !trialInfo.isExpired && (
        <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
          <div className="flex items-start">
            <ClockIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Trial Period Active</h3>
              <p className="mt-1 text-sm text-yellow-700">
                You have <strong>{trialInfo.daysLeft} days</strong> and{' '}
                <strong>{trialInfo.ordersLeft} orders</strong> remaining in your trial.
              </p>
            </div>
          </div>
        </div>
      )}

      {trialInfo?.isExpired && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Trial Expired</h3>
              <p className="mt-1 text-sm text-red-700">
                Your trial has ended. Upgrade to continue using the AI phone service.
              </p>
              <Button className="mt-2" size="sm">
                Upgrade Now
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Active Orders Section */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Active Orders</h2>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading orders...</div>
        ) : orders.length === 0 ? (
          <Card>
            <div className="p-8 text-center">
              <ShoppingBagIcon className="h-12 w-12 text-gray-400 mx-auto" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Active Orders</h3>
              <p className="mt-1 text-sm text-gray-500">
                Orders placed through your AI phone will appear here.
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Pending Column */}
            <div>
              <h3 className="text-sm font-medium text-yellow-700 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                New ({pendingOrders.length})
              </h3>
              <div className="space-y-3">
                {pendingOrders.map(order => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onClick={() => setSelectedOrder(order)}
                  />
                ))}
                {pendingOrders.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No pending orders</p>
                )}
              </div>
            </div>

            {/* Preparing Column */}
            <div>
              <h3 className="text-sm font-medium text-orange-700 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                Preparing ({preparingOrders.length})
              </h3>
              <div className="space-y-3">
                {preparingOrders.map(order => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onClick={() => setSelectedOrder(order)}
                  />
                ))}
                {preparingOrders.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No orders preparing</p>
                )}
              </div>
            </div>

            {/* Ready Column */}
            <div>
              <h3 className="text-sm font-medium text-green-700 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Ready ({readyOrders.length})
              </h3>
              <div className="space-y-3">
                {readyOrders.map(order => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onClick={() => setSelectedOrder(order)}
                  />
                ))}
                {readyOrders.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No orders ready</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link to="/restaurant/menu">
            <Card className="hover:shadow-md transition-shadow h-full">
              <div className="p-5 flex items-center">
                <DocumentTextIcon className="h-10 w-10 text-indigo-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Setup Menu</p>
                  <p className="text-xs text-gray-500">Add your menu items</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/restaurant/bookings">
            <Card className="hover:shadow-md transition-shadow h-full">
              <div className="p-5 flex items-center">
                <CalendarDaysIcon className="h-10 w-10 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">View All Orders</p>
                  <p className="text-xs text-gray-500">Order history & search</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/restaurant/phone">
            <Card className="hover:shadow-md transition-shadow h-full">
              <div className="p-5 flex items-center">
                <PhoneIcon className="h-10 w-10 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">Phone Settings</p>
                  <p className="text-xs text-gray-500">Configure AI assistant</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Phone Number Status */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-green-100">
                <PhoneIcon className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Your AI Phone</h2>
                {user?.twilio_phone_number ? (
                  <p className="text-2xl font-bold text-green-600">{user.twilio_phone_number}</p>
                ) : (
                  <p className="text-sm text-gray-500">No phone number assigned yet</p>
                )}
              </div>
            </div>
            <Link to="/restaurant/phone">
              <Button variant="secondary">Configure</Button>
            </Link>
          </div>

          {user?.twilio_phone_number ? (
            <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
              <CheckCircleIcon className="h-5 w-5" />
              <span>AI assistant is active and ready to take calls</span>
            </div>
          ) : (
            <div className="mt-4 text-sm text-gray-500">
              Contact support to get your dedicated AI phone number assigned.
            </div>
          )}
        </div>
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
