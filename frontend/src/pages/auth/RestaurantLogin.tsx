import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Mail, Lock, AlertCircle, Phone, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function RestaurantLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password, false)
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--bg-primary)' }}>
      {/* Ambient background */}
      <div className="bg-ambient">
        <div className="ambient-blob ambient-blob-cyan w-[500px] h-[500px] -top-[200px] -left-[200px] opacity-20" />
        <div className="ambient-blob ambient-blob-pink w-[400px] h-[400px] bottom-[10%] -right-[150px] opacity-15" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="icon-box icon-box-lg icon-box-cyan rounded-2xl mx-auto mb-4">
            <Phone className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold text-white">RestaurantAI</h1>
          <p className="mt-2" style={{ color: 'var(--text-muted)' }}>Restaurant Portal Login</p>
        </div>

        {/* Login Card */}
        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Email Input */}
            <div>
              <label className="label-glass">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-10"
                  placeholder="your@email.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label className="label-glass">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-glass pl-10"
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            {/* Signup Link */}
            <div className="text-center">
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Don't have an account?{' '}
                <Link to="/signup" className="font-medium hover:underline" style={{ color: 'var(--accent-cyan)' }}>
                  Sign up for free trial
                </Link>
              </p>
            </div>

            {/* Admin Link */}
            <div className="pt-4 text-center" style={{ borderTop: '1px solid var(--border-glass)' }}>
              <Link to="/admin-login" className="text-sm transition-colors hover:text-white" style={{ color: 'var(--text-muted)' }}>
                Platform Admin Login
              </Link>
            </div>
          </form>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 glass-card p-4" style={{ background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, var(--bg-card) 100%)' }}>
          <p className="text-sm font-medium mb-3" style={{ color: 'var(--accent-cyan)' }}>Test Accounts (password: test123)</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { email: 'mario@example.com', name: "Mario's Italian Kitchen" },
              { email: 'john@testpizza.com', name: 'Test Pizza Place' },
              { email: 'owner@tacotown.com', name: 'Taco Town' },
              { email: 'sierra.nesbit@gmail.com', name: "Sierra's Palace" },
            ].map((account) => (
              <button
                key={account.email}
                type="button"
                onClick={() => {
                  setEmail(account.email)
                  setPassword('test123')
                }}
                className="text-left p-2 rounded-xl transition-all hover:scale-[1.02]"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)' }}
              >
                <p className="text-xs font-mono" style={{ color: 'var(--accent-cyan)' }}>{account.email}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{account.name}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
