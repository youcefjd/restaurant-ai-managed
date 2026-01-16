import { useQuery, useMutation, useQueryClient } from '@tantml/react-query'
import { restaurantAPI } from '../../services/api'
import { Calendar, Clock, Users, CheckCircle, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

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
        return 'bg-green-100 text-green-700'
      case 'pending':
        return 'bg-orange-100 text-orange-700'
      case 'cancelled':
        return 'bg-red-100 text-red-700'
      case 'completed':
        return 'bg-blue-100 text-blue-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-orange-600" />
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading reservations...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Table Reservations</h1>
          <p className="text-gray-600 mt-1">Manage table bookings</p>
        </div>

        <div className="flex gap-2">
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-gray-200 bg-white"
          >
            <option value="all">All Dates</option>
            <option value="today">Today</option>
            <option value="upcoming">Upcoming</option>
          </select>

          {['all', 'confirmed', 'pending', 'completed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                statusFilter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {bookingData.length === 0 ? (
        <div className="card text-center py-12">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No reservations found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {bookingData.map((booking: any) => (
            <div key={booking.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  {getStatusIcon(booking.status)}
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-lg">
                        Reservation #{booking.id}
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(booking.status)}`}>
                        {booking.status}
                      </span>
                    </div>

                    {/* Customer Info */}
                    <p className="text-sm text-gray-600 mt-1">
                      {booking.customer?.name || 'Guest'} • {booking.customer?.phone || 'No phone'}
                    </p>

                    {/* Date & Time */}
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-700">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {new Date(booking.booking_date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
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

                    {/* Table Info */}
                    {booking.table_id && (
                      <p className="text-sm text-gray-600 mt-2">
                        <span className="font-medium">Table:</span> #{booking.table_id}
                      </p>
                    )}

                    {/* Special Requests */}
                    {booking.special_requests && (
                      <p className="text-sm text-gray-700 mt-2 bg-yellow-50 p-2 rounded border border-yellow-200">
                        <span className="font-medium">📝 Note:</span> {booking.special_requests}
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="text-right">
                  {booking.status === 'confirmed' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() =>
                          updateStatusMutation.mutate({ id: booking.id, status: 'completed' })
                        }
                        className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Complete
                      </button>
                      <button
                        onClick={() =>
                          updateStatusMutation.mutate({ id: booking.id, status: 'cancelled' })
                        }
                        className="text-sm px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
