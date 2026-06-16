/**
 * Universal storefront renderer.
 *
 * Reads a template JSON (from /templates/{id}) and renders the storefront
 * applying the template's theme + layout intent. Single component, no
 * per-template React variants — visual differences come from JSON.
 *
 * Inputs:
 *   - template:  the JSON dict (see backend/app/intelligence/templates_catalog.py)
 *   - store:     normalized store object from the API
 *   - products:  array of normalized products
 *   - onSelect:  (product) => void, called when buyer taps a product card
 *   - onShare:   () => void, optional, footer share button
 */
import { Search, Share2, ShoppingBag } from 'lucide-react'
import { formatCurrency } from '../lib/utils'

const HEADING_FONTS = {
  serif: 'font-serif',
  sans: 'font-sans',
  display: 'font-sans',
  mono: 'font-mono',
}

const HEADING_WEIGHTS = {
  black: 'font-black',
  bold: 'font-bold',
  semibold: 'font-semibold',
}

const PRODUCT_GRID_CLASS = {
  '2-col': 'grid grid-cols-1 sm:grid-cols-2 gap-6',
  '3-col': 'grid grid-cols-2 md:grid-cols-3 gap-5',
  '4-col': 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4',
  'list': 'flex flex-col gap-3',
}

export default function TemplateRenderer({ template, store, products = [], onSelect, onShare }) {
  if (!template) return null

  const theme = template.theme || {}
  const typo = template.typography || {}
  const layout = template.layout || {}

  // CSS vars + inline styles so we don't have to compile dynamic Tailwind
  const themeStyle = {
    '--t-primary': theme.primary_color,
    '--t-accent': theme.accent_color,
    '--t-background': theme.background,
    '--t-card-bg': theme.card_background,
    '--t-text': theme.text_color,
    '--t-muted': theme.muted_text,
    '--t-border': theme.border_color,
    backgroundColor: theme.background,
    color: theme.text_color,
  }

  const headingFontClass = HEADING_FONTS[typo.heading_font] || 'font-sans'
  const headingWeightClass = HEADING_WEIGHTS[typo.heading_weight] || 'font-bold'

  const sections = template.sections || ['hero', 'all_products', 'footer']
  const sectionRenderers = {
    hero: () => (
      <Hero
        template={template}
        store={store}
        headingFontClass={headingFontClass}
        headingWeightClass={headingWeightClass}
      />
    ),
    featured_products: () =>
      products.length > 0 && (
        <ProductSection
          title="Featured"
          template={template}
          products={products.slice(0, 4)}
          onSelect={onSelect}
          headingFontClass={headingFontClass}
          headingWeightClass={headingWeightClass}
        />
      ),
    all_products: () => (
      <ProductSection
        title={products.length === 0 ? 'Products coming soon' : 'Shop everything'}
        template={template}
        products={products}
        onSelect={onSelect}
        headingFontClass={headingFontClass}
        headingWeightClass={headingWeightClass}
      />
    ),
    about: () =>
      layout.show_about_section && (
        <AboutBlock
          store={store}
          template={template}
          headingFontClass={headingFontClass}
          headingWeightClass={headingWeightClass}
        />
      ),
    footer: () => (
      <Footer store={store} template={template} onShare={onShare} />
    ),
  }

  return (
    <main style={themeStyle} className={`min-h-screen ${headingFontClass}`}>
      {sections.map((s) => (
        <section key={s}>{sectionRenderers[s]?.()}</section>
      ))}
    </main>
  )
}


