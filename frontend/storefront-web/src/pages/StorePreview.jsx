import { useNavigate } from 'react-router-dom'
import { ArrowRight, Edit2, CheckCircle, ShoppingCart } from 'lucide-react'

export default function StorePreview() {
  const navigate = useNavigate()
  const store = JSON.parse(sessionStorage.getItem('aaje_store') || '{"name":"My Store","slug":"my-store","products":[]}')

  const mockProducts = [
    { id: 1, name: 'Premium Item 1', price: 15000, image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop' },
    { id: 2, name: 'Premium Item 2', price: 25000, image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop' },
    { id: 3, name: 'Premium Item 3', price: 35000, image: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&fit=crop' },
  ]

  return (
    <main className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gradient-to-r from-primary-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{store.name}</h1>
              <p className="mt-2 text-gray-600">Your AI-powered storefront</p>
            </div>
            <button
              onClick={() => navigate('/account-connect')}
              className="btn-primary flex items-center gap-2"
            >
              <ArrowRight className="h-4 w-4" />
              Proceed to Setup
            </button>
          </div>
        </div>
      </div>

      {/* Store preview */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Store info */}
          <div className="lg:col-span-1">
            <div className="space-y-4">
              <div className="rounded-lg bg-gray-50 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                  <p className="font-semibold text-gray-900">Store Ready</p>
                </div>
                <p className="text-sm text-gray-600">Your storefront has been generated with AI.</p>
              </div>

              <div className="rounded-lg bg-blue-50 p-6">
                <h3 className="font-semibold text-gray-900 mb-2">Store URL</h3>
                <p className="text-sm font-mono text-blue-700 break-all">
                  aaje.store/{store.slug}
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-6">
                <h3 className="font-semibold text-gray-900 mb-2">What's next?</h3>
                <ol className="space-y-2 text-sm text-gray-600">
                  <li className="flex gap-2">
                    <span className="font-bold text-primary-600">1.</span>
                    <span>Connect your account for payments</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-bold text-primary-600">2.</span>
                    <span>Choose your plan (Free or Premium)</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-bold text-primary-600">3.</span>
                    <span>Start selling and manage via WhatsApp</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>

          {/* Product grid preview */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Sample Products</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              {mockProducts.map((product) => (
                <div key={product.id} className="rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition">
                  <img
                    src={product.image}
                    alt={product.name}
                    className="h-48 w-full object-cover"
                  />
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900">{product.name}</h3>
                    <div className="mt-3 flex items-center justify-between">
                      <p className="text-lg font-bold text-primary-600">₦{product.price.toLocaleString()}</p>
                      <button className="rounded-lg bg-primary-100 p-2 text-primary-600 hover:bg-primary-200 transition">
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

      {/* CTA Section */}
      <div className="border-t border-gray-200 bg-gradient-to-r from-primary-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="rounded-xl bg-white shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900">Ready to accept payments?</h2>
            <p className="mt-2 text-gray-600">Connect your bank account to start receiving payments via Squad</p>
            <button
              onClick={() => navigate('/account-connect')}
              className="mt-6 btn-primary inline-flex items-center gap-2"
            >
              <ArrowRight className="h-4 w-4" />
              Connect Account
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
