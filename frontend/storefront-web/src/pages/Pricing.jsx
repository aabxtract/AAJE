import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, ArrowRight, Zap, MessageCircle, TrendingUp } from 'lucide-react'

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    description: 'Perfect for getting started',
    features: [
      'AI-powered storefront',
      'Product management',
      'Squad payment receiving',
      'Basic checkout',
      'Daily WhatsApp sales notification (8PM)',
      'Order management',
      'Basic BizPrint',
      'Public storefront link',
    ],
    limitations: [
      'No advanced WhatsApp operations',
      'No campaign tracking',
      'No advanced analytics',
    ]
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 3000,
    period: 'per month',
    description: 'Everything you need to grow',
    highlighted: true,
    features: [
      'Everything in Free +',
      'Advanced WhatsApp operations',
      'Campaign & referral links (?ref=instagram)',
      'Conversion & revenue analytics',
      'Operational insights',
      'Inventory intelligence',
      'AI operational support',
      'WhatsApp product management',
      'Richer BizPrint & business scoring',
      'Increased AI assistance',
    ],
  }
]

export default function Pricing() {
  const navigate = useNavigate()
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSelectPlan(plan) {
    setSelectedPlan(plan.id)
    setLoading(true)

    try {
      await new Promise(resolve => setTimeout(resolve, 1000))

      if (plan.id === 'free') {
        const user = JSON.parse(localStorage.getItem('aaje_user'))
        user.plan = 'free'
        localStorage.setItem('aaje_user', JSON.stringify(user))
        navigate('/account-connect')
      } else {
        const user = JSON.parse(localStorage.getItem('aaje_user'))
        user.plan = 'premium'
        localStorage.setItem('aaje_user', JSON.stringify(user))
        navigate('/account-connect')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      {/* Header */}
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900">Simple, Transparent Pricing</h1>
        <p className="mt-4 text-lg text-gray-600">
          Start free. Upgrade anytime. Pay monthly.
        </p>
      </div>

      {/* Pricing cards */}
      <div className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-2 lg:gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative rounded-2xl transition-all ${
                plan.highlighted
                  ? 'ring-2 ring-primary-600 shadow-xl lg:scale-105'
                  : 'border border-gray-200 shadow-lg'
              } bg-white p-8`}
            >
              {plan.highlighted && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
              )}

              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">{plan.name}</h2>
                <p className="mt-2 text-sm text-gray-600">{plan.description}</p>

                <div className="mt-4">
                  {plan.price === 0 ? (
                    <div className="text-3xl font-bold text-gray-900">Free</div>
                  ) : (
                    <div>
                      <span className="text-4xl font-bold text-gray-900">₦{plan.price.toLocaleString()}</span>
                      <span className="text-gray-600 ml-2">{plan.period}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Features */}
              <div className="mb-8 space-y-3">
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </div>
                ))}

                {plan.limitations && (
                  <>
                    <div className="pt-2 border-t border-gray-200" />
                    {plan.limitations.map((limitation, idx) => (
                      <div key={idx} className="flex items-start gap-3 opacity-50">
                        <span className="h-5 w-5 text-gray-300 mt-0.5 flex-shrink-0">✕</span>
                        <span className="text-sm text-gray-500">{limitation}</span>
                      </div>
                    ))}
                  </>
                )}
              </div>

              {/* CTA Button */}
              <button
                onClick={() => handleSelectPlan(plan)}
                disabled={selectedPlan === plan.id && loading}
                className={`w-full py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                  plan.highlighted
                    ? 'btn-primary'
                    : 'border-2 border-gray-200 bg-white text-gray-900 hover:border-primary-300 hover:bg-primary-50'
                }`}
              >
                {selectedPlan === plan.id && loading ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
                    Setting up...
                  </>
                ) : (
                  <>
                    {plan.id === 'free' ? 'Get Started Free' : 'Start Premium'}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Feature comparison */}
      <div className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-12 text-center">What you get on each plan</h2>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Storefront */}
            <div className="rounded-lg border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="inline-flex items-center justify-center rounded-lg bg-blue-100 p-2">
                  <MessageCircle className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900">WhatsApp Integration</h3>
              </div>
              <p className="text-sm text-gray-600">
                <strong className="text-gray-900">Free:</strong> Daily sales notification at 8PM.
              </p>
              <p className="text-sm text-gray-600 mt-2">
                <strong className="text-gray-900">Premium:</strong> Full operational control, product updates, inventory management.
              </p>
            </div>

            {/* Analytics */}
            <div className="rounded-lg border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="inline-flex items-center justify-center rounded-lg bg-purple-100 p-2">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Analytics</h3>
              </div>
              <p className="text-sm text-gray-600">
                <strong className="text-gray-900">Free:</strong> Basic sales tracking.
              </p>
              <p className="text-sm text-gray-600 mt-2">
                <strong className="text-gray-900">Premium:</strong> Campaign analytics, conversion tracking, revenue insights.
              </p>
            </div>

            {/* AI Assistance */}
            <div className="rounded-lg border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="inline-flex items-center justify-center rounded-lg bg-yellow-100 p-2">
                  <Zap className="h-5 w-5 text-yellow-600" />
                </div>
                <h3 className="font-semibold text-gray-900">AI Help</h3>
              </div>
              <p className="text-sm text-gray-600">
                <strong className="text-gray-900">Free:</strong> Basic navigation support.
              </p>
              <p className="text-sm text-gray-600 mt-2">
                <strong className="text-gray-900">Premium:</strong> Advanced operational assistance & insights.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="bg-gradient-to-br from-primary-50 to-white border-t border-gray-200">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Frequently Asked</h2>

          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900">Can I upgrade anytime?</h3>
              <p className="mt-2 text-gray-600">Yes. Upgrade to Premium anytime. Changes take effect immediately.</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900">Is there a setup fee?</h3>
              <p className="mt-2 text-gray-600">No setup fees. Premium is NGN 3,000/month. Free plan is completely free.</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900">Can I cancel?</h3>
              <p className="mt-2 text-gray-600">Yes. Cancel anytime. Your store remains accessible. Back up your data.</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900">Do you take a percentage of my sales?</h3>
              <p className="mt-2 text-gray-600">No. AAJE does not take transaction fees. Squad may apply standard payment fees.</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
