import { CheckCircle, Clock, Package, XCircle } from 'lucide-react'
import { formatCurrency, formatDate, statusClass } from '../lib/utils'

export default function OrderTable({ orders, onUpdateStatus, onSimulatePayment }) {
  if (!orders.length) {
    return <div className="card p-10 text-center text-gray-500"><Package className="mx-auto mb-2 h-10 w-10 text-gray-300" />No orders yet.</div>
  }

  return (
    <div className="card overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
          <tr><th className="px-4 py-3">Order</th><th className="px-4 py-3">Customer</th><th className="px-4 py-3 text-right">Amount</th><th className="px-4 py-3">Payment</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Actions</th></tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {orders.map((order) => {
            const PaidIcon = order.payment_status === 'paid' ? CheckCircle : order.payment_status === 'failed' ? XCircle : Clock
            return (
              <tr key={order.id}>
                <td className="px-4 py-3"><span className="font-mono font-medium">#{String(order.id).slice(-6).toUpperCase()}</span><p className="text-xs text-gray-500">{formatDate(order.created_at)}</p></td>
                <td className="px-4 py-3">{order.customer_name}<p className="text-xs text-gray-500">{order.customer_phone}</p></td>
                <td className="px-4 py-3 text-right font-bold">{formatCurrency(order.total_amount)}</td>
                <td className="px-4 py-3"><span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${statusClass(order.payment_status)}`}><PaidIcon className="h-3 w-3" />{order.payment_status}</span></td>
                <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${statusClass(order.order_status)}`}>{order.order_status}</span></td>
                <td className="px-4 py-3 text-right">
                  {order.payment_status === 'pending' && <button className="btn-secondary mr-2 px-3 py-1.5" onClick={() => onSimulatePayment?.(order)}>Mark paid</button>}
                  {onUpdateStatus && (
                    <select className="input-field inline-block w-32" value={order.order_status} onChange={(e) => onUpdateStatus(order.id, e.target.value)}>
                      {['pending', 'paid', 'cancelled', 'fulfilled'].map((status) => <option key={status}>{status}</option>)}
                    </select>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
