import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  Bell,
  Bot,
  ChevronDown,
  CreditCard,
  ExternalLink,
  LayoutDashboard,
  LogOut,
  Megaphone,
  MessageCircle,
  MoreHorizontal,
  Package,
  Plus,
  Search,
  Settings,
  ShoppingBag,
  Sparkles,
  Store,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'

const navItemClass = (isActive) => `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 ${
  isActive
    ? 'bg-[#17124c] text-white shadow-lg shadow-[#17124c]/30 border-l-4 border-[#25D366]'
    : 'text-[#625d75] hover:bg-[#f5f0fc] hover:text-[#17124c]'
}`

const mobileNavItemClass = (isActive) => `flex flex-col items-center gap-1 rounded-xl px-3 py-2 transition ${
  isActive 
    ? 'text-[#17124c]' 
    : 'text-[#77738c]'
}`

export default function AdminLayout({ children, store, user }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isCopilotOpen, setIsCopilotOpen] = useState(false)
  const [copilotInput, setCopilotInput] = useState('')
  const [copilotMessages, setCopilotMessages] = useState([
    { role: 'ai', text: "Hi, I'm your AAJE Copilot. Ask me about your dashboard, BizPrint, inventory, or next growth move." },
  ])
  const location = useLocation()
  const navigate = useNavigate()

  const mainNav = [
    { label: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { label: 'Storefront', path: '/admin/dashboard', icon: Store },
    { label: 'Orders', path: '/admin/orders', icon: ShoppingBag },
    { label: 'Products', path: '/admin/products', icon: Package },
    { label: 'Campaigns', path: '/admin/campaigns', icon: Megaphone },
  ]

  const secondaryNav = [
    { label: 'BizPrint', path: '/admin/bizprint', icon: Activity },
    { label: 'WhatsApp Ops', path: '/admin/dashboard', icon: MessageCircle },
    { label: 'Settings', path: '/admin/store-setup', icon: Settings },
  ]

  function handleLogout() {
    localStorage.removeItem('aaje_user')
    localStorage.removeItem('auth_token')
    navigate('/')
  }

  function sendCopilotMessage() {
    if (!copilotInput.trim()) return
    setCopilotMessages((prev) => [
      ...prev,
      { role: 'user', text: copilotInput.trim() },
      { role: 'ai', text: "I'm still learning inside this dashboard. For live operations, message AAJE through WhatsApp for now." },
    ])
    setCopilotInput('')
  }

  function renderNavItem(item) {
    const isActive = location.pathname === item.path || (item.path === '/admin/dashboard' && location.pathname === '/dashboard')
    return (
      <Link key={item.path} to={item.path} className={navItemClass(isActive)}>
        <item.icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-[#77738c]'}`} />
        {item.label}
      </Link>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#faf9fc] font-sans text-[#17124c]">
      {localStorage.getItem('wa_redirect') === 'true' && (
        <div className="relative z-[100] flex items-center justify-center gap-4 border-b border-[#dbeafe] bg-[#17124c] px-4 py-3 text-center text-white">
          <p className="text-sm font-semibold">Account connected. Return to WhatsApp to manage your store.</p>
          <button
            onClick={() => {
              localStorage.removeItem('wa_redirect')
              window.location.href = 'https://wa.me/2348000000000?text=I am connected!'
            }}
            className="rounded-lg bg-white px-4 py-1.5 text-xs font-bold text-[#17124c] transition hover:bg-white/90"
          >
            Open WhatsApp
          </button>
        </div>
      )}

      <div className="flex flex-1">
        {/* DESKTOP SIDEBAR */}
        <aside className="hidden w-64 flex-col bg-gradient-to-b from-[#17124c] via-[#1e1a5e] to-[#252378] lg:flex">
          <div className="flex h-20 items-center justify-center border-b border-white/10 px-4">
            <Link to="/admin/dashboard" className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10">
                <span className="text-lg font-bold text-white">A</span>
              </div>
              <div>
                <p className="text-lg font-bold text-white">AAJE</p>
                <p className="text-[0.65rem] font-medium text-white/50">Commerce OS</p>
              </div>
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-6">
            <div className="mb-6">
              <p className="mb-3 px-3 text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-white/40">Operations</p>
              <nav className="space-y-1">{mainNav.map(renderNavItem)}</nav>
            </div>

            <div>
              <p className="mb-3 px-3 text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-white/40">Tools</p>
              <nav className="space-y-1">{secondaryNav.map(renderNavItem)}</nav>
            </div>
          </div>

          <div className="border-t border-white/10 p-4">
            <div className="mb-3 flex items-center gap-3 rounded-xl bg-white/5 p-3">
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#25D366] to-[#128C7E] text-xs font-bold text-white">
                {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'A'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">{store?.store_name || 'My Store'}</p>
                <p className="truncate text-[0.7rem] text-white/50">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500/20 to-amber-600/20 px-3 py-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span className="text-xs font-medium text-amber-200">Free Plan</span>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-white/70 transition hover:bg-white/5 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </aside>

        {/* MAIN CONTENT AREA */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* TOPBAR */}
          <header className="flex h-16 items-center justify-between border-b border-[#e3ddec]/50 bg-white/80 px-4 backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="grid h-10 w-10 place-items-center rounded-xl border border-[#e3ddec] bg-white text-[#17124c] transition hover:border-[#17124c] lg:hidden"
                aria-label="Open menu"
              >
                <MoreHorizontal className="h-5 w-5" />
              </button>

              {/* Store Selector Chip */}
              <div className="hidden items-center gap-2 rounded-xl bg-[#f5f0fc] px-4 py-2 sm:flex">
                <Store className="h-4 w-4 text-[#17124c]" />
                <span className="text-sm font-semibold text-[#17124c]">{store?.store_name || 'My Store'}</span>
                <ChevronDown className="h-3.5 w-3.5 text-[#77738c]" />
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Today Summary Chip */}
              <div className="hidden items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 text-xs font-medium text-emerald-700 sm:flex">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                3 orders today
              </div>

              <button className="relative grid h-10 w-10 place-items-center rounded-xl border border-[#e3ddec] bg-white text-[#625d75] transition hover:border-[#17124c] hover:text-[#17124c]" aria-label="Notifications">
                <Bell className="h-5 w-5" />
                <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-amber-500" />
              </button>

              <button
                onClick={() => store?.slug && window.open(`/store/${store.slug}`, '_blank')}
                className="hidden items-center gap-2 rounded-xl bg-[#17124c] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#17124c]/20 transition hover:bg-[#1e1a5e] sm:inline-flex"
              >
                View Store
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            </div>
          </header>

          {/* PAGE CONTENT */}
          <div className="flex-1 overflow-y-auto bg-[#faf9fc] p-4 sm:p-6 lg:p-8 pb-24 lg:pb-8">
            {children}
          </div>
        </div>
      </div>

      {/* MOBILE BOTTOM NAVIGATION */}
      <nav className="fixed bottom-0 left-0 right-0 z-[100] flex items-center justify-around border-t border-[#e3ddec] bg-white/95 backdrop-blur-lg px-2 py-2 lg:hidden pb-4">
        <MobileNavItem icon={LayoutDashboard} label="Home" path="/admin/dashboard" />
        <MobileNavItem icon={ShoppingBag} label="Orders" path="/admin/orders" />
        <MobileNavItem icon={Package} label="Products" path="/admin/products" />
        <MobileNavItem icon={MessageCircle} label="WhatsApp" path="/admin/dashboard" />
        <MobileNavItem icon={Settings} label="Settings" path="/admin/store-setup" />
      </nav>

      {/* FLOATING AI COPILOT BUTTON */}
      <div className="fixed bottom-6 right-6 z-[150]">
        {isCopilotOpen ? (
          <div className="mb-4 flex h-[500px] w-[min(380px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-[#e3ddec] bg-white shadow-2xl shadow-[#17124c]/15">
            <div className="flex items-center justify-between border-b border-[#eee8f7] bg-gradient-to-r from-[#17124c] to-[#1e1a5e] px-5 py-4 text-white">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-white">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold">AAJE Copilot</h3>
                  <div className="mt-0.5 flex items-center gap-1.5 text-[0.68rem] text-white/65">
                    <Sparkles className="h-3 w-3" /> AI Assistant
                  </div>
                </div>
              </div>
              <button onClick={() => setIsCopilotOpen(false)} className="grid h-8 w-8 place-items-center rounded-xl text-white/72 transition hover:bg-white/10 hover:text-white" aria-label="Close copilot">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto bg-[#faf9fc] p-5">
              {copilotMessages.map((msg, index) => (
                <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-r from-[#17124c] to-[#1e1a5e] text-white' 
                      : 'border border-[#e3ddec] bg-white text-[#17124c]'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-[#eee8f7] bg-white p-4">
              <div className="flex items-center gap-2 rounded-xl border border-[#e3ddec] bg-[#faf9fc] px-3 py-1.5 transition focus-within:border-[#17124c] focus-within:bg-white focus-within:shadow-md">
                <input
                  type="text"
                  value={copilotInput}
                  onChange={(event) => setCopilotInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') sendCopilotMessage()
                  }}
                  placeholder="Ask me anything..."
                  className="flex-1 bg-transparent py-2 text-sm outline-none placeholder:text-[#9a94aa]"
                />
                <button onClick={sendCopilotMessage} className="grid h-10 w-10 place-items-center rounded-xl bg-[#17124c] text-white transition hover:bg-[#1e1a5e]" aria-label="Send message">
                  <Sparkles className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setIsCopilotOpen(true)}
            className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-[#17124c] to-[#1e1a5e] text-white shadow-xl shadow-[#17124c]/30 transition hover:scale-105 hover:shadow-2xl"
            aria-label="Open AAJE Copilot"
          >
            <Sparkles className="h-6 w-6" />
          </button>
        )}
      </div>

      {/* MOBILE MENU */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-[200] lg:hidden">
          <div className="fixed inset-0 bg-[#17124c]/50 backdrop-blur-sm" onClick={() => setIsMobileMenuOpen(false)} />
          <div className="fixed inset-y-0 left-0 flex w-full max-w-[280px] flex-col bg-gradient-to-b from-[#17124c] to-[#1e1a5e] shadow-2xl">
            <div className="flex h-20 items-center justify-between border-b border-white/10 px-4">
              <Link to="/admin/dashboard" className="flex items-center gap-3" onClick={() => setIsMobileMenuOpen(false)}>
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10">
                  <span className="text-lg font-bold text-white">A</span>
                </div>
                <span className="text-lg font-bold text-white">AAJE</span>
              </Link>
              <button onClick={() => setIsMobileMenuOpen(false)} className="grid h-10 w-10 place-items-center rounded-xl text-white/70 transition hover:bg-white/10 hover:text-white" aria-label="Close menu">
                <X className="h-5 w-5" />
              </button>
            </div>

            <nav className="flex-1 space-y-2 overflow-y-auto p-4">
              <div>
                <p className="mb-3 px-3 text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-white/40">Main</p>
                <div className="space-y-1">{mainNav.map(renderNavItem)}</div>
              </div>
              <div className="mt-6">
                <p className="mb-3 px-3 text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-white/40">Tools</p>
                <div className="space-y-1">{secondaryNav.map(renderNavItem)}</div>
              </div>
            </nav>

            <div className="border-t border-white/10 p-4">
              <button onClick={handleLogout} className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/10 px-3 py-3 text-sm font-medium text-white/70 transition hover:bg-white/5 hover:text-white">
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

function MobileNavItem({ icon: Icon, label, path }) {
  const location = useLocation()
  const isActive = location.pathname === path
  
  return (
    <Link
      to={path}
      className={`flex flex-col items-center gap-1 rounded-xl px-3 py-2 transition ${
        isActive ? 'text-[#17124c]' : 'text-[#77738c]'
      }`}
    >
      <div className={`grid h-8 w-8 place-items-center rounded-lg ${isActive ? 'bg-[#17124c]/10 text-[#17124c]' : 'bg-[#f5f0fc]'}`}>
        <Icon className="h-4 w-4" />
      </div>
      <span className="text-[0.65rem] font-medium">{label}</span>
    </Link>
  )
}