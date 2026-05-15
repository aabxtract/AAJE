import { Link } from 'react-router-dom'
import { ShoppingBag, Loader2 } from 'lucide-react'
import OrderTable from '../../components/OrderTable'
import { updateOrderStatus } from '../../lib/api'
import { useOrders, useOwnerStore } from '../../hooks/useStorefront'
import AdminLayout from '../../components/AdminLayout'

export default function Orders() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { orders, loading, refresh } = useOrders(store?.id)
  const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')

  async function updateStatus(orderId, status) {
    try {
      await updateOrderStatus(orderId, { status })
      refresh()
    } catch (err) {
      console.error('Failed to update order status:', err)
      alert('Failed to update status.')
    }
  }

  async function simulatePayment(order) {
    try {
      await updateOrderStatus(order.id, { status: 'paid', payment_status: 'paid', simulate_payment: true })
      refresh()
    } catch (err) {
      console.error('Failed to simulate payment:', err)
      alert('Failed to simulate payment.')
    }
  }

  if (storeLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm text-center">
          <h2 className="text-xl font-bold">No store found</h2>
          <p className="mt-2 text-gray-500">Create your store first to view orders.</p>
          <Link className="mt-4 inline-flex items-center justify-center rounded-md bg-[#0f172a] px-6 py-2 text-sm font-bold text-white transition hover:bg-emerald-700" to="/admin/store-setup">
            Go to Store Setup
          </Link>
        </div>
      </main>
    )
  }

  return (
    <AdminLayout store={store} user={user}>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-black text-[#0f172a]">Orders</h1>
          <p className="text-sm text-gray-500">
            {orders.filter((order) => order.order_status === 'pending').length} pending customer orders
          </p>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-300" />
          </div>
        ) : orders.length > 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
            <OrderTable orders={orders} onUpdateStatus={updateStatus} onSimulatePayment={simulatePayment} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-white py-20 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-full bg-gray-50 text-gray-400 mb-4">
              <ShoppingBag className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">No orders yet</h3>
            <p className="mt-2 max-w-xs text-sm text-gray-500">
              When customers buy from your store link, their orders will appear here for processing.
            </p>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
