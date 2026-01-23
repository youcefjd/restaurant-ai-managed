import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import { useAuth } from '../../../contexts/AuthContext'
import PageHeader from '../../../components/ui/PageHeader'
import PhoneSettings from './PhoneSettings'
import OperatingHoursSettings from './OperatingHoursSettings'

export default function Settings() {
  const { user } = useAuth()
  const accountId = user?.id

  const { data: account, isLoading } = useQuery({
    queryKey: ['account', accountId],
    queryFn: () => restaurantAPI.getAccount(accountId!),
    enabled: !!accountId,
    select: (response) => response.data,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  if (!accountId) {
    return <div className="text-dim">No account found</div>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Configure your restaurant's phone number and operating hours"
      />

      <PhoneSettings
        accountId={accountId}
        currentPhone={account?.twilio_phone_number || null}
      />

      <OperatingHoursSettings
        accountId={accountId}
        currentOpeningTime={account?.opening_time || null}
        currentClosingTime={account?.closing_time || null}
        currentOperatingDays={account?.operating_days || null}
      />

      {/* How it works */}
      <div className="card">
        <h3 className="font-medium mb-4">How it works</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs flex-shrink-0">1</span>
            <p className="text-dim">Customer calls your Twilio phone number</p>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs flex-shrink-0">2</span>
            <p className="text-dim">AI assistant answers and identifies your restaurant</p>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs flex-shrink-0">3</span>
            <p className="text-dim">AI answers questions, takes orders, and makes reservations</p>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs flex-shrink-0">4</span>
            <p className="text-dim">Orders and reservations appear in your dashboard</p>
          </div>
        </div>
      </div>
    </div>
  )
}
