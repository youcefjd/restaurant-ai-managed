import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { MessageSquare, Phone, MessageCircle, Calendar, Clock, Search } from 'lucide-react'
import api from '../../services/api'
import LoadingTRex from '../../components/LoadingTRex'

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
  created_at: string
  updated_at: string | null
  message_count: number
}

export default function Transcripts() {
  const { user } = useAuth()
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [selectedTranscript, setSelectedTranscript] = useState<Transcript | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'sms' | 'voice'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    if (user?.id) {
      loadTranscripts()
    }
  }, [user, filter])

  const loadTranscripts = async () => {
    if (!user?.id) return
    
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filter !== 'all') {
        params.append('transcript_type', filter)
      }
      
      const response = await api.get(`/onboarding/accounts/${user.id}/transcripts?${params.toString()}`)
      setTranscripts(response.data.transcripts || [])
    } catch (error) {
      console.error('Failed to load transcripts:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredTranscripts = transcripts.filter(t => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        t.customer_phone.toLowerCase().includes(query) ||
        t.messages.some(m => m.content.toLowerCase().includes(query))
      )
    }
    return true
  })

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
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
    
    const colors: Record<string, string> = {
      booking_created: 'bg-green-100 text-green-800',
      order_placed: 'bg-blue-100 text-blue-800',
      inquiry: 'bg-gray-100 text-gray-800'
    }
    
    const labels: Record<string, string> = {
      booking_created: 'Booking Created',
      order_placed: 'Order Placed',
      inquiry: 'Inquiry'
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[outcome] || 'bg-gray-100 text-gray-800'}`}>
        {labels[outcome] || outcome}
      </span>
    )
  }

  if (loading) {
    return <LoadingTRex message="Loading transcripts" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transcripts</h1>
          <p className="text-gray-600 mt-1">View SMS and voice call conversations</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar - Transcript List */}
        <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col">
          {/* Filters */}
          <div className="p-4 border-b border-gray-200 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search transcripts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'all'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('sms')}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'sms'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                SMS
              </button>
              <button
                onClick={() => setFilter('voice')}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'voice'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Voice
              </button>
            </div>
          </div>

          {/* Transcript List */}
          <div className="flex-1 overflow-y-auto">
            {filteredTranscripts.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No transcripts found</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredTranscripts.map((transcript) => (
                  <button
                    key={transcript.id}
                    onClick={() => setSelectedTranscript(transcript)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                      selectedTranscript?.id === transcript.id ? 'bg-primary-50 border-l-4 border-primary-500' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        transcript.transcript_type === 'voice'
                          ? 'bg-blue-100 text-blue-600'
                          : 'bg-green-100 text-green-600'
                      }`}>
                        {transcript.transcript_type === 'voice' ? (
                          <Phone className="w-4 h-4" />
                        ) : (
                          <MessageCircle className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {transcript.customer_phone}
                          </p>
                          {getOutcomeBadge(transcript.outcome)}
                        </div>
                        <p className="text-xs text-gray-500 mb-1">
                          {transcript.message_count} messages
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(transcript.created_at)}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Transcript Details */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200">
          {selectedTranscript ? (
            <div className="p-6 h-full flex flex-col">
              {/* Header */}
              <div className="border-b border-gray-200 pb-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      selectedTranscript.transcript_type === 'voice'
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-green-100 text-green-600'
                    }`}>
                      {selectedTranscript.transcript_type === 'voice' ? (
                        <Phone className="w-5 h-5" />
                      ) : (
                        <MessageCircle className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">
                        {selectedTranscript.transcript_type === 'voice' ? 'Voice Call' : 'SMS Conversation'}
                      </h2>
                      <p className="text-sm text-gray-500">{selectedTranscript.customer_phone}</p>
                    </div>
                  </div>
                  {getOutcomeBadge(selectedTranscript.outcome)}
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-600 mt-3">
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
                  <div className="text-gray-400">
                    {selectedTranscript.message_count} messages
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4">
                {selectedTranscript.messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className={`text-xs mt-2 ${
                        message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                      }`}>
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
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Summary</h3>
                  <p className="text-sm text-gray-600">{selectedTranscript.summary}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Select a transcript to view details</p>
              <p className="text-sm mt-1">Choose a conversation from the list to see the full transcript</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
