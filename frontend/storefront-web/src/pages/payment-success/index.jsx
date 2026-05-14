import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { CheckCircle, Loader2, ShoppingBag } from 'lucide-react'
import { getOrderDetail, updateOrderStatus } from '../../lib/api'
import { formatCurrency } from '../../lib/utils'

export default function PaymentSuccess() {
  const location = useLocation()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)

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
      const res = await getOrderDetail(orderId)
      setOrder(res.data)
      setLoading(false)
    }
    load()
  }, [location.search])

  if (loading) return <main className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary-600" /></main>

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <div className="card w-full max-w-md p-8 text-center">
        <CheckCircle className="mx-auto h-16 w-16 text-emerald-600" />
        <h1 className="mt-4 text-2xl font-bold">Payment Successful</h1>
        <p className="mt-2 text-sm text-gray-500">Your order has been confirmed.</p>
        {order && (
          <div className="mt-6 space-y-2 rounded-lg bg-gray-50 p-4 text-left text-sm">
            <p><span className="text-gray-500">Order:</span> #{String(order.id).slice(-6).toUpperCase()}</p>
            <p><span className="text-gray-500">Customer:</span> {order.customer_name}</p>
            <p><span className="text-gray-500">Amount:</span> <strong>{formatCurrency(order.total_amount)}</strong></p>
          </div>
        )}
        <Link className="btn-primary mt-6" to={order?.store_slug ? `/store/${order.store_slug}` : '/'}>
          <ShoppingBag className="mr-2 h-4 w-4" />
          Continue
        </Link>
      </div>
    </main>
  )
}
