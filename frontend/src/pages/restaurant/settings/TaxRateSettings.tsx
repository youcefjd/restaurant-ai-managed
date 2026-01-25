import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import { Receipt, Save, Loader2, AlertCircle, CheckCircle } from 'lucide-react'

interface TaxRateSettingsProps {
  accountId: number
  currentTaxRate: number | null
}

export default function TaxRateSettings({
  accountId,
  currentTaxRate,
}: TaxRateSettingsProps) {
  const queryClient = useQueryClient()
  const [taxRate, setTaxRate] = useState<string>(
    currentTaxRate ? (currentTaxRate * 100).toFixed(2) : ''
  )
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (currentTaxRate !== null) {
      setTaxRate((currentTaxRate * 100).toFixed(2))
    }
  }, [currentTaxRate])

  const updateTaxRateMutation = useMutation({
    mutationFn: (rate: number) => restaurantAPI.updateTaxRate(accountId, rate),
    onSuccess: () => {
      setSuccess('Tax rate updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update tax rate')
      setSuccess('')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const rateValue = parseFloat(taxRate)

    if (isNaN(rateValue) || rateValue < 0 || rateValue > 25) {
      setError('Tax rate must be between 0% and 25%')
      return
    }

    // Convert percentage to decimal (e.g., 8.25 -> 0.0825)
    updateTaxRateMutation.mutate(rateValue / 100)
  }

  return (
    <div className="card">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 rounded-lg bg-white/5">
          <Receipt className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold mb-1">Tax Rate</h2>
          <p className="text-sm text-dim">
            Set your local sales tax rate for order totals.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="tax-rate" className="block text-sm font-medium mb-2">
            Tax Rate (%)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              id="tax-rate"
              step="0.01"
              min="0"
              max="25"
              value={taxRate}
              onChange={(e) => setTaxRate(e.target.value)}
              disabled={updateTaxRateMutation.isPending}
              className="w-32"
              placeholder="8.25"
            />
            <span className="text-dim">%</span>
          </div>
          <p className="text-xs text-dim mt-2">
            Enter as percentage (e.g., 8.25 for 8.25%)
          </p>
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
            disabled={updateTaxRateMutation.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            {updateTaxRateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Tax Rate
              </>
            )}
          </button>
        </div>
      </form>

      {currentTaxRate !== null && (
        <div className="mt-6 p-4 rounded-lg bg-white/5 border border-[--border]">
          <p className="text-sm font-medium mb-1">Current Tax Rate:</p>
          <p className="text-lg">{(currentTaxRate * 100).toFixed(2)}%</p>
        </div>
      )}
    </div>
  )
}
