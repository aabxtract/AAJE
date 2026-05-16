import { useMemo, useState } from 'react'
import { BadgeCheck, CreditCard, MessageCircle, PackageCheck, Search, Share2, ShoppingBag, Sparkles, Truck, Zap } from 'lucide-react'

const THEMES = {
  gadgets: {
    bg: '#050816',
    surface: '#0c1224',
    panel: '#111a30',
    text: '#f8fbff',
    muted: '#9fb0ca',
    accent: '#077ef6',
    accent2: '#39d5ff',
    line: '#23314d',
  },
  fashion: {
    bg: '#fff7f4',
    surface: '#ffffff',
    panel: '#fff0ea',
    text: '#17121f',
    muted: '#766a74',
    accent: '#df4f6f',
    accent2: '#ff9d66',
    line: '#ead8d5',
  },
  food: {
    bg: '#f8fbf2',
    surface: '#ffffff',
    panel: '#edf7df',
    text: '#132015',
    muted: '#60705a',
    accent: '#159947',
    accent2: '#f4a51c',
    line: '#dce8d1',
  },
  creator: {
    bg: '#f7f3ff',
    surface: '#ffffff',
    panel: '#eee7ff',
    text: '#151127',
    muted: '#706884',
    accent: '#6352e8',
    accent2: '#20b8c7',
    line: '#ded6f1',
  },
}

const LAYOUT_LABELS = {
  catalog_powerhouse: 'Smart catalog layout',
  premium_showroom: 'Premium showroom layout',
  deal_stack: 'Fast deal layout',
  service_booking: 'Booking-first layout',
  local_market: 'Local market layout',
}

function formatCurrency(value) {
  return `NGN ${Number(value || 0).toLocaleString()}`
}

