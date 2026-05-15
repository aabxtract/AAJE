import FashionTemplate from './FashionTemplate'
import GadgetsTemplate from './GadgetsTemplate'
import FoodTemplate from './FoodTemplate'
import CreatorTemplate from './CreatorTemplate'

/**
 * StorefrontRenderer — picks the correct template based on config.template
 * and passes through all props (config, products, onSelect, onShare).
 */
export default function StorefrontRenderer({ config, products, onSelect, onShare }) {
  const safeConfig = {
    ...config,
    store_name: config.store_name || 'My Store',
    categories: config.categories || [],
    products: config.products || [],
  }

  const props = { config: safeConfig, products, onSelect, onShare }

  switch (config.template) {
    case 'gadgets':
      return <GadgetsTemplate {...props} />
    case 'food':
      return <FoodTemplate {...props} />
    case 'creator':
      return <CreatorTemplate {...props} />
    case 'fashion':
    default:
      return <FashionTemplate {...props} />
  }
}
