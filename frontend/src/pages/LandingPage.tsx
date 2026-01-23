import { useNavigate } from 'react-router-dom'
import { Phone, Menu, DollarSign, BarChart3, CheckCircle, ArrowRight } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  const features = [
    {
      icon: Phone,
      title: 'AI Phone Answering',
      description: 'Intelligent AI handles calls, takes orders, and books reservations 24/7.',
    },
    {
      icon: Menu,
      title: 'Menu-Aware AI',
      description: 'AI knows your entire menu, dietary options, and can suggest alternatives.',
    },
    {
      icon: DollarSign,
      title: 'Automated Payments',
      description: 'Seamless Stripe Connect integration with automatic commission splits.',
    },
    {
      icon: BarChart3,
      title: 'Real-time Analytics',
      description: 'Track orders, revenue, and customer insights with beautiful dashboards.',
    },
  ]

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      features: ['30-day trial', 'Up to 50 orders/month', 'Basic menu management', 'Email support'],
      highlight: false,
    },
    {
      name: 'Starter',
      price: '$49',
      period: 'per month',
      features: ['Unlimited orders', 'AI phone answering', 'Menu-aware AI', 'Analytics dashboard', 'Priority support'],
      highlight: true,
    },
    {
      name: 'Professional',
      price: '$149',
      period: 'per month',
      features: ['Everything in Starter', 'Multi-location support', 'Advanced analytics', 'Custom integrations', 'Dedicated support'],
      highlight: false,
    },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[--border]" style={{ background: 'var(--bg-card)' }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-accent" />
            <h1 className="text-lg font-semibold">RestaurantAI</h1>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/login')} className="btn btn-secondary">
              Login
            </button>
            <button onClick={() => navigate('/signup')} className="btn btn-primary">
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            AI-Powered Restaurant Management
          </h2>
          <p className="text-lg text-dim mb-8 max-w-2xl mx-auto">
            Transform your restaurant with intelligent AI phone answering, menu-aware conversations,
            and automated order processing. Never miss a call or order again.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button onClick={() => navigate('/signup')} className="btn btn-primary px-6 py-3 flex items-center gap-2">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => navigate('/login')} className="btn btn-secondary px-6 py-3">
              Restaurant Login
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16 max-w-3xl mx-auto">
          {[
            { value: '24/7', label: 'AI Phone Answering' },
            { value: '100%', label: 'Order Accuracy' },
            { value: '10%', label: 'Platform Commission' },
          ].map((stat) => (
            <div key={stat.label} className="card text-center">
              <p className="text-3xl font-bold text-accent mb-1">{stat.value}</p>
              <p className="text-sm text-dim">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4" style={{ background: 'var(--bg-card)' }}>
        <div className="max-w-5xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-12">
            Everything You Need to Run a Modern Restaurant
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div key={feature.title} className="card">
                <feature.icon className="w-8 h-8 text-accent mb-4" />
                <h4 className="font-semibold mb-2">{feature.title}</h4>
                <p className="text-sm text-dim">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-12">Get Started in Minutes</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { step: '1', title: 'Sign Up & Add Menu', description: 'Create your account and upload your restaurant menu' },
              { step: '2', title: 'Connect Stripe', description: 'Link your Stripe account for automatic payment processing' },
              { step: '3', title: 'Start Taking Orders', description: 'AI starts answering calls and taking orders instantly' },
            ].map((item) => (
              <div key={item.step} className="card text-center">
                <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-lg font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h4 className="font-semibold mb-2">{item.title}</h4>
                <p className="text-sm text-dim">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 px-4" style={{ background: 'var(--bg-card)' }}>
        <div className="max-w-5xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-4">Simple, Transparent Pricing</h3>
          <p className="text-center text-dim mb-12">Choose the plan that fits your restaurant</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`card ${plan.highlight ? 'border-accent' : ''}`}
              >
                {plan.highlight && (
                  <span className="badge badge-info mb-4">Most Popular</span>
                )}
                <h4 className="text-xl font-bold mb-2">{plan.name}</h4>
                <div className="mb-6">
                  <span className={`text-3xl font-bold ${plan.highlight ? 'text-accent' : ''}`}>
                    {plan.price}
                  </span>
                  <span className="text-sm text-dim"> /{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                      <span className="text-dim">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => navigate('/signup')}
                  className={`btn w-full ${plan.highlight ? 'btn-primary' : 'btn-secondary'}`}
                >
                  Get Started
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h3 className="text-2xl font-bold mb-4">Ready to Transform Your Restaurant?</h3>
          <p className="text-dim mb-8">Join restaurants already using AI to grow their business</p>
          <button
            onClick={() => navigate('/signup')}
            className="btn btn-primary px-8 py-3 flex items-center gap-2 mx-auto"
          >
            Start Your Free Trial <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[--border]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-accent" />
            <span className="font-semibold">RestaurantAI</span>
          </div>
          <p className="text-sm text-dim">2025 RestaurantAI. All rights reserved.</p>
          <button
            onClick={() => navigate('/admin-login')}
            className="text-sm text-dim hover:text-accent"
          >
            Platform Admin
          </button>
        </div>
      </footer>
    </div>
  )
}
