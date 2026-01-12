import { useNavigate } from 'react-router-dom'
import { Phone, Menu, DollarSign, BarChart3, CheckCircle, ArrowRight } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  const features = [
    {
      icon: Phone,
      title: 'AI Phone Answering',
      description: 'Intelligent AI handles calls, takes orders, answers menu questions, and books reservations 24/7.',
    },
    {
      icon: Menu,
      title: 'Menu-Aware AI',
      description: 'AI knows your entire menu, dietary options, modifiers, and can suggest alternatives.',
    },
    {
      icon: DollarSign,
      title: 'Automated Payments',
      description: 'Seamless Stripe Connect integration with automatic commission splits.',
    },
    {
      icon: BarChart3,
      title: 'Real-time Analytics',
      description: 'Track orders, revenue, customer insights with beautiful dashboards.',
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Phone className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-primary-600">RestaurantAI</h1>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/login')}
                className="btn btn-secondary"
              >
                Restaurant Login
              </button>
              <button
                onClick={() => navigate('/admin-login')}
                className="btn btn-primary"
              >
                Platform Admin
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            AI-Powered Restaurant Platform
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Transform your restaurant with intelligent AI phone answering, menu-aware conversations,
            and automated order processing. Never miss a call or order again.
          </p>
          <div className="flex gap-4 justify-center">
            <button onClick={() => navigate('/signup')} className="btn btn-primary px-8 py-3 text-lg">
              Start Free Trial <ArrowRight className="w-5 h-5 ml-2 inline" />
            </button>
            <button onClick={() => navigate('/login')} className="btn btn-secondary px-8 py-3 text-lg">
              Restaurant Login
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
          <div className="text-center">
            <p className="text-4xl font-bold text-primary-600">24/7</p>
            <p className="text-gray-600 mt-2">AI Phone Answering</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-primary-600">100%</p>
            <p className="text-gray-600 mt-2">Order Accuracy</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-primary-600">10%</p>
            <p className="text-gray-600 mt-2">Platform Commission</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Run a Modern Restaurant
            </h3>
            <p className="text-lg text-gray-600">
              Powerful features designed to save time and increase revenue
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div key={feature.title} className="text-center">
                <div className="inline-flex p-4 bg-primary-50 rounded-lg mb-4">
                  <feature.icon className="w-8 h-8 text-primary-600" />
                </div>
                <h4 className="text-xl font-semibold mb-2">{feature.title}</h4>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Get Started in Minutes
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                1
              </div>
              <h4 className="text-xl font-semibold mb-2">Sign Up & Add Menu</h4>
              <p className="text-gray-600">
                Create your account and upload your restaurant menu with items, prices, and modifiers
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                2
              </div>
              <h4 className="text-xl font-semibold mb-2">Connect Stripe</h4>
              <p className="text-gray-600">
                Link your Stripe account for automatic payment processing with commission splits
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                3
              </div>
              <h4 className="text-xl font-semibold mb-2">Start Taking Orders</h4>
              <p className="text-gray-600">
                AI starts answering calls, taking orders, and managing reservations instantly
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h3>
            <p className="text-lg text-gray-600">
              Choose the plan that fits your restaurant
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-lg p-8 ${
                  plan.highlight
                    ? 'bg-primary-600 text-white ring-4 ring-primary-300 scale-105'
                    : 'bg-white border-2 border-gray-200'
                }`}
              >
                <h4 className={`text-2xl font-bold mb-2 ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>
                  {plan.name}
                </h4>
                <div className="mb-6">
                  <span className={`text-4xl font-bold ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price}
                  </span>
                  <span className={`text-sm ${plan.highlight ? 'text-primary-100' : 'text-gray-600'}`}>
                    {' '}/{plan.period}
                  </span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle className={`w-5 h-5 flex-shrink-0 ${plan.highlight ? 'text-white' : 'text-green-600'}`} />
                      <span className={`text-sm ${plan.highlight ? 'text-white' : 'text-gray-600'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`w-full py-3 rounded-lg font-medium transition-colors ${
                    plan.highlight
                      ? 'bg-white text-primary-600 hover:bg-gray-100'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Phone className="w-6 h-6" />
                <h5 className="text-lg font-bold">RestaurantAI</h5>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered platform for modern restaurants
              </p>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Product</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Features</li>
                <li>Pricing</li>
                <li>Demo</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Company</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>About</li>
                <li>Blog</li>
                <li>Careers</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Support</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Help Center</li>
                <li>Contact</li>
                <li>Status</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            2025 RestaurantAI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
