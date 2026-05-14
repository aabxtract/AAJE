import { Link } from 'react-router-dom'
import OrderTable from '../../components/OrderTable'
import { updateOrderStatus } from '../../lib/api'
import { useOrders, useOwnerStore } from '../../hooks/useStorefront'

export default function Orders() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { orders, loading, refresh } = useOrders(store?.id)

  async function updateStatus(orderId, status) {
    await updateOrderStatus(orderId, { status })
    refresh()
  }

  async function simulatePayment(order) {
    await updateOrderStatus(order.id, { status: 'paid', payment_status: 'paid', simulate_payment: true })
    refresh()
  }

  if (storeLoading) return <main className="p-8 text-gray-500">Loading store...</main>
  if (!store) return <main className="flex min-h-screen items-center justify-center"><Link className="btn-primary" to="/admin/store-setup">Create store first</Link></main>

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Orders</h1>
        <p className="text-sm text-gray-500">{orders.filter((order) => order.order_status === 'pending').length} pending orders</p>
      </div>
      {loading ? <p className="text-gray-500">Loading orders...</p> : <OrderTable orders={orders} onUpdateStatus={updateStatus} onSimulatePayment={simulatePayment} />}
    </main>
  )
}
