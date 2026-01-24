import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../contexts/AuthContext'
import { restaurantAPI } from '../../services/api'
import { MessageSquare, Phone, MessageCircle, Calendar, Clock, Search, X } from 'lucide-react'
import PageHeader from '../../components/ui/PageHeader'

interface Transcript {
  id: number
  transcript_type: 'sms' | 'voice'
  customer_phone: string
  twilio_phone: string | null
  conversation_id: string
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
    timestamp: string
  }>
  summary: string | null
  outcome: string | null
  duration_seconds: number | null
  order_id: number | null
  created_at: string
  updated_at: string | null
  message_count: number
}

export default function Transcripts() {
  const { user } = useAuth()
  const accountId = user?.id
  const [filter, setFilter] = useState<'all' | 'sms' | 'voice'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTranscript, setSelectedTranscript] = useState<Transcript | null>(null)

  const { data: transcriptsResponse, isLoading } = useQuery({
    queryKey: ['transcripts', accountId, filter],
    queryFn: () => {
      const params = filter !== 'all' ? { transcript_type: filter } : undefined
      return restaurantAPI.getTranscripts(accountId!, params)
    },
    enabled: !!accountId,
    staleTime: 60000,
    select: (response) => response.data.transcripts || [],
  })

  const transcripts: Transcript[] = transcriptsResponse || []

  const filteredTranscripts = useMemo(() => {
    if (!searchQuery) return transcripts
    const query = searchQuery.toLowerCase()
    return transcripts.filter(t =>
      t.customer_phone.toLowerCase().includes(query) ||
      t.messages.some(m => m.content.toLowerCase().includes(query))
    )
  }, [transcripts, searchQuery])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return null
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getOutcomeBadge = (outcome: string | null) => {
    if (!outcome) return null
    const badgeClass = outcome === 'booking_created' ? 'badge-success'
      : outcome === 'order_placed' ? 'badge-info' : 'badge-warning'
    const label = outcome === 'booking_created' ? 'Booking'
      : outcome === 'order_placed' ? 'Order' : outcome
    return <span className={`badge ${badgeClass}`}>{label}</span>
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
        title="Transcripts"
        subtitle="View SMS and voice call conversations"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar - Transcript List */}
        <div className="lg:col-span-1 card p-0 flex flex-col max-h-[calc(100vh-200px)]">
          {/* Filters */}
          <div className="p-4 border-b border-[--border] space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dim w-4 h-4" />
              <input
                type="text"
                placeholder="Search transcripts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex gap-2">
              {(['all', 'sms', 'voice'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilter(type)}
                  className={`btn btn-sm flex-1 ${filter === type ? 'btn-primary' : 'btn-secondary'}`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Transcript List */}
          <div className="flex-1 overflow-y-auto">
            {filteredTranscripts.length === 0 ? (
              <div className="p-8 text-center">
                <MessageSquare className="w-10 h-10 mx-auto mb-2 text-dim" />
                <p className="text-dim">No transcripts found</p>
              </div>
            ) : (
              <div className="divide-y divide-[--border]">
                {filteredTranscripts.map((transcript) => (
                  <button
                    key={transcript.id}
                    onClick={() => setSelectedTranscript(transcript)}
                    className={`w-full p-4 text-left hover:bg-white/5 transition-colors ${
                      selectedTranscript?.id === transcript.id ? 'bg-accent/10 border-l-2 border-accent' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        transcript.transcript_type === 'voice' ? 'bg-accent/20 text-accent' : 'bg-success/20 text-success'
                      }`}>
                        {transcript.transcript_type === 'voice' ? (
                          <Phone className="w-4 h-4" />
                        ) : (
                          <MessageCircle className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-medium truncate">{transcript.customer_phone}</p>
                          {transcript.order_id ? (
                            <span className="badge bg-accent/20 text-accent">Order #{transcript.order_id}</span>
                          ) : getOutcomeBadge(transcript.outcome)}
                        </div>
                        <p className="text-xs text-dim">{transcript.message_count} messages</p>
                        <p className="text-xs text-dim">{formatDate(transcript.created_at)}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Transcript Details */}
        <div className="lg:col-span-2 card p-0 flex flex-col max-h-[calc(100vh-200px)]">
          {selectedTranscript ? (
            <>
              {/* Header */}
              <div className="p-4 border-b border-[--border]">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      selectedTranscript.transcript_type === 'voice' ? 'bg-accent/20 text-accent' : 'bg-success/20 text-success'
                    }`}>
                      {selectedTranscript.transcript_type === 'voice' ? (
                        <Phone className="w-5 h-5" />
                      ) : (
                        <MessageCircle className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <h2 className="font-semibold">
                        {selectedTranscript.transcript_type === 'voice' ? 'Voice Call' : 'SMS Conversation'}
                      </h2>
                      <p className="text-sm text-dim">{selectedTranscript.customer_phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedTranscript.order_id && (
                      <span className="badge bg-accent/20 text-accent">Order #{selectedTranscript.order_id}</span>
                    )}
                    {getOutcomeBadge(selectedTranscript.outcome)}
                    <button onClick={() => setSelectedTranscript(null)} className="text-dim hover:text-white lg:hidden">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm text-dim">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {formatDate(selectedTranscript.created_at)}
                  </div>
                  {selectedTranscript.duration_seconds && (
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatDuration(selectedTranscript.duration_seconds)}
                    </div>
                  )}
                  <span>{selectedTranscript.message_count} messages</span>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {selectedTranscript.messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.role === 'user' ? 'bg-accent text-white' : 'bg-white/5'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/60' : 'text-dim'}`}>
                        {new Date(message.timestamp).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary */}
              {selectedTranscript.summary && (
                <div className="p-4 border-t border-[--border]">
                  <h3 className="text-sm font-medium mb-2">Summary</h3>
                  <p className="text-sm text-dim">{selectedTranscript.summary}</p>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 text-dim" />
                <p className="font-medium">Select a transcript</p>
                <p className="text-sm text-dim mt-1">Choose a conversation from the list</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
