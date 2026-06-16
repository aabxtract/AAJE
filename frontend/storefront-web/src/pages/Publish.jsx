import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Globe, Loader2, Sparkles } from 'lucide-react'
import { createStore } from '../lib/api'

// MVP: no plan picker. The trader's storefront is published the moment they
// confirm. Pricing comes back as a separate marketing page (/pricing) and
// later as a dashboard upgrade flow — not in the onboarding path.

export default function Publish() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [storeBuild, setStoreBuild] = useState(null)

  useEffect(() => {
    const raw = sessionStorage.getItem('aaje_store_build')
    if (!raw) {
      setError('Store data not found. Please go back and rebuild.')
      return
    }
    try {
      setStoreBuild(JSON.parse(raw))
    } catch {
      setError('Store data is corrupted. Please go back and rebuild.')
    }
  }, [])

  async function handlePublish() {
    if (!storeBuild?.store_name && !storeBuild?.business_description) {
      setError('Store data is incomplete. Go back and finish onboarding.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await createStore({
        business_description: storeBuild.business_description || storeBuild.description,
        store_name: storeBuild.store_name,
        slug: storeBuild.slug,
        description: storeBuild.description,
        tagline: storeBuild.tagline,
        template: storeBuild.template,
        theme: storeBuild.theme,
        categories: storeBuild.categories || [],
        starter_products: storeBuild.starter_products || [],
        config_json: storeBuild,
      })

      const store = response.data
      localStorage.setItem('aaje_store', JSON.stringify(store))

      const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')
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

  const storeName = storeBuild?.store_name || 'your store'
  const storeSlug = storeBuild?.slug || 'your-store'

  return (
    <main className="min-h-screen bg-[#fbf8ff] px-4 py-14 text-[#12102b] sm:px-6">
      <div className="mx-auto max-w-xl">
        <div className="text-center">
          <div className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-[#dcd4ed] bg-[#f2edff] px-4 py-1.5 text-xs font-bold uppercase text-[#5a4be7]">
            <Sparkles className="h-3.5 w-3.5" />
            One last step
          </div>
          <h1 className="text-4xl font-semibold tracking-[-0.02em]">
            Ready to go live?
          </h1>
          <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-[#74708a]">
            Your storefront for <strong>{storeName}</strong> is built. Publish to
            get your live URL and start receiving orders.
          </p>
        </div>

        <div className="mt-10 rounded-2xl border border-[#e4e1ee] bg-white p-7 shadow-[0_24px_70px_rgba(42,25,91,0.06)]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#f2edff] text-[#5a4be7]">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-[#74708a]">
                Your URL
              </p>
              <p className="font-mono text-sm font-semibold text-[#12102b]">
                {storeSlug}.aaje.store
              </p>
            </div>
          </div>

          <p className="mt-5 text-xs leading-relaxed text-[#74708a]">
            You can change your bank account, products, and store details
            anytime from your dashboard. Customers transfer directly to your
            bank for now — automated payments come back next month after CAC
            clears.
          </p>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            onClick={handlePublish}
            disabled={loading || !storeBuild}
            className="mt-6 inline-flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-[#5a4be7] text-sm font-bold text-white transition hover:bg-[#493bd0] disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Publishing…
              </>
            ) : (
              <>
                Publish my store
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

        <button
          onClick={() => navigate('/confirm')}
          className="mt-4 block w-full text-center text-sm font-medium text-[#74708a] hover:text-[#12102b]"
        >
          ← Edit my store
        </button>
      </div>
    </main>
  )
}
