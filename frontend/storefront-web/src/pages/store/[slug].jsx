import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import StorefrontRenderer from '../../templates/StorefrontRenderer'
import CheckoutForm from '../../components/CheckoutForm'
import { createOrder, getProductsByStore, getStoreBySlug, initiatePayment } from '../../lib/api'

export default function StorePage() {
  const { slug } = useParams()
  const [store, setStore] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [checkoutLoading, setCheckoutLoading] = useState(false)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const storeRes = await getStoreBySlug(slug)
        setStore(storeRes.data)
        const productsRes = await getProductsByStore(storeRes.data.id || slug)
        setProducts((productsRes.data || []).filter((item) => item.is_active !== false))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [slug])

  async function checkout(data) {
    setCheckoutLoading(true)
    try {
      const orderRes = await createOrder({
        store_id: store.id,
        customer_name: data.customer_name,
        customer_phone: data.customer_phone,
        total_amount: data.total_amount,
        items: [{ product_id: data.product_id, quantity: data.quantity, unit_price: selected.price, total_price: data.total_amount }],
      })
      const order = orderRes.data
      try {
        const paymentRes = await initiatePayment({
          user_id: store.user_id,
          store_id: store.id,
          order_id: order.id,
          amount: order.total_amount,
          customer_name: order.customer_name,
          customer_phone: order.customer_phone,
        })
        if (paymentRes.data.payment_link) window.location.href = paymentRes.data.payment_link
        else window.location.href = `/payment-success?order_id=${order.id}&reference=${paymentRes.data.reference || paymentRes.data.payment_reference || ''}&simulate=1`
      } catch {
        window.location.href = `/payment-success?order_id=${order.id}&simulate=1`
      }
    } finally {
      setCheckoutLoading(false)
    }
  }

  async function share() {
    const url = window.location.href
    if (navigator.share) await navigator.share({ title: store.store_name, text: store.description, url })
    else await navigator.clipboard.writeText(url)
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </main>
    )
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center text-center">
        <div>
          <h1 className="text-2xl font-bold">Store not found</h1>
          <p className="text-gray-500">This storefront is not available.</p>
        </div>
      </main>
    )
  }

  // If a product is selected, show the checkout form
  if (selected) {
    return <CheckoutForm product={selected} store={store} loading={checkoutLoading} onCancel={() => setSelected(null)} onSubmit={checkout} />
  }

  // Build the config for the renderer from the store's config_json
  const config = {
    template: store.template || store.config_json?.template || 'fashion',
    theme: store.theme || store.config_json?.theme || 'default',
    store_name: store.store_name,
    tagline: store.tagline || store.config_json?.tagline || '',
    description: store.description || store.config_json?.description || '',
    categories: store.config_json?.categories || [...new Set(products.map((p) => p.category).filter(Boolean))],
    products: store.config_json?.products || [],
    contact_whatsapp: store.contact_whatsapp,
  }

  return (
    <StorefrontRenderer
      config={config}
      products={products}
      onSelect={setSelected}
      onShare={share}
    />
  )
}
