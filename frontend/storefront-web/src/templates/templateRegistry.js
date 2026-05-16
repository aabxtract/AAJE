/**
 * AAJE Template Registry — JSON configs for all 5 storefront templates.
 * The AI picks from these during store generation based on business type.
 * Each config defines the visual identity, layout behavior, and suggested content.
 */
const TEMPLATE_REGISTRY = {
  premium: {
    id: 'premium',
    name: 'Premium Commerce',
    description: 'A high-end, modern e-commerce experience with advanced filtering and search',
    bestFor: ['general', 'electronics', 'mixed catalog', 'luxury'],
    keywords: ['shop', 'store', 'buy', 'sell', 'commerce', 'general'],
    theme: {
      bg: '#f8fafc',
      hero: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      accent: '#10b981',
      text: '#0f172a',
      muted: '#64748b',
      card: '#ffffff',
      border: '#e2e8f0',
    },
    layout: {
      heroStyle: 'full-bleed',
      productGrid: '3-col',
      hasSidebar: true,
      hasSearch: true,
      hasSort: true,
    },
    suggestedCategories: ['Popular', 'New Arrivals', 'Best Sellers', 'On Sale'],
  },

  fashion: {
    id: 'fashion',
    name: 'Fashion & Lifestyle',
    description: 'Warm, editorial-style layout perfect for clothing and accessories',
    bestFor: ['fashion', 'clothing', 'shoes', 'bags', 'thrift', 'boutique'],
    keywords: ['cloth', 'wear', 'fashion', 'shoe', 'bag', 'ankara', 'thrift', 'boutique'],
    theme: {
      bg: '#faf8f5',
      hero: 'linear-gradient(135deg, #1c1917 0%, #44403c 100%)',
      accent: '#d97706',
      text: '#1c1917',
      muted: '#78716c',
      card: '#ffffff',
      border: '#e7e5e4',
    },
    layout: {
      heroStyle: 'editorial',
      productGrid: '2-col',
      hasSidebar: false,
      hasSearch: true,
      hasSort: true,
    },
    suggestedCategories: ['New In', 'Dresses', 'Tops', 'Accessories', 'Sale'],
  },

  gadgets: {
    id: 'gadgets',
    name: 'Tech & Gadgets',
    description: 'Dark, sleek interface for electronics and tech products',
    bestFor: ['gadgets', 'phones', 'laptops', 'electronics', 'repairs', 'accessories'],
    keywords: ['phone', 'laptop', 'gadget', 'pc', 'computer', 'charger', 'repair', 'tech', 'iphone', 'samsung'],
    theme: {
      bg: '#09090b',
      hero: 'linear-gradient(135deg, #09090b 0%, #18181b 100%)',
      accent: '#3b82f6',
      text: '#fafafa',
      muted: '#a1a1aa',
      card: '#18181b',
      border: '#27272a',
    },
    layout: {
      heroStyle: 'tech-grid',
      productGrid: '4-col',
      hasSidebar: true,
      hasSearch: true,
      hasSort: true,
    },
    suggestedCategories: ['Smartphones', 'Laptops', 'Accessories', 'Audio', 'Repairs'],
  },

  food: {
    id: 'food',
    name: 'Food & Restaurant',
    description: 'Appetizing layout with menu-style cards for restaurants and food vendors',
    bestFor: ['food', 'restaurant', 'kitchen', 'catering', 'drinks', 'snacks'],
    keywords: ['food', 'rice', 'meal', 'drink', 'snack', 'catering', 'provision', 'kitchen', 'restaurant'],
    theme: {
      bg: '#fefce8',
      hero: 'linear-gradient(135deg, #ea580c 0%, #dc2626 100%)',
      accent: '#ea580c',
      text: '#1c1917',
      muted: '#78716c',
      card: '#ffffff',
      border: '#fde68a',
    },
    layout: {
      heroStyle: 'menu-banner',
      productGrid: '2-col',
      hasSidebar: false,
      hasSearch: true,
      hasSort: false,
    },
    suggestedCategories: ['Main Dishes', 'Snacks', 'Drinks', 'Desserts', 'Combo Packs'],
  },

  creator: {
    id: 'creator',
    name: 'Creator & Services',
    description: 'Portfolio-style layout for freelancers, consultants, and digital products',
    bestFor: ['creator', 'designer', 'coach', 'consultant', 'services', 'digital'],
    keywords: ['creator', 'design', 'course', 'coach', 'photo', 'video', 'service', 'consult', 'freelance'],
    theme: {
      bg: '#faf5ff',
      hero: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
      accent: '#7c3aed',
      text: '#1e1b4b',
      muted: '#6b7280',
      card: '#ffffff',
      border: '#e9d5ff',
    },
    layout: {
      heroStyle: 'centered-portfolio',
      productGrid: '3-col',
      hasSidebar: false,
      hasSearch: false,
      hasSort: false,
    },
    suggestedCategories: ['Consulting', 'Digital Products', 'Courses', 'Services'],
  },
}

/**
 * Picks the best template based on business description keywords.
 * Returns the template config object.
 */
export function pickTemplate(businessDescription = '') {
  const text = businessDescription.toLowerCase()
  
  for (const [id, config] of Object.entries(TEMPLATE_REGISTRY)) {
    if (id === 'premium') continue // premium is the fallback
    if (config.keywords.some(kw => text.includes(kw))) {
      return config
    }
  }
  
  return TEMPLATE_REGISTRY.premium // default
}

/**
 * Returns all template configs as an array for selection UIs.
 */
export function getAllTemplates() {
  return Object.values(TEMPLATE_REGISTRY)
}

/**
 * Returns a specific template by ID.
 */
export function getTemplate(id) {
  return TEMPLATE_REGISTRY[id] || TEMPLATE_REGISTRY.premium
}

export default TEMPLATE_REGISTRY
