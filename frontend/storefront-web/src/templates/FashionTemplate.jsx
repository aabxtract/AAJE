import { useMemo, useState } from 'react'
import { MessageCircle, Share2, ShoppingBag, Star, Heart } from 'lucide-react'

const THEME = {
  bg: '#fdf2f0',
  accent: '#e85d4a',
  text: '#1a1a1a',
  muted: '#6b5e5b',
  card: '#ffffff',
  badge: '#fce4e0',
}

export default function FashionTemplate({ config, products, onSelect, onShare }) {
  const [category, setCategory] = useState('all')
  const cats = useMemo(() => ['all', ...(config.categories || [])], [config.categories])
  const items = products || config.products || []
  const visible = category === 'all' ? items : items.filter((p) => p.category === category)

  return (
    <div className="min-h-screen" style={{ background: THEME.bg, color: THEME.text }}>
      {/* Hero Banner */}
      <header className="relative overflow-hidden" style={{ background: `linear-gradient(135deg, ${THEME.accent} 0%, #c24a3a 100%)` }}>
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="max-w-xl text-white">
            <p className="mb-2 text-sm font-semibold uppercase tracking-widest opacity-80">
              AAJE Store
            </p>
            <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
              {config.store_name}
            </h1>
            {config.tagline && (
              <p className="mt-3 text-lg font-medium opacity-90">{config.tagline}</p>
            )}
            {config.description && (
              <p className="mt-4 text-sm leading-relaxed opacity-75">{config.description}</p>
            )}
            <div className="mt-8 flex gap-3">
              <a href="#products" className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold" style={{ color: THEME.accent }}>
                <ShoppingBag className="h-4 w-4" /> Shop Now
              </a>
              {onShare && (
                <button onClick={onShare} className="inline-flex items-center gap-2 rounded-full border-2 border-white/40 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">
                  <Share2 className="h-4 w-4" /> Share
                </button>
              )}
            </div>
          </div>
        </div>
        {/* Decorative circles */}
        <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full opacity-10" style={{ background: 'white' }} />
        <div className="absolute -bottom-10 right-20 h-40 w-40 rounded-full opacity-10" style={{ background: 'white' }} />
      </header>

      {/* Categories */}
      <nav id="products" className="border-b" style={{ borderColor: '#e8dbd8' }}>
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          {cats.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className="flex-shrink-0 rounded-full px-5 py-2 text-sm font-semibold transition-all"
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
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((product, i) => (
              <article
                key={product.id || i}
                className="group cursor-pointer overflow-hidden rounded-2xl border shadow-sm transition-all hover:shadow-lg"
                style={{ background: THEME.card, borderColor: '#f0e0dc' }}
                onClick={() => onSelect?.(product)}
              >
                <div className="relative aspect-square overflow-hidden" style={{ background: THEME.badge }}>
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <ShoppingBag className="h-16 w-16 opacity-20" style={{ color: THEME.accent }} />
                    </div>
                  )}
                  <button className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-white/80 backdrop-blur transition hover:bg-white">
                    <Heart className="h-4 w-4" style={{ color: THEME.accent }} />
                  </button>
                  {product.type === 'service' && (
                    <span className="absolute left-3 top-3 rounded-full px-3 py-1 text-xs font-bold text-white" style={{ background: THEME.accent }}>
                      Service
                    </span>
                  )}
                </div>
                <div className="p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: THEME.muted }}>{product.category}</p>
                  <h3 className="mt-1 text-lg font-bold">{product.name}</h3>
                  <p className="mt-1 text-sm leading-relaxed" style={{ color: THEME.muted }}>
                    {product.description}
                  </p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xl font-extrabold" style={{ color: THEME.accent }}>
                      ₦{Number(product.price || 0).toLocaleString()}
                    </span>
                    <div className="flex items-center gap-1 text-xs" style={{ color: THEME.muted }}>
                      <Star className="h-3.5 w-3.5 fill-current" style={{ color: '#f59e0b' }} />
                      {product.type === 'service' ? 'Book' : `${product.stock_quantity || 0} left`}
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="py-20 text-center" style={{ color: THEME.muted }}>
            <ShoppingBag className="mx-auto mb-3 h-12 w-12 opacity-30" />
            <p className="text-lg font-semibold">No products yet</p>
            <p className="text-sm">Check back soon!</p>
          </div>
        )}
      </main>

      {/* WhatsApp FAB */}
      {config.contact_whatsapp && (
        <a
          href={`https://wa.me/${(config.contact_whatsapp || '').replace(/\D/g, '')}`}
          target="_blank"
          rel="noreferrer"
          className="fixed bottom-5 right-5 z-50 inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-xl transition hover:bg-emerald-700"
        >
          <MessageCircle className="h-5 w-5" /> WhatsApp
        </a>
      )}
    </div>
  )
}
