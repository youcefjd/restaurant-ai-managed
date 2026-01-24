import { useQuery } from '@tanstack/react-query'
import { MapPin, Clock } from 'lucide-react'
import { restaurantAPI } from '../../../services/api'
import { useAuth } from '../../../contexts/AuthContext'
import PageHeader from '../../../components/ui/PageHeader'
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

  // Format address display
  const formatAddress = () => {
    const parts = []
    if (account?.address) parts.push(account.address)
    const cityStateZip = [account?.city, account?.state, account?.zip_code].filter(Boolean).join(', ')
    if (cityStateZip) parts.push(cityStateZip)
    return parts.length > 0 ? parts : ['No address set']
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Manage your restaurant profile and operating hours"
      />

      {/* Restaurant Profile */}
      <div className="card">
        <h3 className="font-medium mb-4">Restaurant Profile</h3>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-dim mt-0.5" />
            <div>
              <p className="text-sm text-dim mb-1">Address</p>
              {formatAddress().map((line, i) => (
                <p key={i} className="text-sm">{line}</p>
              ))}
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-dim mt-0.5" />
            <div>
              <p className="text-sm text-dim mb-1">Timezone</p>
              <p className="text-sm">{account?.timezone || 'America/New_York'}</p>
            </div>
          </div>
        </div>
      </div>

      <OperatingHoursSettings
        accountId={accountId}
        currentOpeningTime={account?.opening_time || null}
        currentClosingTime={account?.closing_time || null}
        currentOperatingDays={account?.operating_days || null}
      />
    </div>
  )
}
