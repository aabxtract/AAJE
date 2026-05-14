import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, MessageCircle, ShoppingBag } from 'lucide-react'
import CheckoutForm from '../../components/CheckoutForm'
import ProductCard from '../../components/ProductCard'
import StoreHeader from '../../components/StoreHeader'
import { createOrder, getProductsByStore, getStoreBySlug, initiatePayment } from '../../lib/api'

export default function StorePage() {
  const { slug } = useParams()
  const [store, setStore] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [category, setCategory] = useState('all')
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

  const categories = useMemo(() => ['all', ...new Set(products.map((product) => product.category).filter(Boolean))], [products])
  const visible = category === 'all' ? products : products.filter((product) => product.category === category)

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

  if (loading) return <main className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary-600" /></main>
  if (!store) return <main className="flex min-h-screen items-center justify-center text-center"><div><h1 className="text-2xl font-bold">Store not found</h1><p className="text-gray-500">This storefront is not available.</p></div></main>
  if (selected) return <CheckoutForm product={selected} store={store} loading={checkoutLoading} onCancel={() => setSelected(null)} onSubmit={checkout} />

  const whatsapp = (store.contact_whatsapp || '').replace(/\D/g, '')

  return (
    <div className="min-h-screen bg-gray-50">
      <StoreHeader store={store} onShare={share} />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {categories.length > 1 && (
          <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
            {categories.map((item) => <button key={item} className={`rounded-full px-4 py-2 text-sm font-semibold ${category === item ? 'bg-primary-600 text-white' : 'border bg-white text-gray-700'}`} onClick={() => setCategory(item)}>{item === 'all' ? 'All Products' : item}</button>)}
          </div>
        )}
        {visible.length ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {visible.map((product) => <ProductCard key={product.id} product={product} onSelect={setSelected} />)}
          </div>
        ) : (
          <div className="py-20 text-center text-gray-500"><ShoppingBag className="mx-auto mb-3 h-12 w-12 text-gray-300" />No products available yet.</div>
        )}
      </main>
      {whatsapp && <a href={`https://wa.me/${whatsapp}`} target="_blank" rel="noreferrer" className="fixed bottom-5 right-5 inline-flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-lg"><MessageCircle className="h-5 w-5" />WhatsApp</a>}
    </div>
  )
}
