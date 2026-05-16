import { useState } from 'react'
import { ArrowLeft, CreditCard, Loader2, Lock, ShieldCheck, ShoppingBag } from 'lucide-react'
import { formatCurrency } from '../lib/utils'

const inputClass = 'block w-full rounded-[8px] border border-[#dcd6ea] bg-white px-4 py-3 text-sm font-medium outline-none transition placeholder:text-[#9a94aa] focus:border-[#077ef6] focus:shadow-[0_0_0_3px_rgba(7,126,246,0.12)] hover:border-[#bfb7d1]'

export default function CheckoutForm({ product, store, loading, onCancel, onSubmit }) {
  const [form, setForm] = useState({ customer_name: '', customer_phone: '', quantity: 1 })
  const total = Number(product.price || 0) * Number(form.quantity)

  function submit(event) {
    event.preventDefault()
    onSubmit({ ...form, product_id: product.id, quantity: Number(form.quantity), total_amount: total })
  }

  return (
    <div className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <header className="border-b border-[#eee8f7] bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-4 sm:px-6">
          <button className="grid h-10 w-10 place-items-center rounded-[8px] border border-[#dcd6ea] bg-white text-[#625d75] transition hover:border-[#077ef6] hover:text-[#077ef6]" onClick={onCancel} aria-label="Go back">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-lg font-bold tracking-normal text-[#05051f]">Checkout</h1>
            <p className="text-xs font-medium text-[#77738c]">{store.store_name}</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5 rounded-full bg-[#ecfdf3] px-3 py-1 text-[0.68rem] font-bold uppercase tracking-[0.12em] text-[#027a48]">
            <Lock className="h-3 w-3" /> Secure
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-3xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[8px] border border-[#e3ddec] bg-white p-5 shadow-[0_18px_45px_rgba(35,18,82,0.07)] lg:self-start">
          <div className="flex gap-4">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="h-24 w-24 rounded-[8px] border border-[#eee8f7] object-cover" />
            ) : (
              <div className="grid h-24 w-24 place-items-center rounded-[8px] bg-[#eef6ff] text-[#077ef6]">
                <ShoppingBag className="h-8 w-8" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-[0.68rem] font-bold uppercase tracking-[0.14em] text-[#077ef6]">{product.category || 'Product'}</p>
              <h2 className="mt-1 text-lg font-bold tracking-normal text-[#05051f]">{product.name}</h2>
              <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#625d75]">{product.description}</p>
              <p className="mt-4 text-xl font-bold text-[#030328]">{formatCurrency(product.price)}</p>
            </div>
          </div>
        </div>

        <form className="space-y-5 rounded-[8px] border border-[#e3ddec] bg-white p-6 shadow-[0_18px_45px_rgba(35,18,82,0.07)]" onSubmit={submit}>
          <h3 className="flex items-center gap-2 text-sm font-bold text-[#030328]">
            <CreditCard className="h-4 w-4 text-[#077ef6]" />
            Customer details
          </h3>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-[#030328]">Full name</label>
            <input
              required
              className={inputClass}
              value={form.customer_name}
              onChange={(event) => setForm({ ...form, customer_name: event.target.value })}
              placeholder="e.g. John Doe"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-[#030328]">Phone number</label>
            <input
              required
              className={inputClass}
              value={form.customer_phone}
              onChange={(event) => setForm({ ...form, customer_phone: event.target.value })}
              placeholder="e.g. 08012345678"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-[#030328]">Quantity</label>
            <input
              required
              min="1"
              max={product.stock_quantity}
              type="number"
              className={inputClass}
              value={form.quantity}
              onChange={(event) => setForm({ ...form, quantity: event.target.value })}
            />
            <p className="text-[0.68rem] font-medium text-[#9a94aa]">
              {product.stock_quantity > 0 ? `${product.stock_quantity} available` : 'Limited stock'}
            </p>
          </div>

          {store.pickup_delivery_note && (
            <div className="rounded-[8px] border border-[#bfdbfe] bg-[#eef6ff] p-4 text-sm leading-6 text-[#030328]">
              {store.pickup_delivery_note}
            </div>
          )}

          <div className="flex items-center justify-between border-t border-[#eee8f7] pt-5">
            <span className="text-sm font-bold uppercase tracking-[0.14em] text-[#77738c]">Total</span>
            <span className="text-2xl font-bold text-[#030328]">{formatCurrency(total)}</span>
          </div>

          <button
            type="submit"
            disabled={loading || Number(form.quantity) > Number(product.stock_quantity)}
            className="inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-[#077ef6] px-6 py-4 text-sm font-bold text-white shadow-[0_16px_32px_rgba(7,126,246,0.22)] transition hover:bg-[#0269d2] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <CreditCard className="h-5 w-5" />}
            Pay {formatCurrency(total)}
          </button>

          <div className="flex items-center justify-center gap-4 pt-2">
            <div className="flex items-center gap-1.5 text-[0.68rem] font-semibold text-[#77738c]">
              <ShieldCheck className="h-3.5 w-3.5 text-[#027a48]" /> Encrypted
            </div>
            <div className="flex items-center gap-1.5 text-[0.68rem] font-semibold text-[#77738c]">
              <Lock className="h-3.5 w-3.5 text-[#077ef6]" /> Squad secured
            </div>
          </div>
        </form>
      </main>
    </div>
  )
}
