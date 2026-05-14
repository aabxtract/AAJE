import { useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle, ShoppingCart } from 'lucide-react'
import { formatCurrency } from '../lib/utils'

const fallbackImage =
  'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80'

export default function StorePreview() {
  const navigate = useNavigate()
  const generated = JSON.parse(sessionStorage.getItem('aaje_generated_store') || '{}')
  const persisted = JSON.parse(localStorage.getItem('aaje_store') || '{}')
  const store = { ...generated, ...persisted }
  const storeName = generated.store_name || generated.name || persisted.store_name || 'My Store'
  const products = generated.products || generated.starter_products || [
    {
      id: 'starter',
      name: 'Starter Item',
      description: 'Edit this item after setup.',
      price: 5000,
      image_url: fallbackImage,
    },
  ]

  return (
    <main className="min-h-screen bg-white">
      <div className="border-b border-gray-200 bg-gradient-to-r from-primary-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{storeName}</h1>
              <p className="mt-2 text-gray-600">Your AI-powered storefront preview</p>
            </div>
            <button onClick={() => navigate('/pricing')} className="btn-primary flex items-center gap-2">
              <ArrowRight className="h-4 w-4" />
              Choose Plan
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-1">
            <div className="rounded-lg bg-gray-50 p-6">
              <div className="mb-2 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
                <p className="font-semibold text-gray-900">Store Ready</p>
              </div>
              <p className="text-sm text-gray-600">
                AAJE generated a store setup connected to your signed-in account.
              </p>
            </div>

            <div className="rounded-lg bg-blue-50 p-6">
              <h3 className="mb-2 font-semibold text-gray-900">Store URL</h3>
              <p className="break-all font-mono text-sm text-blue-700">aaje.store/{store.slug || 'your-store'}</p>
            </div>

            <div className="rounded-lg bg-gray-50 p-6">
              <h3 className="mb-2 font-semibold text-gray-900">What is next?</h3>
              <ol className="space-y-2 text-sm text-gray-600">
                <li className="flex gap-2">
                  <span className="font-bold text-primary-600">1.</span>
                  <span>Choose Free or Grow.</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-primary-600">2.</span>
                  <span>Confirm payment setup.</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-primary-600">3.</span>
                  <span>Share your store and manage updates on WhatsApp.</span>
                </li>
              </ol>
            </div>
          </div>

          <div className="lg:col-span-2">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Starter Products</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              {products.map((product, index) => (
                <div key={product.id || product.name || index} className="overflow-hidden rounded-lg border border-gray-200 transition hover:shadow-lg">
                  <img src={product.image || product.image_url || fallbackImage} alt={product.name} className="h-48 w-full object-cover" />
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900">{product.name}</h3>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">{product.description}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <p className="text-lg font-bold text-primary-600">
                        {product.price ? formatCurrency(product.price) : 'Set price'}
                      </p>
                      <button className="rounded-lg bg-primary-100 p-2 text-primary-600 transition hover:bg-primary-200" aria-label="Preview cart action">
                        <ShoppingCart className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 bg-gradient-to-r from-primary-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-12 text-center sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900">Ready to publish?</h2>
          <p className="mt-2 text-gray-600">Choose a plan, confirm payment setup, then start selling with Squad checkout.</p>
          <button onClick={() => navigate('/pricing')} className="btn-primary mt-6 inline-flex items-center gap-2">
            <ArrowRight className="h-4 w-4" />
            Choose Plan
          </button>
        </div>
      </div>
    </main>
  )
}
