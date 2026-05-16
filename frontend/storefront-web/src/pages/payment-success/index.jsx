import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ArrowRight, Check, CheckCircle, Copy, Loader2, ShoppingBag } from 'lucide-react'
import { getOrderDetail, updateOrderStatus } from '../../lib/api'
import { formatCurrency } from '../../lib/utils'

export default function PaymentSuccess() {
  const location = useLocation()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    async function load() {
      const params = new URLSearchParams(location.search)
      const orderId = params.get('order_id')
      if (!orderId) {
        setLoading(false)
        return
      }
      if (params.get('simulate')) {
        await updateOrderStatus(orderId, { status: 'paid', payment_status: 'paid', simulate_payment: true })
      }
      const response = await getOrderDetail(orderId)
      setOrder(response.data)
      setLoading(false)
    }
    load()
  }, [location.search])

  function copyOrderId() {
    if (!order) return
    navigator.clipboard.writeText(String(order.id).slice(-6).toUpperCase())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#fbf8ff]">
        <Loader2 className="h-8 w-8 animate-spin text-[#077ef6]" />
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#fbf8ff] p-4 text-[#030328]">
      <div className="w-full max-w-md">
        <div className="rounded-[8px] border border-[#e3ddec] bg-white p-8 text-center shadow-[0_24px_70px_rgba(42,25,91,0.1)]">
          <div className="mx-auto mb-6 grid h-20 w-20 place-items-center rounded-[12px] bg-[#ecfdf3] text-[#027a48]">
            <CheckCircle className="h-10 w-10" />
          </div>

          <h1 className="text-2xl font-bold tracking-normal text-[#05051f]">Payment successful</h1>
          <p className="mt-2 text-sm font-medium leading-6 text-[#625d75]">Your order has been confirmed and is being processed.</p>

          {order && (
            <div className="mt-6 space-y-3 rounded-[8px] border border-[#e3ddec] bg-[#fcf9ff] p-5 text-left">
              <div className="flex items-center justify-between">
                <span className="text-[0.68rem] font-bold uppercase tracking-[0.14em] text-[#77738c]">Order ID</span>
                <button onClick={copyOrderId} className="flex items-center gap-1.5 text-xs font-bold text-[#077ef6] transition hover:text-[#0269d2]">
                  #{String(order.id).slice(-6).toUpperCase()}
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                </button>
              </div>
              <div className="border-t border-[#eee8f7]" />
              <Row label="Customer" value={order.customer_name} />
              <Row label="Amount paid" value={formatCurrency(order.total_amount)} strong />
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-[#77738c]">Status</span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#ecfdf3] px-2.5 py-1 text-xs font-semibold text-[#027a48]">
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                  Paid
                </span>
              </div>
            </div>
          )}

          <Link
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-[#077ef6] px-6 py-3.5 text-sm font-bold text-white shadow-[0_16px_32px_rgba(7,126,246,0.22)] transition hover:bg-[#0269d2]"
            to={order?.store_slug ? `/store/${order.store_slug}` : '/'}
          >
            <ShoppingBag className="h-4 w-4" />
            Continue shopping
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <p className="mt-6 text-center text-[0.68rem] font-bold uppercase tracking-[0.14em] text-[#9a94aa]">
          Powered by AAJE and Squad Payments
        </p>
      </div>
    </main>
  )
}

function Row({ label, value, strong = false }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs font-medium text-[#77738c]">{label}</span>
      <span className={`${strong ? 'text-sm font-bold' : 'text-xs font-semibold'} text-[#030328]`}>{value}</span>
    </div>
  )
}
