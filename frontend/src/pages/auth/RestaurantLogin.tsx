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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-xl mb-4">
            <Phone className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">RestaurantAI</h1>
          <p className="text-gray-500 mt-2">Restaurant Portal Login</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Email Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="your@email.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              className="w-full py-3 px-4 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
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
              <p className="text-sm text-gray-500">
                Don't have an account?{' '}
                <Link to="/signup" className="text-blue-600 font-medium hover:underline">
                  Sign up for free trial
                </Link>
              </p>
            </div>

            {/* Admin Link */}
            <div className="pt-4 border-t border-gray-200 text-center">
              <Link to="/admin-login" className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                Platform Admin Login
              </Link>
            </div>
          </form>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-sm text-blue-700 font-medium mb-3">Test Accounts (password: test123)</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { email: 'chinese@test.com', name: 'Golden Dragon' },
              { email: 'mexican@test.com', name: 'Casa del Sol' },
              { email: 'italian@test.com', name: 'Bella Italia' },
              { email: 'french@test.com', name: 'Le Petit Bistro' },
            ].map((account) => (
              <button
                key={account.email}
                type="button"
                onClick={() => {
                  setEmail(account.email)
                  setPassword('test123')
                }}
                className="text-left p-2 rounded-lg bg-white border border-blue-200 hover:border-blue-400 hover:bg-blue-50 transition-colors"
              >
                <p className="text-xs font-mono text-blue-700">{account.email}</p>
                <p className="text-xs text-gray-500">{account.name}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
