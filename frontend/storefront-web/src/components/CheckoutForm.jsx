import { useState } from 'react'
import { ArrowLeft, CreditCard, Loader2 } from 'lucide-react'
import { formatCurrency } from '../lib/utils'

export default function CheckoutForm({ product, store, loading, onCancel, onSubmit }) {
  const [form, setForm] = useState({ customer_name: '', customer_phone: '', quantity: 1 })
  const total = Number(product.price || 0) * Number(form.quantity)

  function submit(event) {
    event.preventDefault()
    onSubmit({ ...form, product_id: product.id, quantity: Number(form.quantity), total_amount: total })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
          <button className="rounded p-2 hover:bg-gray-100" onClick={onCancel}><ArrowLeft className="h-5 w-5" /></button>
          <h1 className="font-bold">Checkout</h1>
        </div>
      </header>
      <main className="mx-auto max-w-2xl space-y-5 px-4 py-6">
        <div className="card flex gap-4 p-4">
          {product.image_url && <img src={product.image_url} alt={product.name} className="h-20 w-20 rounded-lg object-cover" />}
          <div>
            <h2 className="font-bold">{product.name}</h2>
            <p className="text-sm text-gray-500">{store.store_name}</p>
            <p className="mt-1 font-bold text-primary-700">{formatCurrency(product.price)}</p>
          </div>
        </div>
        <form className="card space-y-4 p-5" onSubmit={submit}>
          <label className="text-sm font-medium">Name<input required className="input-field mt-1" value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} /></label>
          <label className="text-sm font-medium">Phone<input required className="input-field mt-1" value={form.customer_phone} onChange={(e) => setForm({ ...form, customer_phone: e.target.value })} /></label>
          <label className="text-sm font-medium">Quantity<input required min="1" max={product.stock_quantity} type="number" className="input-field mt-1" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} /></label>
          {store.pickup_delivery_note && <p className="rounded-md bg-blue-50 p-3 text-sm text-blue-800">{store.pickup_delivery_note}</p>}
          <div className="flex items-center justify-between border-t pt-4 text-lg font-bold"><span>Total</span><span>{formatCurrency(total)}</span></div>
          <button className="btn-primary w-full py-3" disabled={loading || Number(form.quantity) > Number(product.stock_quantity)}>
            {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <CreditCard className="mr-2 h-5 w-5" />}
            Pay {formatCurrency(total)}
          </button>
        </form>
      </main>
    </div>
  )
}