function Hero({ template, store, headingFontClass, headingWeightClass }) {
  const theme = template.theme || {}
  const layout = template.layout || {}
  const heroStyle = layout.hero_style || 'full_bleed'
  const heroText = store?.tagline || template.sample_hero_text || ''
  const storeName = store?.store_name || template.name

  if (heroStyle === 'minimal_centered') {
    return (
      <div className="border-b" style={{ borderColor: theme.border_color, background: theme.background }}>
        <div className="mx-auto max-w-4xl px-6 py-20 text-center">
          <h1 className={`text-4xl tracking-tight md:text-6xl ${headingFontClass} ${headingWeightClass}`}>
            {storeName}
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base" style={{ color: theme.muted_text }}>
            {heroText}
          </p>
        </div>
      </div>
    )
  }

  if (heroStyle === 'editorial_split') {
    return (
      <div className="grid md:grid-cols-2">
        <div
          className="flex items-center justify-center px-6 py-16 md:py-24"
          style={{ background: theme.hero_gradient || theme.primary_color, color: '#fff' }}
        >
          <div>
            <p className="text-xs uppercase tracking-widest opacity-70">{template.vibe}</p>
            <h1 className={`mt-3 text-4xl md:text-5xl ${headingFontClass} ${headingWeightClass}`}>
              {storeName}
            </h1>
            <p className="mt-4 max-w-md text-sm opacity-90">{heroText}</p>
          </div>
        </div>
        <div className="flex items-center justify-center px-6 py-16 md:py-24" style={{ background: theme.card_background }}>
          <p className="max-w-md text-sm" style={{ color: theme.muted_text }}>
            {template.tagline}
          </p>
        </div>
      </div>
    )
  }

  if (heroStyle === 'menu_banner') {
    return (
      <div
        className="px-6 py-16 text-center"
        style={{ background: theme.hero_gradient || theme.primary_color, color: '#fff' }}
      >
        <p className="text-xs uppercase tracking-[0.3em] opacity-80">Today's menu</p>
        <h1 className={`mt-2 text-4xl md:text-6xl ${headingFontClass} ${headingWeightClass}`}>
          {storeName}
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm opacity-95">{heroText}</p>
      </div>
    )
  }

  if (heroStyle === 'tech_grid') {
    return (
      <div
        className="border-b px-6 py-14"
        style={{
          background: theme.hero_gradient || theme.primary_color,
          borderColor: theme.border_color,
          color: '#fff',
        }}
      >
        <div className="mx-auto max-w-6xl">
          <h1 className={`text-3xl md:text-5xl ${headingFontClass} ${headingWeightClass}`}>{storeName}</h1>
          <p className="mt-3 max-w-xl text-sm opacity-90">{heroText}</p>
        </div>
      </div>
    )
  }

  if (heroStyle === 'magazine_block') {
    return (
      <div
        className="px-6 py-20"
        style={{ background: theme.hero_gradient || '#000', color: '#fff' }}
      >
        <div className="mx-auto max-w-5xl">
          <div
            className={`text-5xl uppercase leading-none md:text-8xl ${headingFontClass} ${headingWeightClass}`}
            style={{ color: theme.accent_color }}
          >
            {storeName}
          </div>
          <p className="mt-6 max-w-md text-sm opacity-90">{heroText}</p>
        </div>
      </div>
    )
  }

  if (heroStyle === 'service_blocks') {
    return (
      <div
        className="px-6 py-16"
        style={{ background: theme.hero_gradient || theme.primary_color, color: '#fff' }}
      >
        <div className="mx-auto max-w-4xl text-center">
          <h1 className={`text-4xl md:text-5xl ${headingFontClass} ${headingWeightClass}`}>{storeName}</h1>
          <p className="mx-auto mt-4 max-w-xl text-sm opacity-90">{heroText}</p>
        </div>
      </div>
    )
  }

  if (heroStyle === 'portfolio_grid') {
    return (
      <div
        className="px-6 py-20"
        style={{ background: theme.hero_gradient || theme.primary_color, color: '#fff' }}
      >
        <div className="mx-auto max-w-4xl text-center">
          <h1 className={`text-5xl ${headingFontClass} ${headingWeightClass}`}>{storeName}</h1>
          <p className="mx-auto mt-3 max-w-md text-sm opacity-90">{heroText}</p>
        </div>
      </div>
    )
  }

  // Default: full_bleed
  return (
    <div
      className="px-6 py-16 text-center"
      style={{ background: theme.hero_gradient || theme.primary_color, color: '#fff' }}
    >
      <h1 className={`text-4xl md:text-6xl ${headingFontClass} ${headingWeightClass}`}>{storeName}</h1>
      <p className="mx-auto mt-4 max-w-xl text-sm opacity-90">{heroText}</p>
    </div>
  )
}


