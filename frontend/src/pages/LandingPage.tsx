import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell, Phone, Bot, Zap, BarChart3, UtensilsCrossed,
  CheckCircle, ArrowRight, Clock, CreditCard, MessageSquare,
  TrendingUp, CalendarCheck, Mic, FileText, Smartphone,
  Store, Settings, Globe, Languages
} from 'lucide-react'
import ContactFormModal from '../components/ContactFormModal'

const isMarketingSite = window.location.hostname.endsWith('belltab.com')

export default function LandingPage() {
  const navigate = useNavigate()
  const [showContact, setShowContact] = useState(false)
  const handleGetStarted = isMarketingSite ? () => setShowContact(true) : () => navigate('/signup')

  const featureCategories = [
    {
      icon: Bot,
      title: 'AI Voice Agent',
      color: 'var(--accent-cyan)',
      features: [
        { icon: Phone, text: '24/7 phone answering — never miss a call' },
        { icon: UtensilsCrossed, text: 'Menu-aware conversations with dietary info' },
        { icon: Mic, text: 'Natural voice powered by advanced AI' },
        { icon: Languages, text: 'Multi-language support — English, Spanish & more' },
        { icon: FileText, text: 'Call transcripts with AI summaries' },
      ],
    },
    {
      icon: Zap,
      title: 'Smart Automation',
      color: 'var(--accent-yellow, #facc15)',
      features: [
        { icon: MessageSquare, text: 'Voice-to-order pipeline — calls become orders' },
        { icon: CreditCard, text: 'Stripe + Toast POS payment collection' },
        { icon: Smartphone, text: 'SMS order confirmations to customers' },
        { icon: CalendarCheck, text: 'Reservation management & scheduling' },
      ],
    },
    {
      icon: BarChart3,
      title: 'Analytics & Insights',
      color: 'var(--accent-purple, #a78bfa)',
      features: [
        { icon: TrendingUp, text: 'Real-time revenue & order dashboards' },
        { icon: BarChart3, text: 'Popular items & menu performance' },
        { icon: Phone, text: 'Call analytics — duration, outcomes, sentiment' },
        { icon: Clock, text: 'Peak hours & demand forecasting' },
      ],
    },
    {
      icon: Store,
      title: 'Restaurant Management',
      color: 'var(--accent-green, #4ade80)',
      features: [
        { icon: UtensilsCrossed, text: 'Menu builder with categories, modifiers & tags' },
        { icon: Clock, text: 'Operating hours & advance ordering' },
        { icon: Globe, text: 'Multi-location support' },
        { icon: Settings, text: 'Full control over AI behavior & settings' },
      ],
    },
  ]

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      features: [
        '30-day full trial',
        'Up to 50 orders/month',
        'Basic menu management',
        'Call transcripts',
        'Email support',
      ],
      highlight: false,
    },
    {
      name: 'Starter',
      price: '$49',
      period: 'per month',
      features: [
        'Unlimited orders',
        'AI phone answering 24/7',
        'Menu-aware AI conversations',
        'Analytics dashboard',
        'SMS confirmations',
        'Priority support',
      ],
      highlight: true,
    },
    {
      name: 'Pro',
      price: '$149',
      period: 'per month',
      features: [
        'Everything in Starter',
        'Multi-location support',
        'Advanced analytics & reporting',
        'Toast POS integration',
        'Custom AI voice & branding',
        'Dedicated account manager',
      ],
      highlight: false,
    },
  ]

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[--border] backdrop-blur-md" style={{ background: 'rgba(var(--bg-card-rgb, 15, 15, 15), 0.85)' }}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-accent" />
            <h1 className="text-lg font-semibold">Belltab AI</h1>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <button onClick={() => scrollTo('features')} className="text-sm text-dim hover:text-white transition-colors">Features</button>
            <button onClick={() => scrollTo('how-it-works')} className="text-sm text-dim hover:text-white transition-colors">How It Works</button>
            <button onClick={() => scrollTo('pricing')} className="text-sm text-dim hover:text-white transition-colors">Pricing</button>
          </nav>
          <div className="flex gap-3">
            {!isMarketingSite && (
              <button onClick={() => navigate('/login')} className="btn btn-secondary">
                Login
              </button>
            )}
            <button onClick={handleGetStarted} className="btn btn-primary">
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative py-24 px-4 overflow-hidden">
        {/* Gradient glow background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full opacity-15"
            style={{ background: 'radial-gradient(ellipse, var(--accent-cyan) 0%, transparent 70%)' }} />
          <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] rounded-full opacity-10"
            style={{ background: 'radial-gradient(ellipse, var(--accent-purple, #a78bfa) 0%, transparent 70%)' }} />
        </div>

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm mb-8" style={{ background: 'rgba(var(--accent-cyan-rgb, 34, 211, 238), 0.1)', border: '1px solid rgba(var(--accent-cyan-rgb, 34, 211, 238), 0.2)' }}>
            <Bell className="w-4 h-4 text-accent" />
            <span className="text-accent">AI-powered restaurant phone system</span>
          </div>
          <h2 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Your Restaurant's{' '}
            <span className="text-accent">AI Front Desk</span>
          </h2>
          <p className="text-lg md:text-xl text-dim mb-10 max-w-2xl mx-auto leading-relaxed">
            Never miss a call, order, or reservation again. Belltab AI answers your phone 24/7,
            takes orders with perfect accuracy, and sends them straight to your kitchen.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button onClick={handleGetStarted} className="btn btn-primary px-8 py-3 text-base flex items-center gap-2">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => scrollTo('how-it-works')} className="btn btn-secondary px-8 py-3 text-base">
              See How It Works
            </button>
          </div>
        </div>

        {/* Social Proof Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-20 max-w-3xl mx-auto relative z-10">
          {[
            { value: '24/7', label: 'Availability', sublabel: 'Never miss a call' },
            { value: '< 1s', label: 'Response Time', sublabel: 'Instant AI pickup' },
            { value: '100%', label: 'Order Accuracy', sublabel: 'AI-verified orders' },
          ].map((stat) => (
            <div key={stat.label} className="card text-center">
              <p className="text-3xl font-bold text-accent mb-1">{stat.value}</p>
              <p className="text-sm font-medium">{stat.label}</p>
              <p className="text-xs text-dim mt-1">{stat.sublabel}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Demo Video */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">See It In Action</h3>
            <p className="text-dim text-lg">Watch our AI voice agent take a real restaurant order</p>
          </div>
          <div className="relative w-full rounded-2xl overflow-hidden border border-[--border]" style={{ paddingBottom: '56.25%' }}>
            <iframe
              className="absolute inset-0 w-full h-full"
              src="https://www.youtube.com/embed/JEBXIFSeI14"
              title="Belltab AI Demo"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4" style={{ background: 'var(--bg-card)' }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to Run a Modern Restaurant
            </h3>
            <p className="text-dim text-lg max-w-2xl mx-auto">
              From AI-powered phone answering to real-time analytics — one platform to automate and grow your business.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {featureCategories.map((category) => (
              <div key={category.title} className="card">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${category.color}15`, color: category.color }}>
                    <category.icon className="w-5 h-5" />
                  </div>
                  <h4 className="text-xl font-semibold">{category.title}</h4>
                </div>
                <ul className="space-y-3">
                  {category.features.map((feature) => (
                    <li key={feature.text} className="flex items-start gap-3">
                      <feature.icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: category.color }} />
                      <span className="text-sm text-dim">{feature.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">Up and Running in Minutes</h3>
            <p className="text-dim text-lg">Three simple steps to automate your restaurant's phone</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Upload Your Menu',
                description: 'Add your full menu with prices, categories, modifiers, and dietary tags. Our AI learns every detail.',
                icon: UtensilsCrossed,
              },
              {
                step: '2',
                title: 'Connect Your Phone',
                description: 'Forward your restaurant line or get a new AI number. Calls are answered instantly, 24/7.',
                icon: Phone,
              },
              {
                step: '3',
                title: 'Watch Orders Flow In',
                description: 'AI takes orders, collects payments, and sends confirmations. You focus on cooking.',
                icon: TrendingUp,
              },
            ].map((item) => (
              <div key={item.step} className="card text-center relative">
                <div className="w-12 h-12 rounded-full bg-accent flex items-center justify-center text-lg font-bold mx-auto mb-4" style={{ color: 'var(--bg-primary, #000)' }}>
                  {item.step}
                </div>
                <item.icon className="w-6 h-6 text-accent mx-auto mb-3" />
                <h4 className="font-semibold mb-2 text-lg">{item.title}</h4>
                <p className="text-sm text-dim leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4" style={{ background: 'var(--bg-card)' }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl md:text-4xl font-bold mb-4">Simple, Transparent Pricing</h3>
            <p className="text-dim text-lg">Start free. Upgrade when you're ready.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`card relative ${plan.highlight ? 'border-accent' : ''}`}
                style={plan.highlight ? { boxShadow: '0 0 40px rgba(var(--accent-cyan-rgb, 34, 211, 238), 0.1)' } : undefined}
              >
                {plan.highlight && (
                  <span className="badge badge-info mb-4">Most Popular</span>
                )}
                <h4 className="text-xl font-bold mb-2">{plan.name}</h4>
                <div className="mb-6">
                  <span className={`text-4xl font-bold ${plan.highlight ? 'text-accent' : ''}`}>
                    {plan.price}
                  </span>
                  <span className="text-sm text-dim"> /{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                      <span className="text-dim">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={handleGetStarted}
                  className={`btn w-full ${plan.highlight ? 'btn-primary' : 'btn-secondary'}`}
                >
                  {plan.price === '$0' ? 'Start Free Trial' : 'Get Started'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-10"
            style={{ background: 'radial-gradient(ellipse, var(--accent-cyan) 0%, transparent 70%)' }} />
        </div>
        <div className="max-w-2xl mx-auto text-center relative z-10">
          <h3 className="text-3xl md:text-4xl font-bold mb-4">Ready to Never Miss Another Order?</h3>
          <p className="text-dim text-lg mb-10">
            Join restaurants using Belltab AI to answer every call, take every order, and grow their business on autopilot.
          </p>
          <button
            onClick={handleGetStarted}
            className="btn btn-primary px-10 py-4 text-base flex items-center gap-2 mx-auto"
          >
            Start Your Free Trial <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[--border]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-accent" />
            <span className="font-semibold">Belltab AI</span>
          </div>
          <p className="text-sm text-dim">&copy; 2026 Belltab AI. All rights reserved.</p>
          <button
            onClick={() => navigate('/admin-login')}
            className="text-sm text-dim hover:text-accent transition-colors"
          >
            Admin
          </button>
        </div>
      </footer>

      <ContactFormModal open={showContact} onClose={() => setShowContact(false)} />
    </div>
  )
}
