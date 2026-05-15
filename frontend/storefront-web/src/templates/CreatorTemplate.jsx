import { useMemo, useState } from 'react'
import { MessageCircle, Share2, Briefcase, Star, ArrowRight, Palette } from 'lucide-react'

const THEME = {
  bg: '#f8f5ff',
  accent: '#7c3aed',
  text: '#1a1a2e',
  muted: '#6b7280',
  card: '#ffffff',
  border: '#e5e0f0',
}

export default function CreatorTemplate({ config, products, onSelect, onShare }) {
  const [category, setCategory] = useState('all')
  const cats = useMemo(() => ['all', ...(config.categories || [])], [config.categories])
  const items = products || config.products || []
  const visible = category === 'all' ? items : items.filter((p) => p.category === category)

  return (
    <div className="min-h-screen" style={{ background: THEME.bg, color: THEME.text }}>
      {/* Hero */}
      <header className="relative overflow-hidden border-b" style={{ borderColor: THEME.border }}>
        <div className="absolute inset-0 opacity-30" style={{ background: `radial-gradient(circle at 30% 20%, ${THEME.accent}22 0%, transparent 50%)` }} />
        <div className="relative mx-auto max-w-5xl px-4 py-16 text-center sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: `${THEME.accent}15` }}>
            <Palette className="h-8 w-8" style={{ color: THEME.accent }} />
          </div>
          <h1 className="text-4xl font-extrabold sm:text-5xl">{config.store_name}</h1>
          {config.tagline && <p className="mx-auto mt-3 max-w-lg text-lg font-medium" style={{ color: THEME.muted }}>{config.tagline}</p>}
          {config.description && <p className="mx-auto mt-4 max-w-lg text-sm leading-relaxed" style={{ color: THEME.muted }}>{config.description}</p>}
          <div className="mt-8 flex justify-center gap-3">
            <a href="#services" className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-bold text-white" style={{ background: THEME.accent }}>
              <Briefcase className="h-4 w-4" /> View Services
            </a>
            {onShare && (
              <button onClick={onShare} className="inline-flex items-center gap-2 rounded-xl border-2 px-5 py-3 text-sm font-semibold transition hover:bg-purple-50" style={{ borderColor: THEME.border, color: THEME.muted }}>
                <Share2 className="h-4 w-4" /> Share
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Categories */}
      <nav id="services" className="border-b" style={{ borderColor: THEME.border }}>
        <div className="mx-auto flex max-w-5xl justify-center gap-1 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          {cats.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className="flex-shrink-0 rounded-xl px-5 py-2 text-sm font-semibold transition"
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

      {/* Service Cards */}
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        {visible.length > 0 ? (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((product, i) => (
              <article
                key={product.id || i}
                className="group cursor-pointer overflow-hidden rounded-2xl border shadow-sm transition-all hover:shadow-lg hover:border-purple-300"
                style={{ background: THEME.card, borderColor: THEME.border }}
                onClick={() => onSelect?.(product)}
              >
                {product.image_url ? (
                  <div className="aspect-video overflow-hidden">
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                  </div>
                ) : (
                  <div className="flex aspect-video items-center justify-center" style={{ background: `${THEME.accent}08` }}>
                    <Briefcase className="h-12 w-12 opacity-15" style={{ color: THEME.accent }} />
                  </div>
                )}
                <div className="p-6">
                  <div className="mb-2 inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold" style={{ background: `${THEME.accent}12`, color: THEME.accent }}>
                    <Star className="h-3 w-3" /> {product.category || 'Service'}
                  </div>
                  <h3 className="mt-2 text-xl font-bold">{product.name}</h3>
                  <p className="mt-2 text-sm leading-relaxed" style={{ color: THEME.muted }}>{product.description}</p>
                  <div className="mt-5 flex items-center justify-between">
                    <span className="text-2xl font-extrabold" style={{ color: THEME.accent }}>
                      ₦{Number(product.price || 0).toLocaleString()}
                    </span>
                    <span className="inline-flex items-center gap-1 text-sm font-semibold" style={{ color: THEME.accent }}>
                      {product.type === 'service' ? 'Book Now' : 'Buy'} <ArrowRight className="h-4 w-4" />
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="py-20 text-center" style={{ color: THEME.muted }}>
            <Briefcase className="mx-auto mb-3 h-12 w-12 opacity-30" />
            <p className="text-lg font-semibold">Services coming soon</p>
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
