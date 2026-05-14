import { Link } from 'react-router-dom'
import { AlertTriangle, Package, ShoppingBag, Sparkles, Store, Wallet } from 'lucide-react'
import OrderTable from '../../components/OrderTable'
import StorePreview from '../../components/StorePreview'
import { useDashboard, useOwnerStore } from '../../hooks/useStorefront'
import { formatCurrency } from '../../lib/utils'

export default function Dashboard() {
  const { store, loading } = useOwnerStore()
  const { stats, intelligence, orders } = useDashboard(store?.id)

  if (loading) return <main className="p-8 text-gray-500">Loading dashboard...</main>
  if (!store) return <main className="flex min-h-screen items-center justify-center"><div className="text-center"><Store className="mx-auto mb-3 h-12 w-12 text-gray-300" /><Link className="btn-primary" to="/admin/store-setup">Create Store</Link></div></main>

  const cards = [
    ['Today sales', formatCurrency(stats.todaySales), Wallet],
    ['Total orders', stats.totalOrders, ShoppingBag],
    ['Pending orders', stats.pendingOrders, AlertTriangle],
    ['Products in stock', stats.productsInStock, Package],
  ]

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-2xl font-bold">{store.store_name}</h1><p className="text-sm text-gray-500">Store dashboard</p></div>
        <div className="flex gap-2"><Link className="btn-secondary" to="/admin/inventory">Inventory</Link><Link className="btn-primary" to="/admin/products">Products</Link></div>
      </div>
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value, Icon]) => <div key={label} className="card p-5"><Icon className="mb-3 h-5 w-5 text-primary-600" /><p className="text-sm text-gray-500">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></div>)}
      </div>
      <div className="grid gap-8 lg:grid-cols-3">
        <section className="space-y-6 lg:col-span-2">
          <div className="card p-5">
            <h2 className="flex items-center gap-2 font-bold"><Sparkles className="h-5 w-5 text-primary-600" />AI Store Insight</h2>
            <p className="mt-3 text-gray-700">{intelligence.summary}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-md bg-gray-50 p-3"><p className="text-xs text-gray-500">Top product</p><p className="font-semibold">{intelligence.top_product}</p></div>
              <div className="rounded-md bg-gray-50 p-3"><p className="text-xs text-gray-500">Sales trend</p><p className="font-semibold">{intelligence.sales_trend}</p></div>
              <div className="rounded-md bg-gray-50 p-3"><p className="text-xs text-gray-500">Low stock</p><p className="font-semibold">{intelligence.low_stock?.length || 0}</p></div>
            </div>
            <p className="mt-4 rounded-md bg-primary-50 p-3 text-sm text-primary-900">{intelligence.recommendation}</p>
          </div>
          <div>
            <div className="mb-3 flex items-center justify-between"><h2 className="font-bold">Recent orders</h2><Link className="text-sm font-semibold text-primary-700" to="/admin/orders">View all</Link></div>
            <OrderTable orders={orders.slice(0, 5)} />
          </div>
        </section>
        <aside className="space-y-5">
          <StorePreview store={store} />
          <div className="card p-5">
            <h3 className="font-bold">Quick Actions</h3>
            <div className="mt-3 grid gap-2">
              <Link className="rounded-md p-3 hover:bg-gray-50" to="/admin/products">Add or edit products</Link>
              <Link className="rounded-md p-3 hover:bg-gray-50" to="/admin/orders">Review orders</Link>
              <Link className="rounded-md p-3 hover:bg-gray-50" to="/admin/inventory">Adjust stock</Link>
            </div>
          </div>
        </aside>
      </div>
    </main>
  )
}
