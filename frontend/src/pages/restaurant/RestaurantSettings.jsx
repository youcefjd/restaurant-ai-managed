/**
 * Restaurant Settings Page
 * Account and business settings
 */

import { useState, useEffect } from 'react';
import Card from '../../components/Card';
import Button from '../../components/Button';

export default function RestaurantSettings() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      setUser(JSON.parse(userStr));
    }
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account and business settings
        </p>
      </div>

      {/* Account Info */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Business Name</label>
              <p className="mt-1 text-sm text-gray-900">{user?.business_name || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Email</label>
              <p className="mt-1 text-sm text-gray-900">{user?.email || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Subscription</label>
              <p className="mt-1 text-sm text-gray-900 capitalize">
                {user?.subscription_status || 'Trial'}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Operating Hours */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Operating Hours</h2>
          <p className="text-sm text-gray-500">
            Configure your operating hours so the AI can inform customers.
          </p>
          <Button variant="secondary" className="mt-4">Edit Hours</Button>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-red-600 mb-4">Danger Zone</h2>
          <p className="text-sm text-gray-500 mb-4">
            Permanently delete your account and all associated data.
          </p>
          <Button variant="danger">Delete Account</Button>
        </div>
      </Card>
    </div>
  );
}
