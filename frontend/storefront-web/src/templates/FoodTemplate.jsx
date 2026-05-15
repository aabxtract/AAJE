import { useMemo, useState } from 'react'
import { MessageCircle, Share2, ShoppingBag, Utensils, Clock, Flame } from 'lucide-react'

const THEME = {
  bg: '#fefdf8',
  accent: '#16a34a',
  orange: '#ea580c',
  text: '#1a1a1a',
  muted: '#64748b',
  card: '#ffffff',
  border: '#e2e8d4',
}

export default function FoodTemplate({ config, products, onSelect, onShare }) {
  const [category, setCategory] = useState('all')
  const cats = useMemo(() => ['all', ...(config.categories || [])], [config.categories])
  const items = products || config.products || []
  const visible = category === 'all' ? items : items.filter((p) => p.category === category)

  return (
    <div className="min-h-screen" style={{ background: THEME.bg, color: THEME.text }}>
      {/* Hero */}
      <header className="relative overflow-hidden" style={{ background: `linear-gradient(135deg, ${THEME.accent} 0%, #15803d 100%)` }}>
        <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-20 lg:px-8">
          <div className="max-w-xl text-white">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest backdrop-blur">
              <Utensils className="h-3 w-3" /> Food & Drinks
            </div>
            <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">{config.store_name}</h1>
            {config.tagline && <p className="mt-3 text-lg font-medium opacity-90">{config.tagline}</p>}
            {config.description && <p className="mt-3 text-sm leading-relaxed opacity-75">{config.description}</p>}
            <div className="mt-8 flex gap-3">
              <a href="#menu" className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold" style={{ color: THEME.accent }}>
                <ShoppingBag className="h-4 w-4" /> View Menu
              </a>
              {onShare && (
                <button onClick={onShare} className="inline-flex items-center gap-2 rounded-full border-2 border-white/40 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">
                  <Share2 className="h-4 w-4" /> Share
                </button>
              )}
            </div>
          </div>
        </div>
        {/* Decorative */}
        <div className="absolute -bottom-10 -right-10 h-60 w-60 rounded-full opacity-10" style={{ background: 'white' }} />
      </header>

      {/* Categories */}
      <nav id="menu" className="border-b" style={{ borderColor: THEME.border }}>
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          {cats.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className="flex-shrink-0 rounded-full px-5 py-2 text-sm font-semibold transition"
              style={{
                background: category === c ? THEME.accent : 'transparent',
                color: category === c ? '#fff' : THEME.muted,
              }}
            >
              {c === 'all' ? 'All Items' : c}
            </button>
          ))}
        </div>
      </nav>

      {/* Menu Grid */}
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        {visible.length > 0 ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((product, i) => (
              <article
                key={product.id || i}
                className="group cursor-pointer overflow-hidden rounded-2xl border shadow-sm transition-all hover:shadow-lg"
                style={{ background: THEME.card, borderColor: THEME.border }}
                onClick={() => onSelect?.(product)}
              >
                <div className="relative aspect-[4/3] overflow-hidden" style={{ background: '#f0f5e8' }}>
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Utensils className="h-16 w-16 opacity-15" style={{ color: THEME.accent }} />
                    </div>
                  )}
                  <div className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-3 py-1 text-xs font-bold backdrop-blur" style={{ color: THEME.orange }}>
                    <Flame className="h-3 w-3" /> Popular
                  </div>
                </div>
                <div className="p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-lg font-bold">{product.name}</h3>
                      <p className="mt-1 text-sm leading-relaxed" style={{ color: THEME.muted }}>{product.description}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xl font-extrabold" style={{ color: THEME.accent }}>
                      ₦{Number(product.price || 0).toLocaleString()}
                    </span>
                    <div className="flex items-center gap-1 text-xs" style={{ color: THEME.muted }}>
                      <Clock className="h-3.5 w-3.5" />
                      {product.stock_quantity > 0 ? `${product.stock_quantity} available` : 'Order now'}
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="py-20 text-center" style={{ color: THEME.muted }}>
            <Utensils className="mx-auto mb-3 h-12 w-12 opacity-30" />
            <p className="text-lg font-semibold">Menu coming soon</p>
            <p className="text-sm">Check back shortly!</p>
          </div>
        )}
      </main>

      {config.contact_whatsapp && (
        <a
          href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
          target="_blank" rel="noreferrer"
          className="fixed bottom-5 right-5 z-50 inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-xl transition hover:bg-emerald-700"
        >
          <MessageCircle className="h-5 w-5" /> WhatsApp
        </a>
      )}
    </div>
  )
}
