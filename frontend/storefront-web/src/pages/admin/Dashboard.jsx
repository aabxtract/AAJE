import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Copy,
  Eye,
  MessageCircle,
  Package,
  Plus,
  ShoppingBag,
  Sparkles,
  Wallet,
  CheckCircle2,
  Loader2,
} from 'lucide-react'
import { useDashboard, useOwnerStore } from '../../hooks/useStorefront'
import { formatCurrency, formatDate } from '../../lib/utils'
import { connectWhatsapp } from '../../lib/api'
import AdminLayout from '../../components/AdminLayout'

export default function Dashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('aaje_user') || '{}'))
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, orders, stats, intelligence } = useDashboard(store?.id)
  const [connecting, setConnecting] = useState(false)

  async function handleConnectWhatsapp() {
    setConnecting(true)
    try {
      const response = await connectWhatsapp({ whatsapp_no: user.phone || user.whatsapp_no })
      const updatedUser = response.data.user
      localStorage.setItem('aaje_user', JSON.stringify(updatedUser))
      setUser(updatedUser)
      alert('WhatsApp connected successfully!')
    } catch (err) {
      console.error('WhatsApp connection error:', err)
      alert('Failed to connect WhatsApp. Please try again.')
    } finally {
      setConnecting(false)
    }
  }

  async function copyStoreLink() {
    if (!store?.slug) return
    await navigator.clipboard.writeText(`${window.location.origin}/store/${store.slug}`)
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
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4 text-center">
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm max-w-md">
          <h1 className="text-2xl font-bold text-gray-900">Create your store</h1>
          <p className="mt-2 text-sm text-gray-500">Your account is ready. Generate a storefront to start selling.</p>
          <button onClick={() => navigate('/admin/store-setup')} className="mt-6 inline-flex items-center justify-center gap-2 rounded-md bg-[#0f172a] px-6 py-3 text-sm font-bold text-white transition hover:bg-emerald-700">
            <Plus className="h-4 w-4" />
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
    <AdminLayout store={store} user={user}>
      <div className="space-y-8">
        {/* Banner Section */}
        <section className="rounded-xl bg-[#0f172a] p-6 text-white shadow-lg overflow-hidden relative">
          <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-400">
                <Sparkles className="h-3 w-3" />
                Store is live
              </div>
              <h1 className="mt-3 text-3xl font-bold tracking-tight">aaje.store/{store.slug}</h1>
              <p className="mt-2 max-w-xl text-sm text-gray-400 leading-relaxed">
                Your storefront is active. Share this link on WhatsApp or social media to start receiving orders instantly.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={copyStoreLink}
                className="inline-flex items-center gap-2 rounded-md bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
              >
                <Copy className="h-4 w-4" />
                Copy Link
              </button>
              <button
                onClick={() => navigate('/admin/products')}
                className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2.5 text-sm font-bold text-[#0f172a] transition hover:bg-emerald-50"
              >
                <Plus className="h-4 w-4" />
                Add Product
              </button>
            </div>
          </div>
          {/* Abstract background shapes */}
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl"></div>
          <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-blue-500/10 blur-2xl"></div>
        </section>

        {/* Metrics Grid */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Today's Sales" value={formatCurrency(stats.todaySales)} icon={Wallet} color="emerald" />
          <Metric label="Total Revenue" value={formatCurrency(totalRevenue)} icon={BarChart3} color="blue" />
          <Metric label="Orders" value={String(orders.length)} icon={ShoppingBag} color="purple" />
          <Metric label="Low Stock" value={String(lowStockCount)} icon={Package} color="orange" />
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column: Recent Orders & Inventory */}
          <div className="space-y-6 lg:col-span-2">
            {/* Recent Orders */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
                  <p className="text-xs text-gray-500">Your latest customer transactions</p>
                </div>
                <button onClick={() => navigate('/admin/orders')} className="text-sm font-semibold text-emerald-700 hover:underline">View all</button>
              </div>
              
              {orders.length ? (
                <div className="divide-y divide-gray-100">
                  {orders.slice(0, 5).map((order) => (
                    <div key={order.id} className="flex items-center justify-between py-4 transition hover:bg-gray-50/50 px-2 rounded-md -mx-2">
                      <div className="flex items-center gap-3">
                        <div className="grid h-9 w-9 place-items-center rounded-full bg-gray-100 text-gray-600 font-bold text-xs uppercase">
                          {order.customer_name?.charAt(0) || 'G'}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{order.customer_name || 'Guest customer'}</p>
                          <p className="text-xs text-gray-500">{formatDate(order.created_at)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-gray-900">{formatCurrency(order.total_amount)}</p>
                        <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          order.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'
                        }`}>
                          {order.payment_status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-gray-50 text-gray-400 mb-3">
                    <ShoppingBag className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-medium text-gray-900">No orders yet</p>
                  <p className="text-xs text-gray-500 mt-1">Share your store link to start selling.</p>
                </div>
              )}
            </div>

            {/* Inventory Overview */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Inventory Status</h2>
                  <p className="text-xs text-gray-500">Stock levels and product overview</p>
                </div>
                <button onClick={() => navigate('/admin/inventory')} className="text-sm font-semibold text-emerald-700 hover:underline">Manage stock</button>
              </div>
              
              {products.length ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  {products.slice(0, 6).map((product) => (
                    <div key={product.id} className="flex items-center justify-between rounded-lg border border-gray-100 p-4 transition hover:border-emerald-100 hover:bg-emerald-50/20">
                      <div>
                        <p className="font-semibold text-gray-900">{product.name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{formatCurrency(product.price)}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-bold ${product.stock_quantity < 5 ? 'text-orange-600' : 'text-gray-900'}`}>
                          {product.stock_quantity}
                        </p>
                        <p className="text-[10px] text-gray-400 uppercase font-bold">Qty</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-gray-50 text-gray-400 mb-3">
                    <Package className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-medium text-gray-900">No products yet</p>
                  <button onClick={() => navigate('/admin/products')} className="mt-3 text-xs font-bold text-emerald-700">Add first product</button>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: AI Insights & Social */}
          <aside className="space-y-6">
            {/* WhatsApp Connection */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="flex items-center gap-2 font-bold text-gray-900">
                  <MessageCircle className="h-5 w-5 text-emerald-600" />
                  WhatsApp
                </h2>
                {user.whatsapp_connected && <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                {user.whatsapp_connected 
                  ? 'Your account is connected to WhatsApp. You will receive sales updates and bot notifications.' 
                  : 'Connect your WhatsApp number to receive instant sales updates and manage your store via the bot.'}
              </p>
              
              <div className="mt-4 p-3 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-between">
                <span className="font-mono text-sm font-semibold text-gray-700">{user.whatsapp_no || user.phone || 'No number'}</span>
                {!user.whatsapp_connected && (
                  <button 
                    onClick={handleConnectWhatsapp}
                    disabled={connecting}
                    className="text-xs font-bold text-emerald-700 hover:text-emerald-800 disabled:opacity-50"
                  >
                    {connecting ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Connect'}
                  </button>
                )}
              </div>

              {!user.whatsapp_connected && (
                <button 
                  onClick={handleConnectWhatsapp}
                  disabled={connecting}
                  className="mt-4 w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 text-sm font-bold text-white transition hover:bg-emerald-700 disabled:opacity-50 shadow-md"
                >
                  {connecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageCircle className="h-4 w-4" />}
                  Connect WhatsApp Bot
                </button>
              )}
            </div>

            {/* AI Insights */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm relative overflow-hidden">
              <div className="relative z-10">
                <h2 className="flex items-center gap-2 font-bold text-gray-900 mb-4">
                  <Sparkles className="h-5 w-5 text-blue-600" />
                  AI Intelligence
                </h2>
                <div className="p-4 rounded-lg bg-blue-50/50 border border-blue-100/50">
                  <p className="text-sm text-gray-700 leading-relaxed font-medium italic">
                    "{intelligence.recommendation || intelligence.summary || "You're off to a great start! Share your store link on WhatsApp groups to drive your first sales."}"
                  </p>
                </div>
              </div>
              <div className="absolute -right-6 -bottom-6 h-24 w-24 bg-blue-500/5 rounded-full blur-xl"></div>
            </div>

            {/* BizPrint Score */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="font-bold text-gray-900 mb-4">BizPrint Scoring</h2>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-4xl font-black text-[#0f172a]">B+</span>
                <span className="text-xs font-bold text-emerald-600 mb-1 uppercase tracking-wider">Building</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
                <div className="bg-emerald-500 h-2 rounded-full w-[65%]"></div>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                Your score improves with consistent order fulfillment, inventory accuracy, and positive customer interactions.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </AdminLayout>
  )
}

function Metric({ label, value, icon: Icon, color }) {
  const colors = {
    emerald: 'bg-emerald-50 text-emerald-700',
    blue: 'bg-blue-50 text-blue-700',
    purple: 'bg-purple-50 text-purple-700',
    orange: 'bg-orange-50 text-orange-700',
  }
  
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="mt-2 text-2xl font-black text-[#0f172a]">{value}</p>
        </div>
        <div className={`grid h-12 w-12 place-items-center rounded-xl ${colors[color] || colors.emerald}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}
