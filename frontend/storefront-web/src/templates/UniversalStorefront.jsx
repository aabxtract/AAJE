import { useMemo, useState, useEffect } from 'react'
import { 
  MessageCircle, Share2, ShoppingBag, Search, Heart, Star,
  ArrowRight, Menu, X, Filter, ChevronDown, ShieldCheck, 
  Truck, Clock, Headphones
} from 'lucide-react'
import { getTemplate } from './templateRegistry'

/**
 * UniversalStorefront — A single, high-quality renderer for ALL template types.
 * Reads theme/layout from templateRegistry and adapts visuals accordingly.
 */
export default function UniversalStorefront({ config, products, onSelect, onShare }) {
  const templateConfig = getTemplate(config.template)
  const T = templateConfig.theme
  const L = templateConfig.layout

  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('All')
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [sortBy, setSortBy] = useState('default')

  useEffect(() => {
    const h = () => setIsScrolled(window.scrollY > 40)
    window.addEventListener('scroll', h)
    return () => window.removeEventListener('scroll', h)
  }, [])

  const categories = useMemo(() => {
    const cats = ['All', ...(config.categories || [])]
    return [...new Set(cats)]
  }, [config.categories])

  const filteredProducts = useMemo(() => {
    let result = (products || []).filter(p => {
      const matchesSearch = !searchQuery || 
        p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description?.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesCat = activeCategory === 'All' || p.category === activeCategory
      return matchesSearch && matchesCat
    })

    if (sortBy === 'price-low') result.sort((a, b) => (a.price || 0) - (b.price || 0))
    if (sortBy === 'price-high') result.sort((a, b) => (b.price || 0) - (a.price || 0))
    if (sortBy === 'name') result.sort((a, b) => (a.name || '').localeCompare(b.name || ''))

    return result
  }, [products, searchQuery, activeCategory, sortBy])

  const isDark = T.bg.startsWith('#0') || T.bg.startsWith('#1')

  return (
    <div className="min-h-screen" style={{ background: T.bg, color: T.text }}>
      {/* ─── STICKY HEADER ─── */}
      <header 
        className="fixed top-0 z-[100] w-full transition-all duration-300"
        style={{ 
          background: isScrolled ? (isDark ? 'rgba(9,9,11,0.92)' : 'rgba(255,255,255,0.92)') : 'transparent',
          backdropFilter: isScrolled ? 'blur(20px)' : 'none',
          borderBottom: isScrolled ? `1px solid ${T.border}` : 'none',
          padding: isScrolled ? '12px 0' : '20px 0',
        }}
      >
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="text-lg font-black tracking-tight" style={{ 
              color: isScrolled ? T.text : '#ffffff',
              textShadow: isScrolled ? 'none' : '0 1px 3px rgba(0,0,0,0.3)',
            }}>
              {config.store_name?.toUpperCase()}
            </h1>
            <nav className="hidden md:flex items-center gap-1">
              {categories.slice(0, 5).map(cat => (
                <button 
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className="px-3 py-1.5 rounded-full text-xs font-bold transition-all"
                  style={{
                    background: activeCategory === cat ? T.accent : 'transparent',
                    color: activeCategory === cat ? '#fff' : (isScrolled ? T.muted : 'rgba(255,255,255,0.7)'),
                  }}
                >
                  {cat}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-2">
            {L.hasSearch && (
              <div className="relative hidden sm:block">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5" style={{ color: isScrolled ? T.muted : 'rgba(255,255,255,0.5)' }} />
                <input 
                  type="text" placeholder="Search..."
                  value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  className="w-44 lg:w-56 rounded-full py-2 pl-9 pr-4 text-xs outline-none transition-all"
                  style={{
                    background: isScrolled ? (isDark ? T.card : '#f1f5f9') : 'rgba(255,255,255,0.12)',
                    color: isScrolled ? T.text : '#fff',
                    border: 'none',
                  }}
                />
              </div>
            )}
            <button onClick={onShare} className="p-2 rounded-full transition-all" style={{ 
              background: isScrolled ? (isDark ? T.card : '#f1f5f9') : 'rgba(255,255,255,0.12)',
              color: isScrolled ? T.muted : '#fff',
            }}>
              <Share2 className="h-4 w-4" />
            </button>
            <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(true)}>
              <Menu className="h-5 w-5" style={{ color: isScrolled ? T.text : '#fff' }} />
            </button>
          </div>
        </div>
      </header>

      {/* ─── HERO ─── */}
      <section className="relative w-full overflow-hidden" style={{
        background: T.hero,
        minHeight: L.heroStyle === 'full-bleed' ? '70vh' : L.heroStyle === 'editorial' ? '65vh' : '55vh',
      }}>
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent z-10" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent z-10" />
          {/* Decorative shapes */}
          <div className="absolute -right-20 -top-20 h-96 w-96 rounded-full opacity-20 blur-3xl" style={{ background: T.accent }} />
          <div className="absolute -left-10 bottom-0 h-60 w-60 rounded-full opacity-10 blur-2xl" style={{ background: T.accent }} />
        </div>

        <div className="relative z-20 mx-auto flex h-full max-w-7xl flex-col justify-end px-4 sm:px-6 lg:px-8 pb-16 pt-32" style={{ minHeight: 'inherit' }}>
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-white mb-6" style={{ background: T.accent }}>
              <ShieldCheck className="h-3 w-3" />
              {templateConfig.name}
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white leading-[1.1] tracking-tight">
              {config.store_name}
            </h2>
            <p className="mt-5 text-base sm:text-lg text-white/70 leading-relaxed max-w-lg">
              {config.tagline || config.description || 'Quality products and services, curated just for you.'}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#products" className="inline-flex h-12 items-center gap-2 rounded-full bg-white px-7 text-sm font-bold transition-all hover:scale-105 active:scale-95" style={{ color: T.text }}>
                Shop Now <ArrowRight className="h-4 w-4" />
              </a>
              {config.contact_whatsapp && (
                <a href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
                  target="_blank" rel="noreferrer"
                  className="inline-flex h-12 items-center gap-2 rounded-full px-7 text-sm font-bold text-white border border-white/20 transition-all hover:bg-white/10">
                  <MessageCircle className="h-4 w-4" /> Chat with Us
                </a>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ─── PRODUCTS SECTION ─── */}
      <main id="products" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between mb-10">
          <div>
            <h3 className="text-2xl font-black" style={{ color: T.text }}>
              {activeCategory === 'All' ? 'All Products' : activeCategory}
            </h3>
            <p className="text-sm mt-1" style={{ color: T.muted }}>{filteredProducts.length} items available</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Mobile search */}
            <div className="relative sm:hidden">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5" style={{ color: T.muted }} />
              <input type="text" placeholder="Search..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                className="w-full rounded-lg py-2 pl-9 pr-3 text-xs outline-none" style={{ background: isDark ? T.card : '#f1f5f9', border: `1px solid ${T.border}` }} />
            </div>
            {/* Category pills (mobile) */}
            <div className="flex gap-1 overflow-x-auto md:hidden pb-1">
              {categories.map(cat => (
                <button key={cat} onClick={() => setActiveCategory(cat)}
                  className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-bold"
                  style={{ background: activeCategory === cat ? T.accent : (isDark ? T.card : '#f1f5f9'), color: activeCategory === cat ? '#fff' : T.muted, border: `1px solid ${T.border}` }}>
                  {cat}
                </button>
              ))}
            </div>
            {L.hasSort && (
              <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                className="rounded-lg px-3 py-2 text-xs font-bold outline-none"
                style={{ background: isDark ? T.card : '#f1f5f9', color: T.text, border: `1px solid ${T.border}` }}>
                <option value="default">Default</option>
                <option value="price-low">Price: Low to High</option>
                <option value="price-high">Price: High to Low</option>
                <option value="name">Name A-Z</option>
              </select>
            )}
          </div>
        </div>

        <div className={`flex gap-10 ${L.hasSidebar ? '' : ''}`}>
          {/* Sidebar (desktop) */}
          {L.hasSidebar && (
            <aside className="hidden lg:block w-56 shrink-0">
              <div className="sticky top-24 space-y-8">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest mb-4" style={{ color: T.muted }}>
                    <Filter className="inline h-3 w-3 mr-1" />Categories
                  </p>
                  <div className="space-y-1">
                    {categories.map(cat => (
                      <button key={cat} onClick={() => setActiveCategory(cat)}
                        className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-xs font-bold transition-all"
                        style={{
                          background: activeCategory === cat ? (isDark ? T.card : `${T.accent}10`) : 'transparent',
                          color: activeCategory === cat ? T.accent : T.muted,
                          border: activeCategory === cat ? `1px solid ${T.accent}30` : '1px solid transparent',
                        }}>
                        {cat}
                        {activeCategory === cat && <div className="h-1.5 w-1.5 rounded-full" style={{ background: T.accent }} />}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </aside>
          )}

          {/* Product Grid */}
          <div className="flex-1">
            {filteredProducts.length > 0 ? (
              <div className={`grid gap-x-5 gap-y-8 ${
                L.productGrid === '4-col' ? 'sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' :
                L.productGrid === '3-col' ? 'sm:grid-cols-2 lg:grid-cols-3' :
                'sm:grid-cols-2'
              }`}>
                {filteredProducts.map((product, i) => (
                  <article key={product.id || i} onClick={() => onSelect?.(product)}
                    className="group cursor-pointer flex flex-col rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl"
                    style={{ background: T.card, border: `1px solid ${T.border}` }}>
                    {/* Image */}
                    <div className="relative aspect-square overflow-hidden" style={{ background: isDark ? '#1e1e22' : '#f1f5f9' }}>
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110" />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center">
                          <ShoppingBag className="h-12 w-12" style={{ color: T.border }} />
                        </div>
                      )}

                      {/* Hover overlay */}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300" />

                      {/* Quick actions */}
                      <div className="absolute inset-x-3 bottom-3 flex gap-2 translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
                        <button className="flex-1 rounded-xl py-2.5 text-xs font-bold shadow-lg transition hover:scale-[1.02]"
                          style={{ background: T.accent, color: '#fff' }}>
                          {product.type === 'service' ? 'Book Now' : 'Buy Now'}
                        </button>
                        <button className="grid h-10 w-10 place-items-center rounded-xl shadow-lg" style={{ background: '#fff', color: T.muted }}>
                          <Heart className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Badges */}
                      {product.type === 'service' && (
                        <span className="absolute left-3 top-3 rounded-full px-3 py-1 text-[9px] font-black uppercase tracking-wider text-white" style={{ background: T.accent }}>
                          Service
                        </span>
                      )}
                      {i < 2 && !product.type && (
                        <span className="absolute right-3 top-3 rounded-full px-3 py-1 text-[9px] font-black uppercase tracking-wider text-white bg-amber-500">
                          Hot
                        </span>
                      )}
                    </div>

                    {/* Details */}
                    <div className="p-4 flex-1 flex flex-col">
                      <p className="text-[9px] font-black uppercase tracking-[0.15em] mb-1" style={{ color: T.accent }}>
                        {product.category || 'Uncategorized'}
                      </p>
                      <h4 className="text-sm font-bold leading-snug group-hover:underline decoration-1 underline-offset-2" style={{ color: T.text }}>
                        {product.name}
                      </h4>
                      <p className="mt-1.5 text-[11px] leading-relaxed line-clamp-2 flex-1" style={{ color: T.muted }}>
                        {product.description || 'No description available.'}
                      </p>
                      <div className="mt-3 pt-3 flex items-center justify-between" style={{ borderTop: `1px solid ${T.border}` }}>
                        <p className="text-base font-black" style={{ color: T.text }}>
                          {'\u20A6'}{Number(product.price || 0).toLocaleString()}
                        </p>
                        <div className="flex items-center gap-1">
                          <Star className="h-3 w-3 fill-current text-amber-400" />
                          <span className="text-[10px] font-bold" style={{ color: T.muted }}>
                            {product.stock_quantity > 0 ? `${product.stock_quantity} left` : 'Order'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="h-16 w-16 rounded-full grid place-items-center mb-4" style={{ background: isDark ? T.card : '#f1f5f9' }}>
                  <Search className="h-8 w-8" style={{ color: T.border }} />
                </div>
                <h4 className="text-lg font-bold" style={{ color: T.text }}>No products found</h4>
                <p className="text-sm mt-1 max-w-xs" style={{ color: T.muted }}>
                  Try adjusting your search or category filter.
                </p>
                <button onClick={() => { setSearchQuery(''); setActiveCategory('All') }}
                  className="mt-5 text-sm font-bold underline" style={{ color: T.accent }}>
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ─── TRUST STRIP ─── */}
      <section style={{ background: isDark ? T.card : '#ffffff', borderTop: `1px solid ${T.border}` }} className="py-14">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { icon: ShieldCheck, title: 'Secure Payments', desc: 'Encrypted checkout via Squad' },
            { icon: Truck, title: 'Fast Delivery', desc: 'Quick processing on all orders' },
            { icon: Clock, title: 'Always Open', desc: 'Shop 24/7, anytime anywhere' },
            { icon: Headphones, title: 'Direct Support', desc: 'Chat with us on WhatsApp' },
          ].map(b => (
            <div key={b.title} className="text-center">
              <div className="mx-auto mb-3 h-11 w-11 rounded-xl grid place-items-center" style={{ background: `${T.accent}15`, color: T.accent }}>
                <b.icon className="h-5 w-5" />
              </div>
              <h5 className="text-xs font-black" style={{ color: T.text }}>{b.title}</h5>
              <p className="text-[10px] mt-0.5" style={{ color: T.muted }}>{b.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="py-16" style={{ background: isDark ? '#050505' : '#0f172a', color: '#fff' }}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div>
              <h2 className="text-xl font-black tracking-tight mb-2">{config.store_name}</h2>
              <p className="text-xs text-white/50 max-w-xs leading-relaxed">
                Powered by AAJE — AI-native commerce for modern merchants.
              </p>
            </div>
            <div className="flex gap-3">
              {config.contact_whatsapp && (
                <a href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`} target="_blank" rel="noreferrer"
                  className="h-10 w-10 grid place-items-center rounded-full bg-white/10 hover:bg-white/20 transition">
                  <MessageCircle className="h-4 w-4" />
                </a>
              )}
              <button onClick={onShare} className="h-10 w-10 grid place-items-center rounded-full bg-white/10 hover:bg-white/20 transition">
                <Share2 className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="mt-12 pt-6 border-t border-white/10 text-center">
            <p className="text-[10px] text-white/30">&copy; {new Date().getFullYear()} {config.store_name}. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* ─── MOBILE MENU ─── */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-[200] lg:hidden">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="fixed inset-y-0 right-0 w-full max-w-xs p-6 shadow-2xl" style={{ background: isDark ? T.bg : '#fff' }}>
            <div className="flex items-center justify-between mb-10">
              <h3 className="font-black text-sm" style={{ color: T.text }}>MENU</h3>
              <button onClick={() => setMobileMenuOpen(false)}><X className="h-5 w-5" style={{ color: T.muted }} /></button>
            </div>
            <div className="space-y-2">
              {categories.map(cat => (
                <button key={cat} onClick={() => { setActiveCategory(cat); setMobileMenuOpen(false) }}
                  className="block w-full text-left px-4 py-3 rounded-xl text-sm font-bold transition-all"
                  style={{
                    background: activeCategory === cat ? `${T.accent}15` : 'transparent',
                    color: activeCategory === cat ? T.accent : T.text,
                  }}>
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── WhatsApp FAB ─── */}
      {config.contact_whatsapp && (
        <a href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
          target="_blank" rel="noreferrer"
          className="fixed bottom-6 right-6 z-[90] flex h-14 w-14 items-center justify-center rounded-full text-white shadow-2xl transition-all hover:scale-110 active:scale-95 group"
          style={{ background: '#25D366' }}>
          <MessageCircle className="h-6 w-6" />
        </a>
      )}
    </div>
  )
}
