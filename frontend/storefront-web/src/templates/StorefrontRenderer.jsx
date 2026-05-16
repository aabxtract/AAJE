import UniversalStorefront from './UniversalStorefront'

/**
 * StorefrontRenderer — Routes all template types through the UniversalStorefront engine.
 * The engine reads the template config from templateRegistry.js and adapts accordingly.
 */
export default function StorefrontRenderer({ config, products, onSelect, onShare }) {
  const safeConfig = {
    ...config,
    store_name: config.store_name || 'My Store',
    categories: config.categories || [],
    products: config.products || [],
    template: config.template || 'premium',
  }

  return (
    <UniversalStorefront
      config={safeConfig}
      products={products}
      onSelect={onSelect}
      onShare={onShare}
    />
  )
}
