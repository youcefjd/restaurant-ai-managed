import { useNavigate } from 'react-router-dom'
import { Phone, Menu, DollarSign, BarChart3, CheckCircle, ArrowRight, Sparkles } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  const features = [
    {
      icon: Phone,
      title: 'AI Phone Answering',
      description: 'Intelligent AI handles calls, takes orders, answers menu questions, and books reservations 24/7.',
      color: 'cyan',
    },
    {
      icon: Menu,
      title: 'Menu-Aware AI',
      description: 'AI knows your entire menu, dietary options, modifiers, and can suggest alternatives.',
      color: 'pink',
    },
    {
      icon: DollarSign,
      title: 'Automated Payments',
      description: 'Seamless Stripe Connect integration with automatic commission splits.',
      color: 'mint',
    },
    {
      icon: BarChart3,
      title: 'Real-time Analytics',
      description: 'Track orders, revenue, customer insights with beautiful dashboards.',
      color: 'purple',
    },
  ]

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      features: [
        '30-day trial',
        'Up to 50 orders/month',
        'Basic menu management',
        'Email support',
      ],
      cta: 'Start Free Trial',
      highlight: false,
    },
    {
      name: 'Starter',
      price: '$49',
      period: 'per month',
      features: [
        'Unlimited orders',
        'AI phone answering',
        'Menu-aware AI',
        'Analytics dashboard',
        'Priority support',
      ],
      cta: 'Get Started',
      highlight: true,
    },
    {
      name: 'Professional',
      price: '$149',
      period: 'per month',
      features: [
        'Everything in Starter',
        'Multi-location support',
        'Advanced analytics',
        'Custom integrations',
        'Dedicated support',
      ],
      cta: 'Contact Sales',
      highlight: false,
    },
  ]

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      cyan: { bg: 'rgba(0, 212, 255, 0.15)', text: 'var(--accent-cyan)' },
      pink: { bg: 'rgba(255, 107, 157, 0.15)', text: 'var(--accent-pink)' },
      mint: { bg: 'rgba(125, 255, 175, 0.15)', text: 'var(--accent-mint)' },
      purple: { bg: 'rgba(167, 139, 250, 0.15)', text: 'var(--accent-purple)' },
    }
    return colors[color] || colors.cyan
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Ambient background */}
      <div className="bg-ambient">
        <div className="ambient-blob ambient-blob-cyan w-[600px] h-[600px] -top-[300px] left-1/4 opacity-20" />
        <div className="ambient-blob ambient-blob-pink w-[500px] h-[500px] top-[40%] -right-[200px] opacity-15" />
        <div className="ambient-blob ambient-blob-purple w-[400px] h-[400px] bottom-[20%] left-[10%] opacity-10" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50" style={{ background: 'rgba(15, 15, 20, 0.8)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--border-glass)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="icon-box icon-box-md icon-box-cyan rounded-xl">
                <Phone className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-semibold text-white">RestaurantAI</h1>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/login')}
                className="btn-glass"
              >
                Restaurant Login
              </button>
              <button
                onClick={() => navigate('/admin-login')}
                className="btn-primary"
              >
                Platform Admin
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 badge badge-cyan mb-6">
              <Sparkles className="w-4 h-4" />
              <span>AI-Powered Platform</span>
            </div>
            <h2 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
              AI-Powered Restaurant
              <span className="block text-gradient-cyan">Management</span>
            </h2>
            <p className="text-lg mb-8 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Transform your restaurant with intelligent AI phone answering, menu-aware conversations,
              and automated order processing. Never miss a call or order again.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={() => navigate('/signup')}
                className="btn-primary px-8 py-4 text-base inline-flex items-center gap-2"
              >
                Start Free Trial <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => navigate('/login')}
                className="btn-secondary px-8 py-4 text-base"
              >
                Restaurant Login
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
            {[
              { value: '24/7', label: 'AI Phone Answering', color: 'cyan' },
              { value: '100%', label: 'Order Accuracy', color: 'mint' },
              { value: '10%', label: 'Platform Commission', color: 'pink' },
            ].map((stat) => (
              <div key={stat.label} className="glass-card text-center">
                <p className="text-5xl font-bold mb-2" style={{ color: `var(--accent-${stat.color})` }}>{stat.value}</p>
                <p style={{ color: 'var(--text-secondary)' }}>{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Everything You Need to Run a Modern Restaurant
            </h3>
            <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
              Powerful features designed to save time and increase revenue
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => {
              const colors = getColorClasses(feature.color)
              return (
                <div
                  key={feature.title}
                  className="glass-card group hover:scale-[1.02] transition-transform"
                >
                  <div
                    className="icon-box icon-box-lg rounded-xl mb-4"
                    style={{ background: colors.bg, color: colors.text }}
                  >
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">{feature.title}</h4>
                  <p style={{ color: 'var(--text-muted)' }} className="text-sm">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Get Started in Minutes
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Sign Up & Add Menu', description: 'Create your account and upload your restaurant menu with items, prices, and modifiers', color: 'cyan' },
              { step: '2', title: 'Connect Stripe', description: 'Link your Stripe account for automatic payment processing with commission splits', color: 'pink' },
              { step: '3', title: 'Start Taking Orders', description: 'AI starts answering calls, taking orders, and managing reservations instantly', color: 'mint' },
            ].map((item) => (
              <div key={item.step} className="glass-card text-center">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4"
                  style={{ background: `var(--accent-${item.color})`, color: '#000' }}
                >
                  {item.step}
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">{item.title}</h4>
                <p style={{ color: 'var(--text-muted)' }}>{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Simple, Transparent Pricing
            </h3>
            <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
              Choose the plan that fits your restaurant
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`glass-card ${plan.highlight ? 'scale-105 glow-cyan' : ''}`}
                style={plan.highlight ? { border: '1px solid var(--accent-cyan)' } : {}}
              >
                {plan.highlight && (
                  <div className="badge badge-cyan mb-4">Most Popular</div>
                )}
                <h4 className="text-xl font-bold text-white mb-2">
                  {plan.name}
                </h4>
                <div className="mb-6">
                  <span className="text-4xl font-bold" style={{ color: plan.highlight ? 'var(--accent-cyan)' : 'white' }}>
                    {plan.price}
                  </span>
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    {' '}/{plan.period}
                  </span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--accent-mint)' }} />
                      <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => navigate('/signup')}
                  className={plan.highlight ? 'btn-primary w-full py-3' : 'btn-secondary w-full py-3'}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="glass-card text-center p-12" style={{ background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, var(--bg-card) 50%, rgba(255, 107, 157, 0.1) 100%)' }}>
            <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Restaurant?
            </h3>
            <p className="text-lg mb-8" style={{ color: 'var(--text-secondary)' }}>
              Join thousands of restaurants already using AI to grow their business
            </p>
            <button
              onClick={() => navigate('/signup')}
              className="btn-primary px-10 py-4 text-lg inline-flex items-center gap-2"
            >
              Start Your Free Trial <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-12" style={{ borderTop: '1px solid var(--border-glass)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="icon-box icon-box-sm icon-box-cyan rounded-lg">
                  <Phone className="w-4 h-4" />
                </div>
                <h5 className="text-lg font-semibold text-white">RestaurantAI</h5>
              </div>
              <p style={{ color: 'var(--text-muted)' }} className="text-sm">
                AI-powered platform for modern restaurants
              </p>
            </div>
            <div>
              <h6 className="font-semibold text-white mb-4">Product</h6>
              <ul className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                <li className="hover:text-white cursor-pointer transition-colors">Features</li>
                <li className="hover:text-white cursor-pointer transition-colors">Pricing</li>
                <li className="hover:text-white cursor-pointer transition-colors">Demo</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold text-white mb-4">Company</h6>
              <ul className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                <li className="hover:text-white cursor-pointer transition-colors">About</li>
                <li className="hover:text-white cursor-pointer transition-colors">Blog</li>
                <li className="hover:text-white cursor-pointer transition-colors">Careers</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold text-white mb-4">Support</h6>
              <ul className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                <li className="hover:text-white cursor-pointer transition-colors">Help Center</li>
                <li className="hover:text-white cursor-pointer transition-colors">Contact</li>
                <li className="hover:text-white cursor-pointer transition-colors">Status</li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 text-center text-sm" style={{ borderTop: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
            2025 RestaurantAI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
