import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle, Crown, Loader2, Sparkles } from 'lucide-react'
import { createStore } from '../lib/api'
import { getDemoUserId } from '../lib/utils'

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    description: 'Start selling immediately',
    features: [
      'AI-powered storefront',
      'Product management',
      'Squad payment receiving',
      'Guest checkout',
      'Daily WhatsApp notification',
      'Order management',
      'Economic identity basics',
      'Public store link',
    ],
    cta: 'Start free',
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 3000,
    period: '/month',
    description: 'Everything you need to grow',
    highlighted: true,
    features: [
      'Everything in Free',
      'Advanced WhatsApp operations',
      'Campaign and referral links',
      'Conversion and revenue analytics',
      'Inventory intelligence',
      'AI operational support',
      'Richer economic identity',
    ],
    cta: 'Pay NGN 3,000/mo',
  },
]

export default function Publish() {
  const navigate = useNavigate()
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSelectPlan(plan) {
    setSelectedPlan(plan.id)
    setLoading(true)
    setError('')

    try {
      const storeBuild = JSON.parse(sessionStorage.getItem('aaje_store_build') || '{}')
      const userId = getDemoUserId()

      if (!storeBuild.store_name) {
        setError('Store data not found. Please go back and rebuild.')
        setLoading(false)
        return
      }

      const response = await createStore({
        user_id: userId,
        store_name: storeBuild.store_name,
        slug: storeBuild.slug,
        description: storeBuild.description,
        tagline: storeBuild.tagline,
        template: storeBuild.template || 'fashion',
        theme: storeBuild.theme || 'default',
        categories: storeBuild.categories || [],
        starter_products: storeBuild.starter_products || [],
        config_json: storeBuild,
      })

      const store = response.data
      localStorage.setItem('aaje_store', JSON.stringify(store))

      const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')
      user.plan = plan.id
      user.onboarding_complete = true
      localStorage.setItem('aaje_user', JSON.stringify(user))

      sessionStorage.removeItem('aaje_store_build')
      sessionStorage.removeItem('aaje_onboarding_answers')

      navigate('/dashboard')
    } catch (err) {
      console.error('Publish error:', err)
      setError(err.response?.data?.detail || 'Failed to publish store. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#fbf8ff] px-4 py-14 text-[#12102b] sm:px-6">
      <div className="mx-auto max-w-5xl">
        <div className="text-center">
          <div className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-[#dcd4ed] bg-[#f2edff] px-4 py-1.5 text-xs font-bold uppercase text-[#5a4be7]">
            <Sparkles className="h-3.5 w-3.5" />
            Almost there
          </div>
          <h1 className="text-4xl font-semibold tracking-[-0.02em]">Choose your plan</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-[#74708a]">
            Your store is built. Pick a plan to publish and start selling.
          </p>
        </div>

        {error && (
          <div className="mx-auto mt-6 max-w-md rounded-[8px] border border-red-200 bg-red-50 p-3 text-center text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative rounded-[12px] bg-white p-8 transition-all ${
                plan.highlighted
                  ? 'border border-[#5a4be7] shadow-[0_24px_70px_rgba(42,25,91,0.14)]'
                  : 'border border-[#e4e1ee]'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 inline-flex items-center gap-1 rounded-full bg-[#5a4be7] px-4 py-1 text-xs font-semibold text-white">
                  <Crown className="h-3 w-3" />
                  Recommended
                </div>
              )}

              <div className="mb-7">
                <h2 className="text-2xl font-semibold">{plan.name}</h2>
                <p className="mt-2 text-sm text-[#74708a]">{plan.description}</p>
                <div className="mt-5">
                  {plan.price === 0 ? (
                    <span className="text-4xl font-semibold">Free</span>
                  ) : (
                    <div>
                      <span className="text-4xl font-semibold">NGN {plan.price.toLocaleString()}</span>
                      <span className="text-sm text-[#74708a]">{plan.period}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mb-8 space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3">
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#5a4be7]" />
                    <span className="text-sm text-[#625d75]">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handleSelectPlan(plan)}
                disabled={loading && selectedPlan === plan.id}
                className={`inline-flex h-12 w-full items-center justify-center gap-2 rounded-[8px] text-sm font-bold transition disabled:opacity-60 ${
                  plan.highlighted
                    ? 'bg-[#5a4be7] text-white hover:bg-[#493bd0]'
                    : 'border border-[#e4e1ee] bg-white text-[#12102b] hover:border-[#5a4be7]'
                }`}
              >
                {loading && selectedPlan === plan.id ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    {plan.cta}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
