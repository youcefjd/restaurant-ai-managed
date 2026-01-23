import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import { Phone, Save, AlertCircle, CheckCircle, Info, ExternalLink, Loader2, Trash2 } from 'lucide-react'

interface PhoneSettingsProps {
  accountId: number
  currentPhone: string | null
}

export default function PhoneSettings({ accountId, currentPhone }: PhoneSettingsProps) {
  const queryClient = useQueryClient()
  const [phoneNumber, setPhoneNumber] = useState(currentPhone || '')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const updatePhoneMutation = useMutation({
    mutationFn: (phone: string) => restaurantAPI.updateTwilioPhone(accountId, phone),
    onSuccess: () => {
      setSuccess('Phone number updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update phone number')
      setSuccess('')
    },
  })

  const removePhoneMutation = useMutation({
    mutationFn: () => restaurantAPI.removeTwilioPhone(accountId),
    onSuccess: () => {
      setSuccess('Phone number removed successfully!')
      setError('')
      setPhoneNumber('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to remove phone number')
      setSuccess('')
    },
  })

  const handleRemovePhone = () => {
    if (window.confirm('Are you sure you want to remove the phone number? Voice AI will be disabled until you set a new number.')) {
      removePhoneMutation.mutate()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!phoneNumber.trim()) {
      setError('Phone number is required')
      return
    }
    if (!phoneNumber.startsWith('+')) {
      setError('Phone number must be in E.164 format (e.g., +15551234567)')
      return
    }
    const digitsOnly = phoneNumber.replace(/[^\d]/g, '')
    if (digitsOnly.length < 10) {
      setError('Phone number must contain at least 10 digits')
      return
    }

    updatePhoneMutation.mutate(phoneNumber.trim())
  }

  return (
    <div className="card">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 rounded-lg bg-white/5">
          <Phone className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold mb-1">Voice AI Phone Number</h2>
          <p className="text-sm text-dim">
            Configure the Twilio phone number that customers will call.
          </p>
        </div>
      </div>

      {/* Info Box */}
      <div className="p-4 mb-6 rounded-lg bg-accent/10 border border-accent/20">
        <div className="flex items-start gap-3">
          <Info className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium mb-2">How to get a Twilio phone number:</p>
            <ol className="text-sm text-dim space-y-1 list-decimal list-inside">
              <li>Sign up at{' '}
                <a href="https://www.twilio.com/try-twilio" target="_blank" rel="noopener noreferrer"
                   className="text-accent hover:underline inline-flex items-center gap-1">
                  twilio.com <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>Buy a phone number (starts at $1/month)</li>
              <li>Configure webhooks:
                <ul className="list-disc list-inside ml-4 mt-1 space-y-0.5">
                  <li>Voice: <code className="px-1 rounded bg-white/5">https://your-domain.com/api/voice/welcome</code></li>
                  <li>SMS: <code className="px-1 rounded bg-white/5">https://your-domain.com/api/voice/sms/incoming</code></li>
                </ul>
              </li>
              <li>Enter your phone number below (E.164 format: +15551234567)</li>
            </ol>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="phone" className="block text-sm font-medium mb-2">
            Twilio Phone Number
          </label>
          <div className="flex gap-3">
            <div className="flex-1">
              <input
                type="text"
                id="phone"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+15551234567"
                disabled={updatePhoneMutation.isPending}
              />
              <p className="text-xs text-dim mt-2">
                Format: +[country code][number] (e.g., +15551234567 for US)
              </p>
            </div>
            <button
              type="submit"
              disabled={updatePhoneMutation.isPending || !phoneNumber.trim()}
              className="btn btn-primary flex items-center gap-2"
            >
              {updatePhoneMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save
                </>
              )}
            </button>
          </div>
        </div>

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

        {currentPhone && (
          <div className="p-4 rounded-lg bg-white/5 border border-[--border]">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">Current Phone Number:</p>
                <p className="text-lg font-mono">{currentPhone}</p>
                <p className="text-xs text-dim mt-2">
                  Customers call this number to reach your AI assistant
                </p>
              </div>
              <button
                type="button"
                onClick={handleRemovePhone}
                disabled={removePhoneMutation.isPending}
                className="btn btn-danger btn-sm flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                {removePhoneMutation.isPending ? 'Removing...' : 'Remove'}
              </button>
            </div>
          </div>
        )}

        {!currentPhone && (
          <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
            <p className="text-sm text-warning">
              <strong>No phone number configured.</strong> Voice AI will not work until you set a Twilio phone number.
            </p>
          </div>
        )}
      </form>
    </div>
  )
}
