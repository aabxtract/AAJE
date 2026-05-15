import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Eye,
  Home,
  LogOut,
  Package,
  Settings,
  ShoppingBag,
  Menu,
  X,
  MessageCircle,
} from 'lucide-react'
import { useState } from 'react'

export default function AdminLayout({ children, store, user }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const navItems = [
    { label: 'Dashboard', path: '/admin/dashboard', icon: Home },
    { label: 'Products', path: '/admin/products', icon: Package },
    { label: 'Orders', path: '/admin/orders', icon: ShoppingBag },
    { label: 'Inventory', path: '/admin/inventory', icon: BarChart3 },
    { label: 'Store Setup', path: '/admin/store-setup', icon: Settings },
  ]

  function handleLogout() {
    localStorage.removeItem('aaje_user')
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-gray-200 bg-white lg:flex">
        <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-6">
          <div className="grid h-8 w-8 place-items-center rounded-md bg-[#0f172a] text-xs font-black text-white">A</div>
          <span className="font-bold text-gray-900">AAJE Admin</span>
        </div>
        
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <item.icon className={`h-4 w-4 ${isActive ? 'text-emerald-700' : 'text-gray-400'}`} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-gray-200 p-4">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-red-50 hover:text-red-700"
          >
            <LogOut className="h-4 w-4 text-gray-400" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 sm:px-6 lg:px-8">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-gray-900">{store?.store_name || 'My Store'}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              onClick={() => window.open(`/store/${store?.slug}`, '_blank')}
              className="inline-flex items-center gap-2 rounded-md bg-[#0f172a] px-3 py-1.5 text-xs font-bold text-white transition hover:bg-emerald-700"
            >
              <Eye className="h-3.5 w-3.5" />
              Live Store
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          {children}
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity" onClick={() => setIsMobileMenuOpen(false)}></div>
          <div className="fixed inset-y-0 left-0 flex w-full max-w-xs flex-col bg-white">
            <div className="flex h-16 items-center justify-between border-b border-gray-200 px-6">
              <div className="flex items-center gap-3">
                <div className="grid h-8 w-8 place-items-center rounded-md bg-[#0f172a] text-xs font-black text-white">A</div>
                <span className="font-bold text-gray-900">AAJE Admin</span>
              </div>
              <button onClick={() => setIsMobileMenuOpen(false)} className="rounded-md p-2 text-gray-400 hover:bg-gray-100">
                <X className="h-6 w-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium ${
                      isActive ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
            <div className="border-t border-gray-200 p-4">
              <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-600">
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
