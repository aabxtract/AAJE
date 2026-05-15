import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Package, Palette, RefreshCw, Rocket, Tag } from 'lucide-react'

export default function ConfirmBuild() {
  const navigate = useNavigate()
  const [store, setStore] = useState(null)

  useEffect(() => {
    const raw = sessionStorage.getItem('aaje_store_build')
    if (!raw) {
      navigate('/onboarding')
      return
    }
    setStore(JSON.parse(raw))
  }, [navigate])

  function handleRegenerate() {
    sessionStorage.removeItem('aaje_store_build')
    sessionStorage.removeItem('aaje_onboarding_answers')
    navigate('/onboarding')
  }

  function handleConfirm() {
    navigate('/publish')
  }

  if (!store) return null

  const products = store.starter_products || []

  return (
    <main className="min-h-screen bg-[#fbf8ff] px-4 py-12 text-[#12102b] sm:px-6">
      <div className="mx-auto max-w-4xl">
        <div className="text-center">
          <div className="mx-auto mb-5 grid h-16 w-16 place-items-center rounded-[18px] bg-[#ece6ff]">
            <Check className="h-8 w-8 text-[#5a4be7]" />
          </div>
          <h1 className="text-4xl font-semibold tracking-[-0.02em]">Your store is ready</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-[#74708a]">
            Review the AI-generated details below. You can regenerate the setup or continue to publishing.
          </p>
        </div>

        <div className="mt-10 overflow-hidden rounded-[12px] border border-[#e4e1ee] bg-white shadow-[0_24px_70px_rgba(42,25,91,0.08)]">
          <div className="border-b border-[#ece7f5] p-6">
            <div className="flex items-start gap-4">
              <div className="grid h-14 w-14 flex-shrink-0 place-items-center rounded-[12px] bg-[#5a4be7] text-xl font-black text-white">
                {store.store_name?.charAt(0) || 'A'}
              </div>
              <div>
                <h2 className="text-2xl font-semibold">{store.store_name}</h2>
                {store.tagline && <p className="mt-1 text-sm font-semibold text-[#5a4be7]">{store.tagline}</p>}
                <p className="mt-3 text-sm leading-6 text-[#625d75]">{store.description}</p>
              </div>
            </div>
          </div>

          <div className="grid gap-0 md:grid-cols-2">
            <section className="border-b border-[#ece7f5] p-6 md:border-r">
              <div className="flex items-center gap-2 text-sm font-semibold text-[#625d75]">
                <Palette className="h-4 w-4" />
                Template
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-[#f2edff] px-4 py-2 text-sm font-semibold capitalize text-[#5a4be7]">
                  {store.template || 'fashion'}
                </span>
                <span className="rounded-full bg-[#fafafa] px-4 py-2 text-sm text-[#625d75]">
                  Theme: {store.theme || 'default'}
                </span>
              </div>
            </section>

            <section className="border-b border-[#ece7f5] p-6">
              <div className="flex items-center gap-2 text-sm font-semibold text-[#625d75]">
                <Tag className="h-4 w-4" />
                Categories
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {(store.categories || []).map((cat) => (
                  <span key={cat} className="rounded-full border border-[#e4e1ee] bg-white px-3 py-1 text-xs font-semibold text-[#12102b]">
                    {cat}
                  </span>
                ))}
              </div>
            </section>
          </div>

          <section className="p-6">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#625d75]">
              <Package className="h-4 w-4" />
              Starter products ({products.length})
            </div>
            {products.length > 0 ? (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {products.map((product, index) => (
                  <div key={product.name || index} className="rounded-[8px] border border-[#ece7f5] bg-[#fbf9ff] p-4">
                    <p className="font-semibold">{product.name}</p>
                    <p className="mt-1 text-xs leading-5 text-[#74708a]">{product.description || 'No description'}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-sm font-bold text-[#5a4be7]">
                        NGN {Number(product.price || 0).toLocaleString()}
                      </span>
                      <span className="text-xs text-[#9b97aa]">
                        {product.type === 'service' ? 'Service' : `${product.stock_quantity || 0} in stock`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-[#74708a]">No starter products generated. You can add them from your dashboard.</p>
            )}
          </section>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button
            onClick={handleRegenerate}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-[8px] border border-[#e4e1ee] bg-white px-5 py-3 text-sm font-semibold text-[#12102b] transition hover:border-[#5a4be7]"
          >
            <RefreshCw className="h-4 w-4" />
            Regenerate
          </button>
          <button
            onClick={handleConfirm}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-[8px] bg-[#5a4be7] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#493bd0]"
          >
            <Rocket className="h-4 w-4" />
            Looks good. Publish
          </button>
        </div>
      </div>
    </main>
  )
}
