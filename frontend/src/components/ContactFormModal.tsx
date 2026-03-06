import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, User, Mail, Store, Phone, MessageSquare, ArrowRight, CheckCircle } from 'lucide-react'
import api from '../services/api'

interface ContactFormModalProps {
  open: boolean
  onClose: () => void
}

export default function ContactFormModal({ open, onClose }: ContactFormModalProps) {
  const [form, setForm] = useState({
    name: '',
    email: '',
    restaurant: '',
    phone: '',
    message: '',
  })
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('sending')
    try {
      await api.post('/contact', {
        name: form.name,
        email: form.email,
        restaurant: form.restaurant,
        phone: form.phone || undefined,
        message: form.message || undefined,
      })
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  const handleClose = () => {
    onClose()
    // Reset after animation
    setTimeout(() => {
      setStatus('idle')
      setForm({ name: '', email: '', restaurant: '', phone: '', message: '' })
    }, 300)
  }

  const fields: {
    key: keyof typeof form
    label: string
    icon: typeof User
    type: string
    placeholder: string
    required: boolean
    textarea?: boolean
  }[] = [
    { key: 'name', label: 'Full Name', icon: User, type: 'text', placeholder: 'John Doe', required: true },
    { key: 'email', label: 'Email', icon: Mail, type: 'email', placeholder: 'you@restaurant.com', required: true },
    { key: 'restaurant', label: 'Restaurant Name', icon: Store, type: 'text', placeholder: "Joe's Pizza", required: true },
    { key: 'phone', label: 'Phone Number', icon: Phone, type: 'tel', placeholder: '(555) 123-4567', required: false },
    { key: 'message', label: 'Message', icon: MessageSquare, type: 'text', placeholder: 'Tell us about your restaurant...', required: false, textarea: true },
  ]

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleClose} />

          {/* Ambient blobs */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div className="ambient-blob ambient-blob-cyan w-[400px] h-[400px] -top-[100px] -left-[100px] opacity-15" />
            <div className="ambient-blob ambient-blob-pink w-[300px] h-[300px] bottom-[5%] -right-[80px] opacity-10" />
          </div>

          {/* Card */}
          <motion.div
            className="glass-card p-8 w-full max-w-lg relative z-10 max-h-[90vh] overflow-y-auto"
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg transition-colors hover:bg-white/10"
              style={{ color: 'var(--text-muted)' }}
            >
              <X className="w-5 h-5" />
            </button>

            {status === 'sent' ? (
              <div className="text-center py-8">
                <CheckCircle className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--accent-green, #4ade80)' }} />
                <h2 className="text-2xl font-bold text-white mb-2">Thank you!</h2>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  We've received your inquiry and will get back to you within 24 hours.
                </p>
                <button onClick={handleClose} className="btn-primary mt-6 px-8 py-2">
                  Close
                </button>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-white">Get Started with Belltab AI</h2>
                  <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
                    Fill out the form and we'll get back to you within 24 hours.
                  </p>
                </div>

                {/* Error */}
                {status === 'error' && (
                  <div className="rounded-xl p-4 mb-4 text-sm text-red-400" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                    Something went wrong. Please try again.
                  </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-5">
                  {fields.map((f) => (
                    <div key={f.key}>
                      <label className="label-glass">
                        {f.label}
                        {!f.required && <span className="ml-1 opacity-50">(optional)</span>}
                      </label>
                      <div className="relative">
                        <f.icon
                          className="absolute left-3 top-3 w-5 h-5"
                          style={{ color: 'var(--text-muted)' }}
                        />
                        {f.textarea ? (
                          <textarea
                            value={form[f.key]}
                            onChange={set(f.key)}
                            className="input-glass pl-10 min-h-[80px] resize-y"
                            placeholder={f.placeholder}
                            required={f.required}
                            rows={3}
                          />
                        ) : (
                          <input
                            type={f.type}
                            value={form[f.key]}
                            onChange={set(f.key)}
                            className="input-glass pl-10"
                            placeholder={f.placeholder}
                            required={f.required}
                          />
                        )}
                      </div>
                    </div>
                  ))}

                  <button
                    type="submit"
                    disabled={status === 'sending'}
                    className="btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {status === 'sending' ? (
                      <>
                        <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        Send Inquiry
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </form>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
