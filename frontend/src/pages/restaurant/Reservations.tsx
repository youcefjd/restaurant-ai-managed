import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Calendar, Clock, Users, CheckCircle, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import PageHeader from '../../components/ui/PageHeader'

export default function RestaurantReservations() {
  const { user } = useAuth()
  const accountId = user?.id
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [dateFilter, setDateFilter] = useState<string>('today')
  const queryClient = useQueryClient()

  const { data: bookings, isLoading } = useQuery({
    queryKey: ['bookings', accountId, statusFilter, dateFilter],
    queryFn: () => {
      const params: any = {}
      if (statusFilter !== 'all') params.status_filter = statusFilter

      // Date filtering
      if (dateFilter === 'today') {
        params.date_from = new Date().toISOString().split('T')[0]
      } else if (dateFilter === 'upcoming') {
        params.date_from = new Date().toISOString().split('T')[0]
      }

      return restaurantAPI.getBookings(accountId!, params)
    },
    enabled: !!accountId,
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      restaurantAPI.updateBookingStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
    },
  })

  const bookingData = bookings?.data || []

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'badge-success'
      case 'pending':
        return 'badge-warning'
      case 'cancelled':
        return 'badge-danger'
      case 'completed':
        return 'badge-info'
      default:
        return 'badge-info'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-success" />
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-danger" />
      default:
        return <Clock className="w-5 h-5 text-warning" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Table Reservations"
        subtitle="Manage table bookings"
        actions={
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="w-auto"
          >
            <option value="all">All Dates</option>
            <option value="today">Today</option>
            <option value="upcoming">Upcoming</option>
          </select>
        }
      />

      {/* Status Filter */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'confirmed', 'pending', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`btn btn-sm capitalize ${
              statusFilter === status ? 'btn-primary' : 'btn-secondary'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {bookingData.length === 0 ? (
        <div className="card text-center py-12">
          <Calendar className="w-10 h-10 text-dim mx-auto mb-4" />
          <p className="text-dim">No reservations found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bookingData.map((booking: any) => (
            <div key={booking.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {getStatusIcon(booking.status)}
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-medium">Reservation #{booking.id}</h3>
                      <span className={`badge ${getStatusColor(booking.status)}`}>
                        {booking.status}
                      </span>
                    </div>

                    <p className="text-sm text-dim mt-1">
                      {booking.customer?.name || 'Guest'} • {booking.customer?.phone || 'No phone'}
                    </p>

                    <div className="flex items-center gap-4 mt-2 text-sm text-dim flex-wrap">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {new Date(booking.booking_date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{booking.booking_time}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        <span>{booking.party_size} guests</span>
                      </div>
                    </div>

                    {booking.table_id && (
                      <p className="text-sm text-dim mt-2">Table #{booking.table_id}</p>
                    )}

                    {booking.special_requests && (
                      <p className="text-sm mt-2 p-2 rounded-lg bg-warning/10 border border-warning/20 text-warning">
                        Note: {booking.special_requests}
                      </p>
                    )}
                  </div>
                </div>

                {booking.status === 'confirmed' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: booking.id, status: 'completed' })}
                      className="btn btn-sm btn-success"
                    >
                      Complete
                    </button>
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: booking.id, status: 'cancelled' })}
                      className="btn btn-sm btn-danger"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
