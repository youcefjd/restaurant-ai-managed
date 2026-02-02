import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import {
  Store,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle,
  TestTube,
  Eye,
  EyeOff,
  Link as LinkIcon,
  Unlink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

interface ToastSettingsProps {
  accountId: number
  toastEnabled: boolean | null
  toastClientId: string | null
  toastRestaurantGuid: string | null
}

interface MenuItem {
  id: number
  name: string
  toast_item_guid: string | null
}

export default function ToastSettings({
  accountId,
  toastEnabled,
  toastClientId,
  toastRestaurantGuid,
}: ToastSettingsProps) {
  const queryClient = useQueryClient()
  const [enabled, setEnabled] = useState(toastEnabled ?? false)
  const [clientId, setClientId] = useState(toastClientId ?? '')
  const [clientSecret, setClientSecret] = useState('')
  const [restaurantGuid, setRestaurantGuid] = useState(toastRestaurantGuid ?? '')
  const [showSecret, setShowSecret] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle')
  const [showMappings, setShowMappings] = useState(false)
  const [itemMappings, setItemMappings] = useState<Record<number, string>>({})

  // Fetch menu items for mapping
  const { data: menuData } = useQuery({
    queryKey: ['menus', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId),
    enabled: !!accountId && showMappings,
    select: (response) => response.data,
  })

  // Flatten menu items from categories
  const menuItems: MenuItem[] = []
  if (menuData?.menus) {
    for (const menu of menuData.menus) {
      for (const category of menu.categories || []) {
        for (const item of category.items || []) {
          menuItems.push({
            id: item.id,
            name: item.name,
            toast_item_guid: item.toast_item_guid || null,
          })
        }
      }
    }
  }

  useEffect(() => {
    if (toastEnabled !== null) setEnabled(toastEnabled)
    if (toastClientId) setClientId(toastClientId)
    if (toastRestaurantGuid) setRestaurantGuid(toastRestaurantGuid)
  }, [toastEnabled, toastClientId, toastRestaurantGuid])

  // Initialize item mappings from menu data
  useEffect(() => {
    if (menuItems.length > 0) {
      const mappings: Record<number, string> = {}
      for (const item of menuItems) {
        if (item.toast_item_guid) {
          mappings[item.id] = item.toast_item_guid
        }
      }
      setItemMappings(mappings)
    }
  }, [menuData])

  const updateToastMutation = useMutation({
    mutationFn: (data: {
      toast_enabled: boolean
      toast_client_id?: string
      toast_client_secret?: string
      toast_restaurant_guid?: string
    }) => restaurantAPI.updateToastConfig(accountId, data),
    onSuccess: () => {
      setSuccess('Toast settings updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update Toast settings')
      setSuccess('')
    },
  })

  const testConnectionMutation = useMutation({
    mutationFn: () => restaurantAPI.testToastConnection(accountId),
    onSuccess: () => {
      setTestStatus('success')
      setTimeout(() => setTestStatus('idle'), 5000)
    },
    onError: () => {
      setTestStatus('failed')
      setTimeout(() => setTestStatus('idle'), 5000)
    },
  })

  const updateItemMappingMutation = useMutation({
    mutationFn: ({ itemId, toastGuid }: { itemId: number; toastGuid: string }) =>
      restaurantAPI.updateMenuItem(itemId, { toast_item_guid: toastGuid || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menus', accountId] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (enabled && (!clientId || !restaurantGuid)) {
      setError('Client ID and Restaurant GUID are required when Toast is enabled')
      return
    }

    const data: any = {
      toast_enabled: enabled,
    }

    if (enabled) {
      data.toast_client_id = clientId
      data.toast_restaurant_guid = restaurantGuid
      if (clientSecret) {
        data.toast_client_secret = clientSecret
      }
    }

    updateToastMutation.mutate(data)
  }

  const handleTestConnection = () => {
    setTestStatus('testing')
    testConnectionMutation.mutate()
  }

  const handleMappingChange = (itemId: number, toastGuid: string) => {
    setItemMappings((prev) => ({
      ...prev,
      [itemId]: toastGuid,
    }))
  }

  const handleSaveMapping = (itemId: number) => {
    const toastGuid = itemMappings[itemId] || ''
    updateItemMappingMutation.mutate({ itemId, toastGuid })
  }

  return (
    <div className="card">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 rounded-lg bg-white/5">
          <Store className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold mb-1">Toast POS Integration</h2>
          <p className="text-sm text-dim">
            Connect to Toast POS for kitchen display sync and payment processing.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-[--border]">
          <div className="flex items-center gap-3">
            {enabled ? (
              <LinkIcon className="w-5 h-5 text-success" />
            ) : (
              <Unlink className="w-5 h-5 text-dim" />
            )}
            <div>
              <p className="font-medium">Toast Integration</p>
              <p className="text-sm text-dim">
                {enabled ? 'Connected - orders will sync to Toast' : 'Disabled'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setEnabled(!enabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              enabled ? 'bg-success' : 'bg-[--border]'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {enabled && (
          <>
            {/* API Credentials */}
            <div className="space-y-4">
              <div>
                <label htmlFor="toast-client-id" className="block text-sm font-medium mb-2">
                  Toast Client ID
                </label>
                <input
                  type="text"
                  id="toast-client-id"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  disabled={updateToastMutation.isPending}
                  placeholder="Enter your Toast client ID"
                  className="w-full"
                />
              </div>

              <div>
                <label htmlFor="toast-client-secret" className="block text-sm font-medium mb-2">
                  Toast Client Secret
                </label>
                <div className="relative">
                  <input
                    type={showSecret ? 'text' : 'password'}
                    id="toast-client-secret"
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    disabled={updateToastMutation.isPending}
                    placeholder={toastClientId ? '••••••••' : 'Enter your Toast client secret'}
                    className="w-full pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-dim hover:text-white"
                  >
                    {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-dim mt-1">
                  Leave blank to keep existing secret
                </p>
              </div>

              <div>
                <label htmlFor="toast-restaurant-guid" className="block text-sm font-medium mb-2">
                  Toast Restaurant GUID
                </label>
                <input
                  type="text"
                  id="toast-restaurant-guid"
                  value={restaurantGuid}
                  onChange={(e) => setRestaurantGuid(e.target.value)}
                  disabled={updateToastMutation.isPending}
                  placeholder="Enter your Toast restaurant GUID"
                  className="w-full"
                />
                <p className="text-xs text-dim mt-1">
                  Found in your Toast dashboard under restaurant settings
                </p>
              </div>
            </div>

            {/* Test Connection */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testConnectionMutation.isPending || !clientId || !restaurantGuid}
                className="btn btn-secondary flex items-center gap-2"
              >
                {testConnectionMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="w-4 h-4" />
                    Test Connection
                  </>
                )}
              </button>
              {testStatus === 'success' && (
                <span className="text-sm text-success flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" />
                  Connection successful
                </span>
              )}
              {testStatus === 'failed' && (
                <span className="text-sm text-danger flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  Connection failed
                </span>
              )}
            </div>
          </>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-danger/10 border border-danger/20 flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 rounded-lg bg-success/10 border border-success/20 flex items-start gap-3">
            <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
            <p className="text-sm text-success">{success}</p>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateToastMutation.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            {updateToastMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Settings
              </>
            )}
          </button>
        </div>
      </form>

      {/* Menu Item Mappings Section */}
      {enabled && (
        <div className="mt-6 border-t border-[--border] pt-6">
          <button
            type="button"
            onClick={() => setShowMappings(!showMappings)}
            className="flex items-center justify-between w-full text-left"
          >
            <div>
              <h3 className="font-medium">Menu Item Mappings</h3>
              <p className="text-sm text-dim">Map your menu items to Toast item GUIDs</p>
            </div>
            {showMappings ? (
              <ChevronUp className="w-5 h-5 text-dim" />
            ) : (
              <ChevronDown className="w-5 h-5 text-dim" />
            )}
          </button>

          {showMappings && (
            <div className="mt-4 space-y-3">
              {menuItems.length === 0 ? (
                <p className="text-sm text-dim">No menu items found. Add items to your menu first.</p>
              ) : (
                menuItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-white/5"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{item.name}</p>
                    </div>
                    <input
                      type="text"
                      value={itemMappings[item.id] || ''}
                      onChange={(e) => handleMappingChange(item.id, e.target.value)}
                      placeholder="Toast GUID"
                      className="w-48 text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => handleSaveMapping(item.id)}
                      disabled={updateItemMappingMutation.isPending}
                      className="btn btn-secondary btn-sm"
                    >
                      Save
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Current Status */}
      {toastEnabled && (
        <div className="mt-6 p-4 rounded-lg bg-white/5 border border-[--border]">
          <p className="text-sm font-medium mb-2">Current Configuration:</p>
          <div className="space-y-1 text-sm">
            <p>
              <span className="text-dim">Status:</span>{' '}
              <span className="text-success">Connected</span>
            </p>
            {toastRestaurantGuid && (
              <p>
                <span className="text-dim">Restaurant GUID:</span>{' '}
                <span className="font-mono text-xs">{toastRestaurantGuid}</span>
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
