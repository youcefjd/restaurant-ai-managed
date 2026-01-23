import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import { Clock, Save, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import GoogleMapsImport from './GoogleMapsImport'

const weekdays = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
]

interface OperatingHoursSettingsProps {
  accountId: number
  currentOpeningTime: string | null
  currentClosingTime: string | null
  currentOperatingDays: number[] | null
}

export default function OperatingHoursSettings({
  accountId,
  currentOpeningTime,
  currentClosingTime,
  currentOperatingDays,
}: OperatingHoursSettingsProps) {
  const queryClient = useQueryClient()
  const [openingTime, setOpeningTime] = useState(currentOpeningTime || '')
  const [closingTime, setClosingTime] = useState(currentClosingTime || '')
  const [operatingDays, setOperatingDays] = useState<number[]>(currentOperatingDays || [])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (currentOpeningTime) setOpeningTime(currentOpeningTime)
    if (currentClosingTime) setClosingTime(currentClosingTime)
    if (currentOperatingDays) setOperatingDays(currentOperatingDays)
  }, [currentOpeningTime, currentClosingTime, currentOperatingDays])

  const updateHoursMutation = useMutation({
    mutationFn: (hours: { opening_time?: string; closing_time?: string; operating_days?: number[] }) =>
      restaurantAPI.updateOperatingHours(accountId, hours),
    onSuccess: () => {
      setSuccess('Operating hours updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update operating hours')
      setSuccess('')
    },
  })

  const handleHoursImported = (hours: { opening_time?: string; closing_time?: string; operating_days?: number[] }) => {
    if (hours.opening_time) setOpeningTime(hours.opening_time)
    if (hours.closing_time) setClosingTime(hours.closing_time)
    if (hours.operating_days) setOperatingDays(hours.operating_days)
    setSuccess('Operating hours imported from Google Maps!')
    setTimeout(() => setSuccess(''), 5000)
  }

  const toggleDay = (day: number) => {
    setOperatingDays(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day].sort()
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/

    if (openingTime && !timeRegex.test(openingTime)) {
      setError('Opening time must be in HH:MM format (e.g., 09:00)')
      return
    }
    if (closingTime && !timeRegex.test(closingTime)) {
      setError('Closing time must be in HH:MM format (e.g., 22:00)')
      return
    }
    if (openingTime && closingTime && openingTime >= closingTime) {
      setError('Opening time must be before closing time')
      return
    }

    updateHoursMutation.mutate({
      opening_time: openingTime || undefined,
      closing_time: closingTime || undefined,
      operating_days: operatingDays.length > 0 ? operatingDays : undefined,
    })
  }

  return (
    <div className="card">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 rounded-lg bg-white/5">
          <Clock className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold mb-1">Operating Hours</h2>
          <p className="text-sm text-dim">
            Set your hours manually or import from Google Maps.
          </p>
        </div>
      </div>

      <GoogleMapsImport accountId={accountId} onHoursImported={handleHoursImported} />

      <div className="my-4">
        <p className="text-sm font-medium text-center text-dim">Or set hours manually</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="opening-time" className="block text-sm font-medium mb-2">
              Opening Time
            </label>
            <input
              type="time"
              id="opening-time"
              value={openingTime}
              onChange={(e) => setOpeningTime(e.target.value)}
              disabled={updateHoursMutation.isPending}
            />
            <p className="text-xs text-dim mt-2">24-hour format</p>
          </div>

          <div>
            <label htmlFor="closing-time" className="block text-sm font-medium mb-2">
              Closing Time
            </label>
            <input
              type="time"
              id="closing-time"
              value={closingTime}
              onChange={(e) => setClosingTime(e.target.value)}
              disabled={updateHoursMutation.isPending}
            />
            <p className="text-xs text-dim mt-2">24-hour format</p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-3">
            Operating Days
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {weekdays.map((day) => (
              <button
                key={day.value}
                type="button"
                onClick={() => toggleDay(day.value)}
                disabled={updateHoursMutation.isPending}
                className={`btn btn-sm ${
                  operatingDays.includes(day.value) ? 'btn-primary' : 'btn-secondary'
                }`}
              >
                {day.label}
              </button>
            ))}
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

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateHoursMutation.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            {updateHoursMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Hours
              </>
            )}
          </button>
        </div>
      </form>

      {(currentOpeningTime || currentClosingTime || (currentOperatingDays && currentOperatingDays.length > 0)) && (
        <div className="mt-6 p-4 rounded-lg bg-white/5 border border-[--border]">
          <p className="text-sm font-medium mb-2">Current Operating Hours:</p>
          {currentOpeningTime && currentClosingTime && (
            <p className="text-lg mb-2">
              {currentOpeningTime} - {currentClosingTime}
            </p>
          )}
          {currentOperatingDays && currentOperatingDays.length > 0 && (
            <p className="text-sm text-dim">
              Open: {currentOperatingDays.map((d: number) => weekdays[d].label).join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