export default function MegaStoreTemplate({ config, products, onSelect, onShare }) {
  const theme = THEMES[config.template] || THEMES.fashion
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const items = products?.length ? products : config.products || []
  const cats = useMemo(() => ['all', ...(config.categories || [])], [config.categories])
  const visible = items.filter((product) => {
    const matchesCategory = category === 'all' || product.category === category
    const haystack = `${product.name || ''} ${product.category || ''} ${product.description || ''}`.toLowerCase()
    return matchesCategory && haystack.includes(query.toLowerCase())
  })
  const featured = visible.slice(0, 3)
  const heroImage = config.display_image_url || config.hero_image_url
  const layoutLabel = LAYOUT_LABELS[config.layout] || 'AI-selected layout'

  return (
    <div className="min-h-screen" style={{ background: theme.bg, color: theme.text }}>
      <header className="border-b" style={{ borderColor: theme.line }}>
        <div className="mx-auto grid min-h-[82vh] max-w-7xl gap-10 px-4 py-8 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
          <div className="flex flex-col justify-between">
            <nav className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                {config.logo_url ? (
                  <img src={config.logo_url} alt={config.store_name} className="h-11 w-11 rounded-[8px] object-cover" />
                ) : (
                  <div className="grid h-11 w-11 place-items-center rounded-[8px] font-black text-white" style={{ background: theme.accent }}>
                    {(config.store_name || 'A').charAt(0)}
                  </div>
                )}
                <div>
                  <p className="text-sm font-black">{config.store_name}</p>
                  <p className="text-xs" style={{ color: theme.muted }}>{layoutLabel}</p>
                </div>
              </div>
              {onShare && (
                <button onClick={onShare} className="grid h-10 w-10 place-items-center rounded-[8px] border" style={{ borderColor: theme.line }}>
                  <Share2 className="h-4 w-4" />
                </button>
              )}
            </nav>

            <section className="py-12 lg:py-16">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-black uppercase tracking-wide" style={{ borderColor: theme.line, color: theme.accent2 }}>
                <Sparkles className="h-3.5 w-3.5" />
                {config.business_focus || config.template} storefront
              </div>
              <h1 className="max-w-3xl text-5xl font-black leading-[1.02] sm:text-6xl lg:text-7xl">
                {config.store_name}
              </h1>
              <p className="mt-5 max-w-2xl text-lg font-semibold" style={{ color: theme.accent2 }}>
                {config.tagline || 'Built for fast checkout and repeat customers.'}
              </p>
              <p className="mt-5 max-w-2xl text-sm leading-7" style={{ color: theme.muted }}>
                {config.description}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a href="#products" className="inline-flex h-12 items-center gap-2 rounded-[8px] px-5 text-sm font-black text-white" style={{ background: theme.accent }}>
                  <ShoppingBag className="h-4 w-4" />
                  Shop catalog
                </a>
                {config.contact_whatsapp && (
                  <a href={`https://wa.me/${String(config.contact_whatsapp).replace(/\D/g, '')}`} className="inline-flex h-12 items-center gap-2 rounded-[8px] border px-5 text-sm font-bold" style={{ borderColor: theme.line }}>
                    <MessageCircle className="h-4 w-4" />
                    WhatsApp seller
                  </a>
                )}
              </div>
            </section>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ['Squad payments', CreditCard],
                ['Stock tracked', PackageCheck],
                ['WhatsApp ready', MessageCircle],
              ].map(([label, Icon]) => (
                <div key={label} className="flex items-center gap-3 rounded-[8px] border p-3" style={{ borderColor: theme.line, background: theme.surface }}>
                  <Icon className="h-4 w-4" style={{ color: theme.accent }} />
                  <span className="text-xs font-bold" style={{ color: theme.muted }}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          <aside className="flex items-center">
            <div className="w-full overflow-hidden rounded-[18px] border" style={{ borderColor: theme.line, background: theme.surface }}>
              <div className="aspect-[4/3] overflow-hidden" style={{ background: theme.panel }}>
                {heroImage ? (
                  <img src={heroImage} alt={config.store_name} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full flex-col justify-between p-8">
                    <div className="inline-flex w-fit items-center gap-2 rounded-full px-4 py-2 text-xs font-black text-white" style={{ background: theme.accent }}>
                      <Zap className="h-3 w-3" />
                      Add display photo
                    </div>
                    <div>
                      <p className="text-3xl font-black">Hero media space</p>
                      <p className="mt-2 max-w-sm text-sm leading-6" style={{ color: theme.muted }}>
                        Add a shop display, product stack, logo, or campaign image from the dashboard.
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-3 border-t text-center" style={{ borderColor: theme.line }}>
                {(config.categories || []).slice(0, 3).map((cat) => (
                  <div key={cat} className="border-r p-4 last:border-r-0" style={{ borderColor: theme.line }}>
                    <p className="text-xs font-black uppercase" style={{ color: theme.accent }}>{cat}</p>
                    <p className="mt-1 text-[11px]" style={{ color: theme.muted }}>Ready to order</p>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </header>

      <section className="border-b" style={{ borderColor: theme.line, background: theme.surface }}>
        <div className="mx-auto flex max-w-7xl gap-3 overflow-x-auto px-4 py-4 sm:px-6 lg:px-8">
          {cats.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className="flex-shrink-0 rounded-full px-5 py-2 text-sm font-black"
              style={{
                background: category === cat ? theme.accent : theme.panel,
                color: category === cat ? '#fff' : theme.text,
              }}
            >
              {cat === 'all' ? 'All products' : cat}
            </button>
          ))}
        </div>
      </section>

      <main id="products" className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="grid gap-6 lg:grid-cols-[0.78fr_1.22fr]">
          <div>
            <p className="text-xs font-black uppercase tracking-wide" style={{ color: theme.accent }}>AI recommendations</p>
            <h2 className="mt-2 text-3xl font-black">Built around what your customers buy.</h2>
            <div className="mt-5 space-y-3">
              {(config.ai_suggestions || []).slice(0, 3).map((item) => (
                <div key={item} className="flex gap-3 rounded-[8px] border p-4" style={{ borderColor: theme.line, background: theme.surface }}>
                  <BadgeCheck className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: theme.accent }} />
                  <p className="text-sm leading-6" style={{ color: theme.muted }}>{item}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {featured.map((product) => (
              <ProductCard key={product.id || product.name} product={product} theme={theme} onSelect={onSelect} compact />
            ))}
          </div>
        </section>

        <section className="mt-12">
          <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-black uppercase tracking-wide" style={{ color: theme.accent }}>Catalog</p>
              <h2 className="mt-1 text-3xl font-black">Products customers can order now</h2>
            </div>
            <label className="flex h-12 min-w-0 items-center gap-3 rounded-[8px] border px-4 sm:w-80" style={{ borderColor: theme.line, background: theme.surface }}>
              <Search className="h-4 w-4" style={{ color: theme.muted }} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search products" className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
            </label>
          </div>

          {visible.length ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {visible.map((product) => (
                <ProductCard key={product.id || product.name} product={product} theme={theme} onSelect={onSelect} />
              ))}
            </div>
          ) : (
            <div className="rounded-[12px] border p-10 text-center" style={{ borderColor: theme.line, background: theme.surface }}>
              <ShoppingBag className="mx-auto h-10 w-10" style={{ color: theme.muted }} />
              <p className="mt-3 font-black">No matching products</p>
            </div>
          )}
        </section>
      </main>

      <footer className="border-t" style={{ borderColor: theme.line, background: theme.surface }}>
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-8 sm:grid-cols-3 sm:px-6 lg:px-8">
          {[
            ['Verified checkout', 'Accept Squad-powered payments with a clear order record.', CreditCard],
            ['Delivery ready', 'Show pickup, delivery, and WhatsApp confirmation details.', Truck],
            ['Managed inventory', 'Stock updates after successful paid orders.', PackageCheck],
          ].map(([title, text, Icon]) => (
            <div key={title} className="rounded-[8px] border p-5" style={{ borderColor: theme.line }}>
              <Icon className="h-5 w-5" style={{ color: theme.accent }} />
              <h3 className="mt-3 font-black">{title}</h3>
              <p className="mt-2 text-sm leading-6" style={{ color: theme.muted }}>{text}</p>
            </div>
          ))}
        </div>
      </footer>
    </div>
  )
}

function ProductCard({ product, theme, onSelect, compact = false }) {
  return (
    <article
      onClick={() => onSelect?.(product)}
      className="group cursor-pointer overflow-hidden rounded-[12px] border transition hover:-translate-y-1"
      style={{ borderColor: theme.line, background: theme.surface }}
    >
      <div className={compact ? 'aspect-[4/3]' : 'aspect-square'} style={{ background: theme.panel }}>
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition group-hover:scale-105" />
        ) : (
          <div className="flex h-full items-center justify-center">
            <ShoppingBag className="h-12 w-12 opacity-30" style={{ color: theme.accent }} />
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="text-xs font-black uppercase" style={{ color: theme.accent }}>{product.category || 'Product'}</p>
        <h3 className="mt-1 font-black">{product.name}</h3>
        {!compact && <p className="mt-2 line-clamp-2 text-sm leading-6" style={{ color: theme.muted }}>{product.description}</p>}
        <div className="mt-4 flex items-center justify-between gap-3">
          <span className="font-black" style={{ color: theme.accent }}>{formatCurrency(product.price)}</span>
          <span className="text-xs font-bold" style={{ color: theme.muted }}>
            {product.type === 'service' ? 'Book' : `${product.stock_quantity || 0} left`}
          </span>
        </div>
      </div>
    </article>
  )
}
