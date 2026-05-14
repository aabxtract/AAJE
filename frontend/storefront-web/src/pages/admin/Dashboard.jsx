import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  TrendingUp,
  Package,
  ShoppingBag,
  Wallet,
  MessageCircle,
  Settings,
  LogOut,
  Zap,
  Eye,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')
  const [timeframe, setTimeframe] = useState('7d')

  // Mock data
  const stats = {
    todaySales: 125000,
    todayOrders: 3,
    totalSales: 1250000,
    totalOrders: 42,
    products: 12,
    lowStock: 2,
    conversionRate: 3.2,
    avgOrderValue: 29761,
  }

  const recentOrders = [
    { id: 1, customer: 'Adekunle O.', amount: 45000, status: 'completed', date: '2 hours ago' },
    { id: 2, customer: 'Zainab M.', amount: 32000, status: 'pending', date: '5 hours ago' },
    { id: 3, customer: 'Chidi E.', amount: 67500, status: 'completed', date: '1 day ago' },
    { id: 4, customer: 'Bolanle A.', amount: 23000, status: 'completed', date: '2 days ago' },
    { id: 5, customer: 'Tunde R.', amount: 15000, status: 'pending', date: '2 days ago' },
  ]

  const topProducts = [
    { name: 'Premium Sneakers', sales: 28, revenue: 420000 },
    { name: 'Leather Bag', sales: 16, revenue: 240000 },
    { name: 'Designer Belt', sales: 12, revenue: 180000 },
  ]

  function handleLogout() {
    localStorage.removeItem('aaje_user')
    navigate('/signup')
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary-600 to-primary-700">
                <span className="text-sm font-bold text-white">AAJE</span>
              </div>
              <div>
                <p className="text-xs text-gray-500">Welcome back</p>
                <p className="font-semibold text-gray-900">My Store</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => window.open('/store/my-store', '_blank')}
                className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
              >
                <Eye className="h-4 w-4" />
                View Store
              </button>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Welcome section */}
        <div className="mb-8 rounded-2xl bg-gradient-to-r from-primary-600 to-primary-700 p-8 text-white shadow-lg">
          <div className="max-w-2xl">
            <h1 className="text-3xl font-bold">Good to see you!</h1>
            <p className="mt-2 text-primary-100">Here's a summary of your store's performance.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/admin/products')}
                className="inline-flex items-center gap-2 rounded-lg bg-white/20 px-4 py-2 font-semibold hover:bg-white/30 transition backdrop-blur-sm"
              >
                <Plus className="h-4 w-4" />
                Add Product
              </button>
              <button className="inline-flex items-center gap-2 rounded-lg bg-white/20 px-4 py-2 font-semibold hover:bg-white/30 transition backdrop-blur-sm">
                <MessageCircle className="h-4 w-4" />
                View on WhatsApp
              </button>
            </div>
          </div>
        </div>

        {/* Stats cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              label: "Today's Sales",
              value: `₦${stats.todaySales.toLocaleString()}`,
              icon: Wallet,
              color: 'emerald',
              trend: '+12%',
            },
            {
              label: 'Total Orders',
              value: stats.totalOrders.toString(),
              icon: ShoppingBag,
              color: 'blue',
              trend: '+5 this week',
            },
            {
              label: 'Products',
              value: stats.products.toString(),
              icon: Package,
              color: 'purple',
              subtext: `${stats.lowStock} low stock`,
            },
            {
              label: 'Avg Order Value',
              value: `₦${stats.avgOrderValue.toLocaleString()}`,
              icon: TrendingUp,
              color: 'orange',
              trend: '+8%',
            },
          ].map((card, idx) => (
            <div key={idx} className="rounded-xl bg-white p-6 shadow-sm hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{card.label}</p>
                  <p className="mt-2 text-2xl font-bold text-gray-900">{card.value}</p>
                  {card.trend && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-emerald-600">
                      <ArrowUpRight className="h-3 w-3" />
                      {card.trend}
                    </p>
                  )}
                  {card.subtext && <p className="mt-1 text-xs text-gray-500">{card.subtext}</p>}
                </div>
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-${card.color}-100`}>
                  <card.icon className={`h-6 w-6 text-${card.color}-600`} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left section - Charts & Analysis */}
          <div className="space-y-6 lg:col-span-2">
            {/* Sales Chart Placeholder */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                  <BarChart3 className="h-5 w-5 text-primary-600" />
                  Sales Overview
                </h2>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700"
                >
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="90d">Last 90 days</option>
                </select>
              </div>
              <div className="h-64 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <BarChart3 className="mx-auto h-12 w-12 text-gray-300 mb-2" />
                  <p className="text-sm text-gray-500">Chart visualization coming soon</p>
                </div>
              </div>
            </div>

            {/* Recent Orders */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                  <ShoppingBag className="h-5 w-5 text-primary-600" />
                  Recent Orders
                </h2>
                <button
                  onClick={() => navigate('/admin/orders')}
                  className="text-sm font-semibold text-primary-600 hover:text-primary-700"
                >
                  View All →
                </button>
              </div>

              <div className="divide-y divide-gray-100">
                {recentOrders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between py-4">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{order.customer}</p>
                      <p className="text-xs text-gray-500">{order.date}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">₦{order.amount.toLocaleString()}</p>
                      <span
                        className={`mt-1 inline-block rounded-full px-2 py-1 text-xs font-medium ${
                          order.status === 'completed'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}
                      >
                        {order.status === 'completed' ? 'Completed' : 'Pending'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right sidebar */}
          <div className="space-y-6">
            {/* Top Products */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h2 className="flex items-center gap-2 font-bold text-gray-900 mb-4">
                <Zap className="h-5 w-5 text-primary-600" />
                Top Products
              </h2>
              <div className="space-y-3">
                {topProducts.map((product, idx) => (
                  <div key={idx} className="rounded-lg border border-gray-100 p-3 hover:border-primary-200 hover:bg-primary-50 transition">
                    <p className="font-medium text-gray-900 text-sm">{product.name}</p>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-gray-600">{product.sales} sales</span>
                      <span className="font-semibold text-gray-900">₦{(product.revenue / 1000).toLocaleString()}k</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Insight */}
            <div className="rounded-xl bg-gradient-to-br from-primary-50 to-primary-100 border border-primary-200 p-6">
              <div className="flex items-start gap-3 mb-3">
                <div className="rounded-lg bg-primary-600 p-2 mt-1">
                  <Zap className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">AI Insight</p>
                  <p className="text-xs text-primary-700">Smart recommendation</p>
                </div>
              </div>
              <p className="text-sm text-gray-700">
                Your <strong>Premium Sneakers</strong> are trending! Consider restocking to avoid stockouts.
              </p>
            </div>

            {/* Quick Links */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h3 className="font-bold text-gray-900 mb-3">Quick Links</h3>
              <div className="space-y-2">
                {[
                  { label: 'Manage Products', icon: Package, href: '/admin/products' },
                  { label: 'View Orders', icon: ShoppingBag, href: '/admin/orders' },
                  { label: 'Inventory', icon: Package, href: '/admin/inventory' },
                  { label: 'Settings', icon: Settings, href: '#' },
                ].map((link, idx) => (
                  <button
                    key={idx}
                    onClick={() => link.href !== '#' && navigate(link.href)}
                    className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
                  >
                    <link.icon className="h-4 w-4" />
                    {link.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
