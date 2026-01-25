import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Phone, Mail, Lock, Building, User, AlertCircle, CheckCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Signup() {
  const [formData, setFormData] = useState({
    business_name: '',
    owner_name: '',
    owner_email: '',
    owner_phone: '',
    password: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuth()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await signup(formData)
    } catch (err: any) {
      setError(err.message || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[--bg] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-accent rounded-full mb-4">
            <Phone className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold">Start Your Free Trial</h1>
          <p className="text-dim mt-2">30 days free, no credit card required</p>
        </div>

        {/* Signup Card */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Error Message */}
            {error && (
              <div className="bg-danger/10 border border-danger/20 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
                <p className="text-sm text-danger">{error}</p>
              </div>
            )}

            {/* Restaurant Name */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Restaurant Name
              </label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim" />
                <input
                  type="text"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[--border] rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
                  placeholder="Mario's Italian Kitchen"
                  required
                />
              </div>
            </div>

            {/* Owner Name */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Your Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim" />
                <input
                  type="text"
                  name="owner_name"
                  value={formData.owner_name}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[--border] rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
                  placeholder="Mario Rossi"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim" />
                <input
                  type="email"
                  name="owner_email"
                  value={formData.owner_email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[--border] rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
                  placeholder="mario@restaurant.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Phone */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Phone Number
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim" />
                <input
                  type="tel"
                  name="owner_phone"
                  value={formData.owner_phone}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[--border] rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
                  placeholder="+1 (555) 123-4567"
                  required
                  autoComplete="tel"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[--border] rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
                  placeholder="••••••••"
                  required
                  autoComplete="new-password"
                  minLength={6}
                />
              </div>
              <p className="text-xs text-dim mt-1">Minimum 6 characters</p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary py-4 text-lg font-semibold"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>

            {/* Login Link */}
            <div className="text-center pt-2">
              <p className="text-sm text-dim">
                Already have an account?{' '}
                <Link to="/login" className="text-accent font-medium hover:underline">
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </div>

        {/* Benefits */}
        <div className="card mt-6 p-4">
          <p className="text-sm font-medium mb-3">What you get with your free trial:</p>
          <ul className="text-sm text-dim space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-success" />
              30-day free trial
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-success" />
              AI-powered phone ordering
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-success" />
              Order & reservation management
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-success" />
              No credit card required
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
