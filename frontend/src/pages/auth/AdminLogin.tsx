import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Shield, Mail, Lock, AlertCircle, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AdminLogin() {
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
      await login(email, password, true)
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
        <div className="ambient-blob ambient-blob-purple w-[500px] h-[500px] -top-[200px] -right-[200px] opacity-20" />
        <div className="ambient-blob ambient-blob-pink w-[400px] h-[400px] bottom-[10%] -left-[150px] opacity-15" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="icon-box icon-box-lg rounded-2xl mx-auto mb-4" style={{ background: 'rgba(167, 139, 250, 0.15)', color: 'var(--accent-purple)' }}>
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold text-white">Platform Admin</h1>
          <p className="mt-2" style={{ color: 'var(--text-muted)' }}>Secure Admin Access</p>
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
                Admin Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-10"
                  placeholder="admin@restaurantai.com"
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
              className="w-full py-3 px-4 rounded-xl font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: 'linear-gradient(135deg, var(--accent-purple) 0%, #8b5cf6 100%)', color: '#fff', boxShadow: '0 4px 15px rgba(167, 139, 250, 0.3)' }}
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Verifying...
                </>
              ) : (
                'Admin Sign In'
              )}
            </button>

            {/* Back Link */}
            <div className="text-center">
              <Link
                to="/"
                className="inline-flex items-center gap-2 text-sm transition-colors hover:text-white"
                style={{ color: 'var(--text-muted)' }}
              >
                <ArrowLeft className="w-4 h-4" />
                Back to home
              </Link>
            </div>
          </form>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 glass-card p-4" style={{ background: 'linear-gradient(135deg, rgba(255, 184, 108, 0.1) 0%, var(--bg-card) 100%)' }}>
          <p className="text-sm font-medium mb-2" style={{ color: 'var(--accent-orange)' }}>Demo Admin Credentials:</p>
          <button
            type="button"
            onClick={() => {
              setEmail('admin@restaurantai.com')
              setPassword('admin123')
            }}
            className="w-full text-left p-2 rounded-xl transition-all hover:scale-[1.02]"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)' }}
          >
            <p className="text-xs font-mono" style={{ color: 'var(--accent-orange)' }}>admin@restaurantai.com</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Password: admin123</p>
          </button>
        </div>
      </div>
    </div>
  )
}
