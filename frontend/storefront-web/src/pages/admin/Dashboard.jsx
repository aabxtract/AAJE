import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowUpRight,
  Clock,
  ExternalLink,
  Gauge,
  Loader2,
  MessageCircle,
  Package,
  Plus,
  ShoppingBag,
  Sparkles,
  Zap,
} from 'lucide-react'
import { useDashboard, useOwnerStore } from '../../hooks/useStorefront'
import { formatCurrency } from '../../lib/utils'
import AdminLayout from '../../components/AdminLayout'
import MonoConnectOverlay from '../../components/MonoConnectOverlay'

function DashboardContent({ store, products, orders, navigate }) {
  const paidOrders = orders.filter((order) => order.payment_status === 'paid')
  const totalRevenue = paidOrders.reduce((sum, order) => sum + Number(order.total_amount || 0), 0)
  const todayOrders = orders.filter(order => {
    const orderDate = new Date(order.created_at)
    const today = new Date()
    return orderDate.toDateString() === today.toDateString()
  })
  const lowStockProducts = products.filter(p => (p.stock_quantity || 0) <= 5)

  const activities = useMemo(() => {
    const items = []
    orders.slice(0, 5).forEach(order => {
      items.push({
        type: 'order',
        title: 'New order received',
        detail: `Order #${String(order.id).slice(-6).toUpperCase()} - ${formatCurrency(order.total_amount)}`,
        time: order.created_at,
        icon: ShoppingBag,
        color: 'bg-emerald-500/10 text-emerald-600',
      })
    })
    lowStockProducts.slice(0, 2).forEach(product => {
      items.push({
        type: 'stock',
        title: 'Low stock alert',
        detail: `${product.name} has only ${product.stock_quantity} units left`,
        time: new Date().toISOString(),
        icon: Package,
        color: 'bg-amber-500/10 text-amber-600',
      })
    })
    if (items.length === 0) {
      items.push({
        type: 'system',
        title: 'System ready',
        detail: 'All systems operational',
        time: new Date().toISOString(),
        icon: Zap,
        color: 'bg-[#17124c]/10 text-[#17124c]',
      })
    }
    return items.sort((a, b) => new Date(b.time) - new Date(a.time)).slice(0, 6)
  }, [orders, lowStockProducts])

  return (
    <div className="space-y-6 pb-20 lg:space-y-8 lg:pb-8">
      {/* HERO SECTION */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#17124c] via-[#1e1a5e] to-[#252378] p-6 text-white shadow-2xl shadow-[#17124c]/20 lg:p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHptMCAzMmMtNy43MzIgMC0xNC02LjI2OC0xNC0xNHM2LjI2OC0xNCAxNC0xNCAxNCA2LjI2OCAxNCAxNC02LjI2OCAxNC0xNCAxNHoiIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjAzIi8+PC9nPjwvc3ZnPg==')] opacity-40" />
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex-1">
            <div className="mb-2 flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/80">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                Live Operations
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight lg:text-3xl">{store.store_name}</h1>
            <p className="mt-1 text-sm text-white/60">{store.category || 'Your storefront'}</p>
            
            <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-white/50">Total Sales</p>
                <p className="mt-1 text-xl font-bold">{formatCurrency(totalRevenue)}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-white/50">Today</p>
                <p className="mt-1 text-xl font-bold">{todayOrders.length} orders</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-white/50">BizPrint</p>
                <p className="mt-1 flex items-center gap-1 text-xl font-bold">
                  <Gauge className="h-4 w-4 text-amber-400" /> 78
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-white/50">Products</p>
                <p className="mt-1 text-xl font-bold">{products.length} items</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button onClick={() => navigate('/admin/products')} className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition hover:bg-white/20">
              <Plus className="h-4 w-4" />
              Add Product
            </button>
            <button onClick={() => store?.slug && window.open(`/store/${store.slug}`, '_blank')} className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition hover:bg-white/20">
              <ExternalLink className="h-4 w-4" />
              View Store
            </button>
            <button onClick={() => navigate('/admin/orders')} className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition hover:bg-white/20">
              <ShoppingBag className="h-4 w-4" />
              Orders
            </button>
          </div>
        </div>
      </section>

      {/* QUICK METRICS */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-[#e3ddec] bg-white p-4 shadow-md shadow-[#17124c]/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#77738c]">Revenue</p>
          <p className="mt-3 text-xl font-bold text-[#17124c]">{formatCurrency(totalRevenue)}</p>
          <p className="mt-2 text-xs font-semibold text-emerald-600">+12%</p>
        </div>
        <div className="rounded-2xl border border-[#e3ddec] bg-white p-4 shadow-md shadow-[#17124c]/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#77738c]">Orders</p>
          <p className="mt-3 text-xl font-bold text-[#17124c]">{orders.length}</p>
          <p className="mt-2 text-xs font-semibold text-emerald-600">+4%</p>
        </div>
        <div className="rounded-2xl border border-[#e3ddec] bg-white p-4 shadow-md shadow-[#17124c]/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#77738c]">Inventory</p>
          <p className="mt-3 text-xl font-bold text-[#17124c]">{lowStockProducts.length > 0 ? `${lowStockProducts.length} low` : 'Healthy'}</p>
          <p className="mt-2 text-xs font-semibold text-amber-600">{lowStockProducts.length > 0 ? 'Needs attention' : 'OK'}</p>
        </div>
        <div className="rounded-2xl border border-[#e3ddec] bg-white p-4 shadow-md shadow-[#17124c]/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#77738c]">Reach</p>
          <p className="mt-3 text-xl font-bold text-[#17124c]">1.2k</p>
          <p className="mt-2 text-xs font-semibold text-emerald-600">+18%</p>
        </div>
      </section>

      {/* OPERATIONAL FEED */}
      <section className="rounded-2xl border border-white/10 bg-white/60 p-6 shadow-xl shadow-[#17124c]/5 backdrop-blur-sm">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#17124c]">Business Activity</h2>
            <p className="text-sm text-[#625d75]">Recent events and operations</p>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-medium text-[#625d75]">
            <Clock className="h-3.5 w-3.5" /> Real-time
          </span>
        </div>
        <div className="space-y-3">
          {activities.map((activity, index) => (
            <div key={index} className="flex items-center gap-4 rounded-xl bg-[#fbf8ff] p-4 transition hover:bg-[#f5f0fc]">
              <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${activity.color}`}>
                <activity.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-[#17124c]">{activity.title}</p>
                <p className="truncate text-sm text-[#625d75]">{activity.detail}</p>
              </div>
              <span className="shrink-0 text-xs text-[#9a94aa]">
                {new Date(activity.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* WHATSAPP OPS */}
      <section className="rounded-2xl border border-[#e3ddec] bg-white p-6 shadow-lg shadow-[#17124c]/5">
        <div className="mb-5 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#25D366]/10 text-[#25D366]">
            <MessageCircle className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#17124c]">WhatsApp Operations</h2>
            <p className="text-sm text-[#625d75]">Conversational commerce center</p>
          </div>
        </div>
        <div className="space-y-3">
          <div className="max-w-[85%] rounded-2xl bg-[#f5f0fc] px-4 py-3 text-sm text-[#17124c]">
            Your gadget sales increased 18% this week. Phones and chargers are top sellers.
          </div>
          <div className="max-w-[85%] rounded-2xl bg-[#f5f0fc] px-4 py-3 text-sm text-[#17124c]">
            Low stock alert: 3 products need restocking. Tap to view.
          </div>
        </div>
        <button className="mt-4 w-full rounded-xl border border-[#e3ddec] py-3 text-sm font-semibold text-[#17124c] transition hover:bg-[#fbf8ff]">
          Open WhatsApp Ops
        </button>
      </section>

      {/* AI INSIGHTS */}
      <section className="rounded-2xl border border-[#c4b5fd]/30 bg-gradient-to-br from-[#f5f0fc] to-[#faf7ff] p-6 shadow-lg shadow-[#17124c]/5">
        <div className="mb-4 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[#5a4be7]" />
          <h2 className="text-lg font-bold text-[#17124c]">AI Insights</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-lg bg-white p-3">
            <Zap className="mt-0.5 h-4 w-4 shrink-0 text-[#5a4be7]" />
            <p className="text-sm text-[#17124c]">Your gadget sales increased this week.</p>
          </div>
          <div className="flex items-start gap-3 rounded-lg bg-white p-3">
            <Zap className="mt-0.5 h-4 w-4 shrink-0 text-[#5a4be7]" />
            <p className="text-sm text-[#17124c]">Instagram campaign performed best with 12 conversions.</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  
  // Always call hooks in the same order at the top
  const [user] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('aaje_user') || '{}')
    } catch {
      return {}
    }
  })
  
  const [bankConnected] = useState(() => {
    try {
      const storedUser = JSON.parse(localStorage.getItem('aaje_user') || '{}')
      return !!storedUser.mono_account_id
    } catch {
      return false
    }
  })

  const { store, loading: storeLoading } = useOwnerStore()
  const dashboardData = useDashboard(store?.id || null)
  const products = dashboardData?.products || []
  const orders = dashboardData?.orders || []

  const handleMonoComplete = (data) => {
    const updatedUser = {
      ...user,
      mono_account_id: data.mono_account_id,
      verified_bank_name: data.bank_name,
      verified_bank_account: data.account_number,
      verified_bank_code: data.bank_code,
      full_name: data.account_name || user.full_name,
    }
    localStorage.setItem('aaje_user', JSON.stringify(updatedUser))
    window.location.reload()
  }

  // Loading state - uses conditional rendering
  if (storeLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#fbf8ff]">
        <Loader2 className="h-8 w-8 animate-spin text-[#077ef6]" />
      </div>
    )
  }

  // No store - still in AdminLayout but different content
  if (!store) {
    return (
      <AdminLayout store={null} user={user}>
        <main className="flex min-h-[60vh] items-center justify-center p-4 text-center">
          <div className="max-w-md rounded-2xl border border-[#e3ddec] bg-white p-10 shadow-[0_24px_70px_rgba(42,25,91,0.1)]">
            <div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-xl bg-[#eef6ff] text-[#077ef6]">
              <Plus className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-bold tracking-normal text-[#05051f]">Create your store</h1>
            <p className="mt-3 text-sm leading-6 text-[#625d75]">Your account is ready. Generate a storefront to start selling across Africa.</p>
            <button onClick={() => navigate('/admin/store-setup')} className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#17124c] px-6 py-4 text-sm font-bold text-white shadow-lg shadow-[#17124c]/20 transition hover:bg-[#1a1638]">
              Start setup
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </main>
      </AdminLayout>
    )
  }

  // Bank not connected
  if (!bankConnected) {
    return (
      <AdminLayout store={store} user={user}>
        <MonoConnectOverlay onComplete={handleMonoComplete} />
      </AdminLayout>
    )
  }

  // Main dashboard - show content inside layout
  return (
    <AdminLayout store={store} user={user}>
      <DashboardContent store={store} products={products} orders={orders} navigate={navigate} />
    </AdminLayout>
  )
}