function ProductSection({ title, template, products, onSelect, headingFontClass, headingWeightClass }) {
  const theme = template.theme || {}
  const layout = template.layout || {}
  const gridClass = PRODUCT_GRID_CLASS[layout.product_grid] || PRODUCT_GRID_CLASS['3-col']

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-6 flex items-end justify-between">
        <h2 className={`text-xl md:text-2xl ${headingFontClass} ${headingWeightClass}`}>{title}</h2>
        {layout.show_search && (
          <button
            className="hidden items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium md:inline-flex"
            style={{ borderColor: theme.border_color, color: theme.muted_text }}
          >
            <Search className="h-3.5 w-3.5" /> Search
          </button>
        )}
      </div>

      {products.length === 0 ? (
        <div
          className="rounded-xl border-2 border-dashed p-12 text-center text-sm"
          style={{ borderColor: theme.border_color, color: theme.muted_text }}
        >
          The store owner hasn't added products yet. Check back soon.
        </div>
      ) : (
        <div className={gridClass}>
          {products.map((p) => (
            <ProductCard key={p.id} product={p} template={template} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  )
}


function ProductCard({ product, template, onSelect }) {
  const theme = template.theme || {}
  const layout = template.layout || {}
  const card = layout.card_style || 'flat'

  const cardStyle = {
    background: theme.card_background,
    borderColor: theme.border_color,
    color: theme.text_color,
  }

  const cardClass = {
    elevated: 'rounded-2xl border shadow-sm transition hover:shadow-md',
    flat: 'rounded-lg border transition hover:opacity-95',
    outlined: 'rounded-xl border-2 transition hover:border-current',
    warm: 'rounded-2xl border shadow-md transition hover:shadow-lg',
  }[card] || 'rounded-lg border'

  return (
    <button
      onClick={() => onSelect?.(product)}
      className={`group block w-full overflow-hidden text-left ${cardClass}`}
      style={cardStyle}
    >
      <div
        className="aspect-square w-full bg-cover bg-center"
        style={{
          backgroundColor: theme.background,
          backgroundImage: product.image_url ? `url(${product.image_url})` : undefined,
        }}
      >
        {!product.image_url && (
          <div className="flex h-full items-center justify-center text-xs" style={{ color: theme.muted_text }}>
            No image
          </div>
        )}
      </div>
      <div className="p-3">
        <p className="line-clamp-2 text-sm font-semibold">{product.name}</p>
        <p className="mt-1 text-base font-bold" style={{ color: theme.primary_color }}>
          {formatCurrency(product.price)}
        </p>
      </div>
    </button>
  )
}


function AboutBlock({ store, template, headingFontClass, headingWeightClass }) {
  const theme = template.theme || {}
  const text = store?.description || store?.store_description || ''
  if (!text) return null
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 text-center">
      <h2 className={`text-xl ${headingFontClass} ${headingWeightClass}`}>About this store</h2>
      <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed" style={{ color: theme.muted_text }}>
        {text}
      </p>
    </div>
  )
}


function Footer({ store, template, onShare }) {
  const theme = template.theme || {}
  return (
    <div
      className="mt-auto border-t px-6 py-8 text-center text-xs"
      style={{ borderColor: theme.border_color, color: theme.muted_text }}
    >
      <p>
        Powered by{' '}
        <span style={{ color: theme.primary_color }}>AAJE</span>
      </p>
      {onShare && (
        <button onClick={onShare} className="mt-3 inline-flex items-center gap-1.5">
          <Share2 className="h-3.5 w-3.5" /> Share this store
        </button>
      )}
    </div>
  )
}
