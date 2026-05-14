import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Copy,
  Eye,
  LogOut,
  MessageCircle,
  Package,
  Plus,
  ShoppingBag,
  Sparkles,
  Wallet,
} from 'lucide-react'
import { useDashboard, useOwnerStore } from '../../hooks/useStorefront'
import { formatCurrency, formatDate } from '../../lib/utils'

export default function Dashboard() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, orders, stats, intelligence } = useDashboard(store?.id)

  function handleLogout() {
    localStorage.removeItem('aaje_user')
    localStorage.removeItem('auth_token')
    navigate('/signup')
  }

  async function copyStoreLink() {
    if (!store?.slug) return
    await navigator.clipboard.writeText(`${window.location.origin}/store/${store.slug}`)
  }

  if (storeLoading) {
    return <main className="flex min-h-screen items-center justify-center text-gray-500">Loading your store...</main>
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4 text-center">
        <div className="card max-w-md p-8">
          <h1 className="text-2xl font-bold text-gray-900">Create your store</h1>
          <p className="mt-2 text-sm text-gray-500">Your account is ready. Generate a storefront to start selling.</p>
          <button onClick={() => navigate('/admin/store-setup')} className="btn-primary mt-6">
            <Plus className="mr-2 h-4 w-4" />
            Create Store
          </button>
        </div>
      </main>
    )
  }

  const paidOrders = orders.filter((order) => order.payment_status === 'paid')
  const totalRevenue = paidOrders.reduce((sum, order) => sum + Number(order.total_amount || 0), 0)
  const lowStockCount = stats.lowStockProducts.length

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#0f172a] text-sm font-black text-white">A</div>
            <div>
              <p className="text-xs text-gray-500">Welcome back, {user.full_name || 'Founder'}</p>
              <p className="font-semibold text-gray-900">{store.store_name}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={() => navigate(`/store/${store.slug}`)} className="btn-secondary hidden sm:inline-flex">
              <Eye className="mr-2 h-4 w-4" />
              View Store
            </button>
            <button onClick={handleLogout} className="btn-ghost">
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="mb-8 rounded-lg bg-[#0f172a] p-6 text-white">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold text-emerald-200">Store link</p>
              <h1 className="mt-2 text-3xl font-bold">aaje.store/{store.slug}</h1>
              <p className="mt-2 max-w-2xl text-sm text-white/70">
                WhatsApp is linked to {user.whatsapp_no || user.phone || 'your signup phone'} so the bot can find this account.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button onClick={copyStoreLink} className="inline-flex items-center gap-2 rounded-md bg-white/10 px-4 py-2 text-sm font-semibold hover:bg-white/20">
                <Copy className="h-4 w-4" />
                Copy Store Link
              </button>
              <button onClick={() => navigate('/admin/products')} className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-semibold text-[#0f172a] hover:bg-emerald-50">
                <Plus className="h-4 w-4" />
                Add Product
              </button>
            </div>
          </div>
        </section>

        <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Today's Sales" value={formatCurrency(stats.todaySales)} icon={Wallet} />
          <Metric label="Total Revenue" value={formatCurrency(totalRevenue)} icon={BarChart3} />
          <Metric label="Orders" value={String(orders.length)} icon={ShoppingBag} />
          <Metric label="Low Stock" value={String(lowStockCount)} icon={Package} />
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <div className="card p-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
                <button onClick={() => navigate('/admin/orders')} className="text-sm font-semibold text-primary-700">View all</button>
              </div>
              {orders.length ? (
                <div className="divide-y divide-gray-100">
                  {orders.slice(0, 5).map((order) => (
                    <div key={order.id} className="flex items-center justify-between py-4">
                      <div>
                        <p className="font-medium text-gray-900">{order.customer_name || 'Guest customer'}</p>
                        <p className="text-xs text-gray-500">{formatDate(order.created_at)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">{formatCurrency(order.total_amount)}</p>
                        <p className="text-xs capitalize text-gray-500">{order.payment_status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-md bg-gray-50 p-4 text-sm text-gray-500">No orders yet. Share your store link to start selling.</p>
              )}
            </div>

            <div className="card p-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-lg font-bold text-gray-900">Products and Stock</h2>
                <button onClick={() => navigate('/admin/inventory')} className="text-sm font-semibold text-primary-700">Inventory</button>
              </div>
              {products.length ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  {products.slice(0, 6).map((product) => (
                    <div key={product.id} className="rounded-md border border-gray-100 p-3">
                      <p className="font-medium text-gray-900">{product.name}</p>
                      <p className="mt-1 text-xs text-gray-500">
                        {product.stock_quantity} in stock - {formatCurrency(product.price)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-md bg-gray-50 p-4 text-sm text-gray-500">No products yet. Add your first product to publish your store.</p>
              )}
            </div>
          </div>

          <aside className="space-y-6">
            <div className="card p-6">
              <h2 className="flex items-center gap-2 font-bold text-gray-900">
                <MessageCircle className="h-5 w-5 text-emerald-700" />
                WhatsApp
              </h2>
              <p className="mt-3 text-sm text-gray-600">
                {user.whatsapp_connected ? 'Connected for store notifications and bot lookup.' : 'Connect WhatsApp to receive sales updates.'}
              </p>
              <p className="mt-2 font-mono text-sm text-gray-900">{user.whatsapp_no || user.phone || 'No number saved'}</p>
            </div>

            <div className="card p-6">
              <h2 className="flex items-center gap-2 font-bold text-gray-900">
                <Sparkles className="h-5 w-5 text-primary-700" />
                AI Insight
              </h2>
              <p className="mt-3 text-sm text-gray-700">{intelligence.recommendation || intelligence.summary}</p>
            </div>

            <div className="card p-6">
              <h2 className="font-bold text-gray-900">BizPrint</h2>
              <p className="mt-3 text-3xl font-bold text-[#0f172a]">Building</p>
              <p className="mt-2 text-sm text-gray-600">Orders, inventory updates, and payment activity will strengthen this profile.</p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}

function Metric({ label, value, icon: Icon }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="grid h-11 w-11 place-items-center rounded-md bg-emerald-50 text-emerald-700">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  )
}
