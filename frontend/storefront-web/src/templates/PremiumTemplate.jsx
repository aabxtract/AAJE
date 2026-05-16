import { useMemo, useState, useEffect } from 'react'
import { 
  MessageCircle, 
  Share2, 
  ShoppingBag, 
  Search, 
  Filter, 
  ChevronRight, 
  Star, 
  Heart,
  ArrowRight,
  Info,
  X,
  Menu
} from 'lucide-react'

export default function PremiumStorefront({ config, products, onSelect, onShare }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('All')
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Sync scroll for sticky header effects
  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const categories = useMemo(() => {
    const cats = ['All', ...(config.categories || [])]
    return [...new Set(cats)]
  }, [config.categories])

  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           p.description?.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesCategory = activeCategory === 'All' || p.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [products, searchQuery, activeCategory])

  const themeColor = config.theme_color || '#0f172a' // Default Navy

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 selection:bg-emerald-100 selection:text-emerald-900">
      {/* Dynamic Header */}
      <header className={`fixed top-0 z-[100] w-full transition-all duration-300 ${
        isScrolled ? 'bg-white/80 backdrop-blur-lg shadow-sm py-3' : 'bg-transparent py-5'
      }`}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 className={`text-xl font-black tracking-tighter transition-colors ${
                isScrolled ? 'text-slate-900' : 'text-white drop-shadow-sm'
              }`}>
                {config.store_name?.toUpperCase() || 'AAJE STORE'}
              </h1>
              <nav className="hidden md:flex items-center gap-6">
                {categories.slice(0, 5).map(cat => (
                  <button 
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    className={`text-sm font-bold transition-all hover:opacity-100 ${
                      activeCategory === cat ? 'opacity-100' : 'opacity-60'
                    } ${isScrolled ? 'text-slate-700' : 'text-white'}`}
                  >
                    {cat}
                  </button>
                ))}
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative hidden sm:block">
                <Search className={`absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 ${
                  isScrolled ? 'text-slate-400' : 'text-white/60'
                }`} />
                <input 
                  type="text" 
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-48 lg:w-64 rounded-full py-2 pl-9 pr-4 text-sm outline-none transition-all ${
                    isScrolled 
                      ? 'bg-slate-100 focus:bg-white focus:ring-2 focus:ring-emerald-500/20' 
                      : 'bg-white/10 backdrop-blur-md text-white placeholder:text-white/60 focus:bg-white/20'
                  }`}
                />
              </div>
              <button 
                onClick={onShare}
                className={`p-2 rounded-full transition-all ${
                  isScrolled ? 'bg-slate-100 text-slate-600' : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                <Share2 className="h-4.5 w-4.5" />
              </button>
              <button className="md:hidden p-2 text-white" onClick={() => setMobileMenuOpen(true)}>
                <Menu className={`h-6 w-6 ${isScrolled ? 'text-slate-900' : 'text-white'}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative h-[60vh] min-h-[500px] w-full overflow-hidden bg-slate-900">
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-r from-slate-900 via-slate-900/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
          <img 
            src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&q=80&w=2000" 
            alt="Hero Background" 
            className="h-full w-full object-cover opacity-50"
          />
        </div>

        <div className="relative z-10 mx-auto flex h-full max-w-7xl flex-col justify-center px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl animate-in fade-in slide-in-from-left-8 duration-1000">
            <span className="inline-block rounded-full bg-emerald-500 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-white mb-6">
              Official Storefront
            </span>
            <h2 className="text-4xl font-black text-white sm:text-6xl lg:text-7xl leading-[1.1]">
              {config.store_name}
            </h2>
            <p className="mt-6 text-lg text-slate-300 leading-relaxed max-w-lg">
              {config.tagline || 'Experience the future of commerce. Handpicked quality items curated just for you.'}
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <a 
                href="#products" 
                className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-white px-8 text-sm font-bold text-slate-900 transition-all hover:scale-105 active:scale-95"
              >
                Shop Collection
                <ArrowRight className="h-4 w-4" />
              </a>
              {config.contact_whatsapp && (
                <a 
                  href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
                  target="_blank"
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-emerald-600 px-8 text-sm font-bold text-white transition-all hover:bg-emerald-700"
                >
                  <MessageCircle className="h-4.5 w-4.5" />
                  Chat with Us
                </a>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main id="products" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-12 lg:flex-row">
          {/* Filter Sidebar */}
          <aside className="hidden w-64 shrink-0 lg:block">
            <div className="sticky top-24 space-y-10">
              <div>
                <h4 className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 mb-5">
                  <Filter className="h-3.5 w-3.5" /> Categories
                </h4>
                <div className="space-y-2">
                  {categories.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setActiveCategory(cat)}
                      className={`flex w-full items-center justify-between rounded-lg px-4 py-2.5 text-sm font-bold transition-all ${
                        activeCategory === cat 
                          ? 'bg-emerald-50 text-emerald-700 shadow-sm' 
                          : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      {cat}
                      {activeCategory === cat && <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl bg-emerald-600 p-6 text-white overflow-hidden relative">
                <div className="relative z-10">
                  <h4 className="font-bold mb-2">Need help?</h4>
                  <p className="text-xs opacity-80 mb-4">Our AI assistant is ready to help you find what you need.</p>
                  <button className="w-full rounded-lg bg-white py-2 text-xs font-bold text-emerald-700">Open Chat</button>
                </div>
                <Sparkles className="absolute -right-4 -bottom-4 h-20 w-20 text-white/10" />
              </div>
            </div>
          </aside>

          {/* Product Grid Area */}
          <div className="flex-1">
            <div className="mb-8 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">
                {activeCategory} <span className="ml-2 text-sm font-medium text-slate-400">{filteredProducts.length} items</span>
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400">Sort:</span>
                <select className="bg-transparent text-xs font-bold text-slate-900 outline-none">
                  <option>Newest First</option>
                  <option>Price: Low to High</option>
                  <option>Price: High to Low</option>
                </select>
              </div>
            </div>

            {filteredProducts.length > 0 ? (
              <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 xl:grid-cols-3">
                {filteredProducts.map((product, i) => (
                  <article 
                    key={product.id || i}
                    onClick={() => onSelect?.(product)}
                    className="group cursor-pointer flex flex-col"
                  >
                    <div className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-slate-100 mb-4">
                      {product.image_url ? (
                        <img 
                          src={product.image_url} 
                          alt={product.name} 
                          className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center">
                          <ShoppingBag className="h-12 w-12 text-slate-200" />
                        </div>
                      )}
                      
                      {/* Hover Actions */}
                      <div className="absolute inset-x-4 bottom-4 flex translate-y-4 gap-2 opacity-0 transition-all group-hover:translate-y-0 group-hover:opacity-100">
                        <button className="flex-1 rounded-xl bg-white py-3 text-xs font-bold text-slate-900 shadow-xl transition hover:bg-slate-50">
                          Add to Cart
                        </button>
                        <button className="grid h-10 w-10 place-items-center rounded-xl bg-white text-slate-400 shadow-xl transition hover:text-emerald-500">
                          <Heart className="h-4 w-4" />
                        </button>
                      </div>

                      {product.type === 'service' && (
                        <span className="absolute left-3 top-3 rounded-full bg-slate-900/80 backdrop-blur-md px-3 py-1 text-[10px] font-black uppercase text-white">
                          Professional Service
                        </span>
                      )}
                      {i < 3 && (
                        <span className="absolute right-3 top-3 rounded-full bg-emerald-500 px-3 py-1 text-[10px] font-black uppercase text-white">
                          New Arrival
                        </span>
                      )}
                    </div>

                    <div className="px-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-[10px] font-black uppercase tracking-widest text-emerald-600">{product.category}</p>
                        <div className="flex items-center gap-1 text-[10px] font-bold text-amber-500">
                          <Star className="h-3 w-3 fill-current" />
                          4.8
                        </div>
                      </div>
                      <h4 className="text-base font-bold text-slate-900 group-hover:text-emerald-600 transition-colors truncate">
                        {product.name}
                      </h4>
                      <p className="mt-1 line-clamp-2 text-xs text-slate-500 leading-relaxed h-8">
                        {product.description || 'No description provided.'}
                      </p>
                      <div className="mt-4 flex items-center justify-between">
                        <p className="text-lg font-black text-slate-900">
                          ₦{Number(product.price || 0).toLocaleString()}
                        </p>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${
                          product.stock_quantity < 5 ? 'text-orange-500' : 'text-slate-400'
                        }`}>
                          {product.type === 'service' ? 'Booking' : `${product.stock_quantity || 0} in stock`}
                        </span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="grid h-20 w-20 place-items-center rounded-full bg-slate-50 text-slate-200 mb-4">
                  <Search className="h-10 w-10" />
                </div>
                <h4 className="text-lg font-bold text-slate-900">No products found</h4>
                <p className="text-sm text-slate-500 mt-1 max-w-xs">
                  We couldn't find any products matching your current search or category filter.
                </p>
                <button 
                  onClick={() => { setSearchQuery(''); setActiveCategory('All'); }}
                  className="mt-6 text-sm font-bold text-emerald-600 underline"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Trust Badges Section */}
      <section className="bg-white border-t border-slate-100 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { title: 'Secure Payment', body: 'Fully encrypted and powered by Squad API', icon: ShoppingBag },
              { title: 'Verified Seller', body: 'BizPrint verified identity and operations', icon: Info },
              { title: 'Fast Fulfillment', body: 'Prompt processing on all confirmed orders', icon: ArrowRight },
              { title: 'Direct Support', body: 'Chat directly with us via WhatsApp bot', icon: MessageCircle },
            ].map(badge => (
              <div key={badge.title} className="text-center md:text-left">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-slate-50 text-emerald-600">
                  <badge.icon className="h-6 w-6" />
                </div>
                <h5 className="font-bold text-slate-900 mb-1">{badge.title}</h5>
                <p className="text-xs text-slate-500 leading-relaxed">{badge.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-10">
            <div>
              <h2 className="text-2xl font-black tracking-tighter mb-4">{config.store_name}</h2>
              <p className="text-sm text-slate-400 max-w-xs leading-relaxed">
                Powered by AAJE. Helping modern merchants build high-performance storefronts with AI intelligence.
              </p>
            </div>
            <div className="flex items-center gap-4">
              {config.contact_whatsapp && (
                <a href={`https://wa.me/${config.contact_whatsapp}`} className="h-10 w-10 grid place-items-center rounded-full bg-white/10 hover:bg-white/20 transition-all">
                  <MessageCircle className="h-5 w-5" />
                </a>
              )}
              <button onClick={onShare} className="h-10 w-10 grid place-items-center rounded-full bg-white/10 hover:bg-white/20 transition-all">
                <Share2 className="h-5 w-5" />
              </button>
            </div>
          </div>
          <div className="mt-20 pt-8 border-t border-white/5 text-center">
            <p className="text-xs text-slate-500 font-medium">
              &copy; {new Date().getFullYear()} {config.store_name}. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Mobile Menu Sidebar */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-[200] lg:hidden">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="fixed inset-y-0 right-0 w-full max-w-xs bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-10">
              <h3 className="font-black">MENU</h3>
              <button onClick={() => setMobileMenuOpen(false)}><X /></button>
            </div>
            <div className="space-y-6">
              <div className="space-y-4">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Categories</p>
                {categories.map(cat => (
                  <button 
                    key={cat} 
                    onClick={() => { setActiveCategory(cat); setMobileMenuOpen(false); }}
                    className="block text-xl font-bold text-slate-900"
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      {config.contact_whatsapp && (
        <a
          href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
          target="_blank"
          rel="noreferrer"
          className="fixed bottom-6 right-6 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-2xl transition-all hover:scale-110 hover:bg-emerald-700 active:scale-95 group"
        >
          <MessageCircle className="h-6 w-6" />
          <span className="absolute right-full mr-3 whitespace-nowrap rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white opacity-0 transition-opacity group-hover:opacity-100">
            Chat with us
          </span>
        </a>
      )}
    </div>
  )
}
