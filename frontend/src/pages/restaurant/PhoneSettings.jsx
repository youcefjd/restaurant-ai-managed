/**
 * Phone & AI Settings Page
 * Configure the AI phone assistant and manage the Twilio phone number
 */

import { useState, useEffect } from 'react';
import {
  PhoneIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { useAppContext } from '../../App';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function formatPhoneDisplay(phone) {
  if (!phone) return '';
  // Format +15551234567 as +1 (555) 123-4567
  if (phone.startsWith('+1') && phone.length === 12) {
    return `+1 (${phone.slice(2, 5)}) ${phone.slice(5, 8)}-${phone.slice(8)}`;
  }
  return phone;
}

export default function PhoneSettings() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState(null);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);

  const appContext = useAppContext();
  const showNotification = appContext?.showNotification || ((msg, type) => console.log(type, msg));

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const userData = JSON.parse(userStr);
      setUser(userData);
      if (userData.twilio_phone_number) {
        setPhoneNumber(userData.twilio_phone_number);
      }
    }
  }, []);

  const refreshUserData = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/onboarding/accounts/${user.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const accountData = await response.json();
        // Update local storage with new phone number
        const updatedUser = { ...user, twilio_phone_number: accountData.twilio_phone_number };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
        setPhoneNumber(accountData.twilio_phone_number || '');
      }
    } catch (err) {
      console.error('Failed to refresh user data:', err);
    }
  };

  const handleSavePhone = async () => {
    if (!phoneNumber.trim()) {
      setError('Please enter a phone number');
      return;
    }

    // Basic validation - should start with +
    let formattedPhone = phoneNumber.trim();
    if (!formattedPhone.startsWith('+')) {
      // Assume US number if no country code
      formattedPhone = '+1' + formattedPhone.replace(/\D/g, '');
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/onboarding/accounts/${user.id}/twilio-phone`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ twilio_phone_number: formattedPhone }),
      });

      if (response.ok) {
        showNotification('AI phone number updated successfully', 'success');
        setIsEditing(false);
        await refreshUserData();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update phone number');
      }
    } catch (err) {
      console.error('Save error:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleRemovePhone = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/onboarding/accounts/${user.id}/twilio-phone`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showNotification('AI phone number removed', 'success');
        setShowRemoveConfirm(false);
        setPhoneNumber('');
        await refreshUserData();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to remove phone number');
      }
    } catch (err) {
      console.error('Remove error:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setPhoneNumber(user?.twilio_phone_number || '');
    setError(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Phone & AI Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Configure your AI phone assistant
        </p>
      </div>

      {/* AI Phone Number */}
      <Card>
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">AI Phone Number</h2>
              <p className="text-sm text-gray-500 mt-1">
                This is the phone number customers call to place orders via AI
              </p>
            </div>
            {user?.twilio_phone_number && !isEditing && (
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Edit phone number"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setShowRemoveConfirm(true)}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Remove phone number"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            )}
          </div>

          {isEditing || !user?.twilio_phone_number ? (
            // Edit/Add Mode
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number
                </label>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => {
                      setPhoneNumber(e.target.value);
                      setError(null);
                    }}
                    placeholder="+1 (555) 123-4567"
                    className="flex-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Enter in E.164 format (e.g., +15551234567) or we'll format it for you
                </p>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600 flex items-start gap-2">
                  <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex gap-3">
                {user?.twilio_phone_number && (
                  <Button variant="secondary" onClick={cancelEdit} disabled={loading}>
                    Cancel
                  </Button>
                )}
                <Button onClick={handleSavePhone} disabled={loading}>
                  {loading ? 'Saving...' : 'Save Phone Number'}
                </Button>
              </div>
            </div>
          ) : (
            // Display Mode
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-green-100">
                <PhoneIcon className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {formatPhoneDisplay(user.twilio_phone_number)}
                </p>
                <div className="flex items-center gap-2 text-sm text-green-600 mt-1">
                  <CheckCircleIcon className="h-4 w-4" />
                  <span>Active and receiving calls</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Setup Instructions */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Setup Instructions</h2>

          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium">
                1
              </div>
              <div>
                <p className="font-medium text-gray-900">Get a Twilio Phone Number</p>
                <p className="text-sm text-gray-500">
                  Purchase a phone number from{' '}
                  <a href="https://www.twilio.com/console/phone-numbers" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline">
                    Twilio Console
                  </a>
                  . Choose a local or toll-free number.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium">
                2
              </div>
              <div>
                <p className="font-medium text-gray-900">Configure Voice Webhook</p>
                <p className="text-sm text-gray-500">
                  In Twilio, set the Voice webhook URL to:
                </p>
                <code className="mt-1 block text-xs bg-gray-100 px-2 py-1 rounded text-gray-800">
                  {API_BASE}/api/voice/incoming
                </code>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium">
                3
              </div>
              <div>
                <p className="font-medium text-gray-900">Enter Your Number Above</p>
                <p className="text-sm text-gray-500">
                  Once configured in Twilio, enter the phone number here to link it to your restaurant.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium">
                4
              </div>
              <div>
                <p className="font-medium text-gray-900">Test Your Setup</p>
                <p className="text-sm text-gray-500">
                  Call your AI phone number to test the voice assistant. Make sure your menu is imported first.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Info Box */}
      <Card>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex gap-3">
            <InformationCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">Auto-Provisioning Coming Soon</p>
              <p className="text-sm text-blue-700 mt-1">
                In a future update, phone numbers will be automatically provisioned when you sign up.
                For now, please follow the manual setup instructions above.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* AI Settings Placeholder */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Assistant Settings</h2>
          <p className="text-sm text-gray-500">
            Additional AI configuration options coming soon:
          </p>
          <ul className="mt-2 text-sm text-gray-500 list-disc list-inside space-y-1">
            <li>Custom greeting message</li>
            <li>Voice selection</li>
            <li>Language settings</li>
            <li>Order confirmation preferences</li>
          </ul>
        </div>
      </Card>

      {/* Remove Confirmation Modal */}
      {showRemoveConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowRemoveConfirm(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Remove Phone Number</h3>
                <button onClick={() => setShowRemoveConfirm(false)} className="text-gray-400 hover:text-gray-500">
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              <p className="text-gray-500 mb-4">
                Are you sure you want to remove your AI phone number? Customers will no longer be able to call in to place orders.
              </p>
              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => setShowRemoveConfirm(false)} className="flex-1">
                  Cancel
                </Button>
                <Button variant="danger" onClick={handleRemovePhone} disabled={loading} className="flex-1">
                  {loading ? 'Removing...' : 'Remove'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
