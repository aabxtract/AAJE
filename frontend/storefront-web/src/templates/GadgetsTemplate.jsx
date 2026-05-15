import { useMemo, useState } from 'react'
import { MessageCircle, Share2, ShoppingBag, Zap, Cpu } from 'lucide-react'

const THEME = {
  bg: '#0b1120',
  accent: '#3b82f6',
  text: '#e2e8f0',
  muted: '#94a3b8',
  card: '#131c31',
  border: '#1e293b',
}

export default function GadgetsTemplate({ config, products, onSelect, onShare }) {
  const [category, setCategory] = useState('all')
  const cats = useMemo(() => ['all', ...(config.categories || [])], [config.categories])
  const items = products || config.products || []
  const visible = category === 'all' ? items : items.filter((p) => p.category === category)

  return (
    <div className="min-h-screen" style={{ background: THEME.bg, color: THEME.text }}>
      {/* Hero */}
      <header className="relative overflow-hidden border-b" style={{ borderColor: THEME.border }}>
        <div className="absolute inset-0 opacity-20" style={{ background: `radial-gradient(ellipse at 70% 0%, ${THEME.accent}33 0%, transparent 60%)` }} />
        <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <div className="max-w-xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-bold uppercase tracking-widest" style={{ borderColor: THEME.accent, color: THEME.accent }}>
              <Zap className="h-3 w-3" /> Tech Store
            </div>
            <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">{config.store_name}</h1>
            {config.tagline && <p className="mt-3 text-lg font-medium" style={{ color: THEME.muted }}>{config.tagline}</p>}
            {config.description && <p className="mt-3 text-sm leading-relaxed" style={{ color: THEME.muted }}>{config.description}</p>}
            <div className="mt-8 flex gap-3">
              <a href="#products" className="inline-flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-bold text-white" style={{ background: THEME.accent }}>
                <ShoppingBag className="h-4 w-4" /> Browse Products
              </a>
              {onShare && (
                <button onClick={onShare} className="inline-flex items-center gap-2 rounded-lg border px-5 py-3 text-sm font-semibold transition hover:bg-white/5" style={{ borderColor: THEME.border, color: THEME.muted }}>
                  <Share2 className="h-4 w-4" /> Share
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Categories */}
      <nav id="products" className="border-b" style={{ borderColor: THEME.border }}>
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          {cats.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className="flex-shrink-0 rounded-lg px-5 py-2 text-sm font-semibold transition"
              style={{
                background: category === c ? THEME.accent : 'transparent',
                color: category === c ? '#fff' : THEME.muted,
              }}
            >
              {c === 'all' ? 'All' : c}
            </button>
          ))}
        </div>
      </nav>

      {/* Product Grid */}
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        {visible.length > 0 ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {visible.map((product, i) => (
              <article
                key={product.id || i}
                className="group cursor-pointer overflow-hidden rounded-xl border transition-all hover:border-blue-500/40"
                style={{ background: THEME.card, borderColor: THEME.border }}
                onClick={() => onSelect?.(product)}
              >
                <div className="relative aspect-square overflow-hidden" style={{ background: '#0f1a30' }}>
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Cpu className="h-16 w-16 opacity-15" style={{ color: THEME.accent }} />
                    </div>
                  )}
                  {product.type === 'service' && (
                    <span className="absolute left-3 top-3 rounded-md px-2 py-1 text-xs font-bold text-white" style={{ background: THEME.accent }}>
                      Service
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: THEME.accent }}>{product.category}</p>
                  <h3 className="mt-1 font-bold">{product.name}</h3>
                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed" style={{ color: THEME.muted }}>{product.description}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-lg font-extrabold" style={{ color: THEME.accent }}>
                      ₦{Number(product.price || 0).toLocaleString()}
                    </span>
                    <span className="text-xs" style={{ color: THEME.muted }}>
                      {product.type === 'service' ? 'Book' : `${product.stock_quantity || 0} in stock`}
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="py-20 text-center" style={{ color: THEME.muted }}>
            <Cpu className="mx-auto mb-3 h-12 w-12 opacity-30" />
            <p className="text-lg font-semibold">No products yet</p>
            <p className="text-sm">Check back soon!</p>
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
