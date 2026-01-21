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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center">
                <Phone className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900">RestaurantAI</h1>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/login')}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Restaurant Login
              </button>
              <button
                onClick={() => navigate('/admin-login')}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Platform Admin
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              AI-Powered Restaurant Management
            </h2>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              Transform your restaurant with intelligent AI phone answering, menu-aware conversations,
              and automated order processing. Never miss a call or order again.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={() => navigate('/signup')}
                className="px-6 py-3 text-base font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors inline-flex items-center gap-2"
              >
                Start Free Trial <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 text-base font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors"
              >
                Restaurant Login
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16 pt-16 border-t border-gray-200">
            {[
              { value: '24/7', label: 'AI Phone Answering' },
              { value: '100%', label: 'Order Accuracy' },
              { value: '10%', label: 'Platform Commission' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-4xl font-bold text-blue-600 mb-1">{stat.value}</p>
                <p className="text-gray-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Run a Modern Restaurant
            </h3>
            <p className="text-lg text-gray-600">
              Powerful features designed to save time and increase revenue
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h4>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Get Started in Minutes
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Sign Up & Add Menu', description: 'Create your account and upload your restaurant menu with items, prices, and modifiers' },
              { step: '2', title: 'Connect Stripe', description: 'Link your Stripe account for automatic payment processing with commission splits' },
              { step: '3', title: 'Start Taking Orders', description: 'AI starts answering calls, taking orders, and managing reservations instantly' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h4>
                <p className="text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h3>
            <p className="text-lg text-gray-600">
              Choose the plan that fits your restaurant
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl p-8 ${
                  plan.highlight
                    ? 'bg-blue-600 text-white ring-4 ring-blue-200 scale-105'
                    : 'bg-white border border-gray-200 shadow-sm'
                }`}
              >
                <h4 className={`text-xl font-bold mb-2 ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>
                  {plan.name}
                </h4>
                <div className="mb-6">
                  <span className={`text-4xl font-bold ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price}
                  </span>
                  <span className={`text-sm ${plan.highlight ? 'text-blue-100' : 'text-gray-500'}`}>
                    {' '}/{plan.period}
                  </span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle className={`w-5 h-5 flex-shrink-0 ${plan.highlight ? 'text-blue-200' : 'text-green-500'}`} />
                      <span className={`text-sm ${plan.highlight ? 'text-white' : 'text-gray-600'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`w-full py-3 rounded-lg font-medium transition-colors ${
                    plan.highlight
                      ? 'bg-white text-blue-600 hover:bg-blue-50'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Restaurant?
          </h3>
          <p className="text-lg text-blue-100 mb-8">
            Join thousands of restaurants already using AI to grow their business
          </p>
          <button
            onClick={() => navigate('/signup')}
            className="px-8 py-4 text-lg font-medium text-blue-600 bg-white hover:bg-blue-50 rounded-lg transition-colors inline-flex items-center gap-2"
          >
            Start Your Free Trial <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                  <Phone className="w-4 h-4 text-white" />
                </div>
                <h5 className="text-lg font-semibold">RestaurantAI</h5>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered platform for modern restaurants
              </p>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Product</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="hover:text-white cursor-pointer transition-colors">Features</li>
                <li className="hover:text-white cursor-pointer transition-colors">Pricing</li>
                <li className="hover:text-white cursor-pointer transition-colors">Demo</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Company</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="hover:text-white cursor-pointer transition-colors">About</li>
                <li className="hover:text-white cursor-pointer transition-colors">Blog</li>
                <li className="hover:text-white cursor-pointer transition-colors">Careers</li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Support</h6>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="hover:text-white cursor-pointer transition-colors">Help Center</li>
                <li className="hover:text-white cursor-pointer transition-colors">Contact</li>
                <li className="hover:text-white cursor-pointer transition-colors">Status</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            © 2025 RestaurantAI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
