import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, Loader2, Send, Sparkles, User as UserIcon, Plus, X, Package, Tag, ChevronRight } from 'lucide-react'
import { generateStore } from '../lib/api'
import { pickTemplate, getTemplate } from '../templates/templateRegistry'

const QUESTIONS = [
  {
    id: 'business',
    text: "Hi, I'm your AAJE store assistant. What kind of business are you building? Tell me what you sell or offer.",
    placeholder: 'e.g., I sell phones, laptop accessories, and repairs in Computer Village...',
  },
  {
    id: 'product_focus',
    text: 'What do customers mostly buy from you?',
    optionsByBusiness: {
      gadgets: ['Phones and phone accessories', 'Laptops and PCs', 'Repairs and diagnostics', 'General gadgets'],
      fashion: ['Ready-to-wear pieces', 'Shoes and bags', 'Thrift finds', 'Custom outfits'],
      food: ['Cooked meals', 'Snacks and drinks', 'Provisions', 'Catering packs'],
      creator: ['Digital products', 'Consulting or coaching', 'Creative services', 'Classes or bookings'],
      default: ['Physical products', 'Services', 'Digital products', 'Mixed catalog'],
    },
  },
  {
    id: 'customers',
    text: 'Nice. Who are your ideal customers? This helps me choose the right storefront direction.',
    placeholder: 'e.g., Students, office workers, resellers, Lagos walk-in customers...',
  },
  {
    id: 'style',
    text: 'What style fits your brand best?',
    options: ['Premium and trusted', 'Deal-heavy and fast', 'Clean catalog', 'Local market friendly', 'Bold and vibrant'],
  },
  {
    id: 'name',
    text: 'Almost done! What should your store be called?',
    placeholder: "e.g., Ada's Collections, Jude Sneakers...",
  },
]

function businessType(value = '') {
  const text = value.toLowerCase()
  if (/(phone|gadget|laptop|pc|computer|charger|repair|accessor|iphone|samsung)/.test(text)) return 'gadgets'
  if (/(food|rice|meal|drink|snack|catering|provision|kitchen)/.test(text)) return 'food'
  if (/(fashion|cloth|shoe|bag|wear|thrift|boutique|ankara)/.test(text)) return 'fashion'
  if (/(creator|design|course|coach|photo|video|service|consult)/.test(text)) return 'creator'
  return 'default'
}

/**
 * AI-suggested categories and sample products based on business type.
 * These are "controlled" suggestions the user can accept, modify, or add to.
 */
const AI_SUGGESTIONS = {
  gadgets: {
    categories: ['Smartphones', 'Laptops', 'Accessories', 'Repairs'],
    products: {
      'Smartphones': [
        { name: 'iPhone 15 Pro Max', price: 850000, stock: 5, desc: '256GB, Natural Titanium' },
        { name: 'Samsung Galaxy S24', price: 620000, stock: 8, desc: '128GB, Phantom Black' },
      ],
      'Laptops': [
        { name: 'MacBook Air M3', price: 980000, stock: 3, desc: '8GB RAM, 256GB SSD' },
        { name: 'HP Pavilion 15', price: 420000, stock: 6, desc: 'Intel i5, 8GB, 512GB' },
      ],
      'Accessories': [
        { name: 'AirPods Pro 2', price: 185000, stock: 15, desc: 'USB-C, Active Noise Cancelling' },
        { name: 'USB-C Charger 65W', price: 12000, stock: 30, desc: 'Fast charging, GaN' },
      ],
      'Repairs': [
        { name: 'Screen Replacement', price: 25000, stock: 99, desc: 'iPhone/Samsung display fix', type: 'service' },
      ],
    },
  },
  fashion: {
    categories: ['New Arrivals', 'Tops & Shirts', 'Dresses', 'Accessories'],
    products: {
      'New Arrivals': [
        { name: 'Ankara Maxi Dress', price: 18000, stock: 10, desc: 'Vibrant African print, all sizes' },
        { name: 'Denim Jacket', price: 15000, stock: 8, desc: 'Classic wash, unisex fit' },
      ],
      'Tops & Shirts': [
        { name: 'Cotton T-Shirt', price: 5500, stock: 25, desc: '100% cotton, multiple colors' },
      ],
      'Dresses': [
        { name: 'Bodycon Mini Dress', price: 12000, stock: 12, desc: 'Stretch fabric, party-ready' },
      ],
      'Accessories': [
        { name: 'Leather Tote Bag', price: 22000, stock: 6, desc: 'Genuine leather, spacious' },
        { name: 'Beaded Necklace Set', price: 4500, stock: 20, desc: 'Handmade, gold tone' },
      ],
    },
  },
  food: {
    categories: ['Main Dishes', 'Snacks', 'Drinks', 'Combo Packs'],
    products: {
      'Main Dishes': [
        { name: 'Jollof Rice Plate', price: 2500, stock: 50, desc: 'With chicken and plantain' },
        { name: 'Pounded Yam & Egusi', price: 3000, stock: 30, desc: 'With assorted meat' },
      ],
      'Snacks': [
        { name: 'Shawarma (Large)', price: 3500, stock: 40, desc: 'Chicken, full loaded' },
        { name: 'Meat Pie (Pack of 3)', price: 1800, stock: 25, desc: 'Freshly baked' },
      ],
      'Drinks': [
        { name: 'Chapman Bottle', price: 1500, stock: 30, desc: '75cl, chilled' },
      ],
      'Combo Packs': [
        { name: 'Family Combo', price: 12000, stock: 10, desc: 'Feeds 4: rice, chicken, drinks' },
      ],
    },
  },
  creator: {
    categories: ['Consulting', 'Courses', 'Digital Products', 'Services'],
    products: {
      'Consulting': [
        { name: '1-Hour Strategy Call', price: 30000, stock: 99, desc: 'Business growth consultation', type: 'service' },
      ],
      'Courses': [
        { name: 'Social Media Masterclass', price: 15000, stock: 99, desc: '4-week intensive program', type: 'service' },
      ],
      'Digital Products': [
        { name: 'Brand Design Template', price: 5000, stock: 99, desc: 'Canva editable templates' },
      ],
      'Services': [
        { name: 'Logo Design Package', price: 50000, stock: 99, desc: '3 concepts + revisions', type: 'service' },
        { name: 'Website Development', price: 200000, stock: 99, desc: 'Full custom build', type: 'service' },
      ],
    },
  },
  default: {
    categories: ['Popular', 'New Arrivals', 'Best Sellers'],
    products: {
      'Popular': [
        { name: 'Sample Product 1', price: 5000, stock: 20, desc: 'Quality product for your store' },
      ],
      'New Arrivals': [
        { name: 'Sample Product 2', price: 8000, stock: 15, desc: 'Latest addition to catalog' },
      ],
      'Best Sellers': [
        { name: 'Sample Product 3', price: 3500, stock: 30, desc: 'Customer favorite' },
      ],
    },
  },
}

export default function Onboarding() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [input, setInput] = useState('')
  const [answers, setAnswers] = useState({})
  const [building, setBuilding] = useState(false)

  // Inventory setup phase
  const [phase, setPhase] = useState('chat') // 'chat' | 'inventory'
  const [categories, setCategories] = useState([])
  const [categoryProducts, setCategoryProducts] = useState({}) // { "Cat Name": [{ name, price, stock, desc }] }
  const [newCatName, setNewCatName] = useState('')
  const [editingCat, setEditingCat] = useState(null)
  const [newProduct, setNewProduct] = useState({ name: '', price: '', stock: '', desc: '' })

  useEffect(() => {
    setMessages([{ role: 'ai', text: QUESTIONS[0].text }])
  }, [])

  function addMessage(role, text) {
    setMessages((prev) => [...prev, { role, text }])
  }

  function advanceToNext(newAnswers, nextIndex) {
    if (nextIndex < QUESTIONS.length) {
      setQuestionIndex(nextIndex)
      setTimeout(() => addMessage('ai', QUESTIONS[nextIndex].text), 400)
      setInput('')
    } else {
      // Chat phase done — move to inventory setup
      transitionToInventory(newAnswers)
    }
  }

  function handleSendText() {
    const value = input.trim()
    if (!value) return
    addMessage('user', value)
    const currentQ = QUESTIONS[questionIndex]
    const newAnswers = { ...answers, [currentQ.id]: value }
    setAnswers(newAnswers)
    advanceToNext(newAnswers, questionIndex + 1)
  }

  function handleOptionSelect(option) {
    addMessage('user', option)
    const currentQ = QUESTIONS[questionIndex]
    const newAnswers = { ...answers, [currentQ.id]: option }
    setAnswers(newAnswers)
    advanceToNext(newAnswers, questionIndex + 1)
  }

  function transitionToInventory(finalAnswers) {
    const bType = businessType(finalAnswers.business)
    const suggestions = AI_SUGGESTIONS[bType] || AI_SUGGESTIONS.default

    // Pre-populate categories and products from AI suggestions
    setCategories([...suggestions.categories])
    setCategoryProducts({ ...suggestions.products })
    setPhase('inventory')
  }

  function addCategory() {
    const name = newCatName.trim()
    if (!name || categories.includes(name)) return
    setCategories(prev => [...prev, name])
    setCategoryProducts(prev => ({ ...prev, [name]: [] }))
    setNewCatName('')
  }

  function removeCategory(cat) {
    setCategories(prev => prev.filter(c => c !== cat))
    setCategoryProducts(prev => {
      const copy = { ...prev }
      delete copy[cat]
      return copy
    })
    if (editingCat === cat) setEditingCat(null)
  }

  function addProductToCategory(cat) {
    if (!newProduct.name.trim() || !newProduct.price) return
    setCategoryProducts(prev => ({
      ...prev,
      [cat]: [...(prev[cat] || []), {
        name: newProduct.name.trim(),
        price: Number(newProduct.price),
        stock: Number(newProduct.stock) || 10,
        desc: newProduct.desc.trim() || '',
      }],
    }))
    setNewProduct({ name: '', price: '', stock: '', desc: '' })
  }

  function removeProduct(cat, idx) {
    setCategoryProducts(prev => ({
      ...prev,
      [cat]: prev[cat].filter((_, i) => i !== idx),
    }))
  }

  async function buildStore() {
    setBuilding(true)

    try {
      // Pick template from registry based on business description
      const templateConfig = pickTemplate(answers.business || '')

      // Flatten all products
      const allProducts = []
      for (const cat of categories) {
        for (const p of (categoryProducts[cat] || [])) {
          allProducts.push({
            name: p.name,
            price: p.price,
            stock_quantity: p.stock,
            description: p.desc,
            category: cat,
            type: p.type || 'product',
          })
        }
      }

      const prompt = [
        answers.business,
        answers.product_focus ? `Main product focus: ${answers.product_focus}` : '',
        answers.customers ? `Target customers: ${answers.customers}` : '',
        answers.style ? `Style preference: ${answers.style}` : '',
        answers.name ? `Store name: ${answers.name}` : '',
      ].filter(Boolean).join('\n')

      let blueprint = {}
      try {
        const response = await generateStore(prompt)
        blueprint = response.data || {}
      } catch { /* Use defaults if AI fails */ }

      const storeName = answers.name?.trim() || blueprint.store_name || 'My Store'
      const storeData = {
        template: templateConfig.id,
        store_name: storeName,
        description: blueprint.description || `${answers.business || 'Quality products'} for ${answers.customers || 'everyone'}`,
        tagline: blueprint.tagline || '',
        theme: blueprint.theme || 'default',
        categories: categories,
        starter_products: allProducts,
        slug: storeName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
      }

      sessionStorage.setItem('aaje_store_build', JSON.stringify(storeData))
      sessionStorage.setItem('aaje_onboarding_answers', JSON.stringify(answers))

      navigate('/confirm')
    } catch (err) {
      console.error('Build error:', err)
      alert('Something went wrong. Please try again.')
      setBuilding(false)
    }
  }

  const currentQ = QUESTIONS[questionIndex]
  const dynamicOptions = currentQ?.optionsByBusiness?.[businessType(answers.business)] || currentQ?.optionsByBusiness?.default || currentQ?.options
  const isOptions = dynamicOptions && questionIndex < QUESTIONS.length

  // ─── INVENTORY SETUP PHASE ───
  if (phase === 'inventory') {
    return (
      <main className="min-h-screen bg-[#fbf8ff] text-[#12102b]">
        <header className="border-b border-[#ece7f5] bg-white px-4 py-4">
          <div className="mx-auto flex max-w-4xl items-center gap-3">
            <img src="/IMG_5663.PNG" alt="" className="h-9" />
            <div>
              <p className="text-sm font-semibold">Set Up Your Inventory</p>
              <p className="text-xs text-[#74708a]">Organize categories and products for your store</p>
            </div>
            <div className="ml-auto flex items-center gap-2 rounded-full bg-[#f2edff] px-3 py-1">
              <Sparkles className="h-4 w-4 text-[#5a4be7]" />
              <span className="text-xs font-semibold text-[#5a4be7]">AI Suggested</span>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-4xl px-4 py-8">
          {/* AI suggestion banner */}
          <div className="mb-8 rounded-xl bg-gradient-to-r from-[#5a4be7] to-[#7c3aed] p-5 text-white">
            <div className="flex items-start gap-3">
              <Bot className="h-6 w-6 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold mb-1">AI has pre-filled your inventory!</p>
                <p className="text-sm opacity-80 leading-relaxed">
                  Based on your business type, I've suggested some categories and products. 
                  You can edit, remove, or add more below. When you're happy, hit "Build Store".
                </p>
              </div>
            </div>
          </div>

          {/* Add Category */}
          <div className="mb-6 flex gap-2">
            <input
              type="text"
              value={newCatName}
              onChange={e => setNewCatName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addCategory()}
              placeholder="Add a new category..."
              className="flex-1 rounded-lg border border-[#e4e1ee] bg-white px-4 py-3 text-sm outline-none focus:border-[#5a4be7] focus:ring-2 focus:ring-[#ece6ff]"
            />
            <button onClick={addCategory} disabled={!newCatName.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-[#5a4be7] px-5 py-3 text-sm font-bold text-white disabled:opacity-40 hover:bg-[#493bd0] transition">
              <Plus className="h-4 w-4" /> Add
            </button>
          </div>

          {/* Categories & Products */}
          <div className="space-y-4">
            {categories.map(cat => (
              <div key={cat} className="rounded-xl border border-[#e4e1ee] bg-white overflow-hidden shadow-sm">
                {/* Category Header */}
                <div className="flex items-center justify-between px-5 py-4 bg-[#fbf9ff] border-b border-[#ece7f5]">
                  <div className="flex items-center gap-3">
                    <Tag className="h-4 w-4 text-[#5a4be7]" />
                    <h3 className="font-bold text-[#12102b]">{cat}</h3>
                    <span className="text-[10px] font-bold text-[#9b97aa] bg-[#f2edff] px-2 py-0.5 rounded-full">
                      {(categoryProducts[cat] || []).length} items
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setEditingCat(editingCat === cat ? null : cat)}
                      className="text-xs font-bold text-[#5a4be7] hover:underline">
                      {editingCat === cat ? 'Done' : 'Add Product'}
                    </button>
                    <button onClick={() => removeCategory(cat)} className="p-1 text-[#9b97aa] hover:text-red-500">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Products List */}
                <div className="divide-y divide-[#f5f2fa]">
                  {(categoryProducts[cat] || []).map((p, idx) => (
                    <div key={idx} className="flex items-center justify-between px-5 py-3 hover:bg-[#fbf9ff] transition">
                      <div className="flex items-center gap-3">
                        <Package className="h-4 w-4 text-[#9b97aa]" />
                        <div>
                          <p className="text-sm font-semibold">{p.name}</p>
                          <p className="text-[10px] text-[#9b97aa]">{p.desc || 'No description'}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-bold text-[#5a4be7]">NGN {Number(p.price).toLocaleString()}</span>
                        <span className="text-[10px] text-[#9b97aa]">{p.stock} qty</span>
                        <button onClick={() => removeProduct(cat, idx)} className="p-1 text-[#9b97aa] hover:text-red-500">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}

                  {(categoryProducts[cat] || []).length === 0 && editingCat !== cat && (
                    <div className="px-5 py-6 text-center text-xs text-[#9b97aa]">
                      No products yet. Click "Add Product" to get started.
                    </div>
                  )}
                </div>

                {/* Add Product Form (inline) */}
                {editingCat === cat && (
                  <div className="border-t border-[#ece7f5] bg-[#fbf9ff] p-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <input placeholder="Product name" value={newProduct.name}
                        onChange={e => setNewProduct(p => ({ ...p, name: e.target.value }))}
                        className="rounded-md border border-[#e4e1ee] px-3 py-2 text-xs outline-none focus:border-[#5a4be7]" />
                      <input placeholder="Price" type="number" value={newProduct.price}
                        onChange={e => setNewProduct(p => ({ ...p, price: e.target.value }))}
                        className="rounded-md border border-[#e4e1ee] px-3 py-2 text-xs outline-none focus:border-[#5a4be7]" />
                      <input placeholder="Stock qty" type="number" value={newProduct.stock}
                        onChange={e => setNewProduct(p => ({ ...p, stock: e.target.value }))}
                        className="rounded-md border border-[#e4e1ee] px-3 py-2 text-xs outline-none focus:border-[#5a4be7]" />
                      <button onClick={() => addProductToCategory(cat)}
                        disabled={!newProduct.name.trim() || !newProduct.price}
                        className="rounded-md bg-[#5a4be7] px-3 py-2 text-xs font-bold text-white disabled:opacity-40 hover:bg-[#493bd0] transition">
                        + Add
                      </button>
                    </div>
                    <input placeholder="Description (optional)" value={newProduct.desc}
                      onChange={e => setNewProduct(p => ({ ...p, desc: e.target.value }))}
                      className="mt-2 w-full rounded-md border border-[#e4e1ee] px-3 py-2 text-xs outline-none focus:border-[#5a4be7]" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Build Button */}
          <div className="mt-10 flex gap-3">
            <button onClick={() => setPhase('chat')}
              className="rounded-lg border border-[#e4e1ee] bg-white px-6 py-4 text-sm font-semibold text-[#12102b] hover:border-[#5a4be7] transition">
              Back
            </button>
            <button onClick={buildStore} disabled={building || categories.length === 0}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-[#5a4be7] px-6 py-4 text-sm font-bold text-white transition hover:bg-[#493bd0] disabled:opacity-50">
              {building ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Building your store...</>
              ) : (
                <><Sparkles className="h-4 w-4" /> Build Store <ChevronRight className="h-4 w-4" /></>
              )}
            </button>
          </div>
        </div>
      </main>
    )
  }

  // ─── CHAT PHASE ───
  return (
    <main className="flex min-h-screen flex-col bg-[#fbf8ff] text-[#12102b]">
      <header className="border-b border-[#ece7f5] bg-white px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <img src="/IMG_5663.PNG" alt="" className="h-9" />
          <div>
            <p className="text-sm font-semibold">AAJE Store Builder</p>
            <p className="text-xs text-[#74708a]">AI is setting up your storefront</p>
          </div>
          <div className="ml-auto flex items-center gap-2 rounded-full bg-[#f2edff] px-3 py-1">
            <Sparkles className="h-4 w-4 text-[#5a4be7]" />
            <span className="text-xs font-semibold text-[#5a4be7]">
              Step {Math.min(questionIndex + 1, QUESTIONS.length)} of {QUESTIONS.length}
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="mx-auto max-w-3xl space-y-5">
          {messages.map((msg, index) => (
            <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'ai' && (
                <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#5a4be7] text-white">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`max-w-[82%] rounded-[16px] px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#5a4be7] text-white'
                    : 'border border-[#ece7f5] bg-white text-[#12102b]'
                }`}
              >
                {msg.text}
              </div>
              {msg.role === 'user' && (
                <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#ece6ff] text-[#5a4be7]">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {!building && questionIndex < QUESTIONS.length && (
        <div className="border-t border-[#ece7f5] bg-white px-4 py-4">
          <div className="mx-auto max-w-3xl">
            {isOptions ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {dynamicOptions.map((option) => (
                  <button
                    key={option}
                    onClick={() => handleOptionSelect(option)}
                    className="rounded-[8px] border border-[#e4e1ee] bg-white px-4 py-3 text-left text-sm font-medium text-[#12102b] transition hover:border-[#5a4be7] hover:bg-[#f4efff]"
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => event.key === 'Enter' && handleSendText()}
                  placeholder={currentQ?.placeholder || 'Type your answer...'}
                  autoFocus
                  className="flex-1 rounded-[8px] border border-[#e4e1ee] bg-[#fafafa] px-4 py-3 text-sm outline-none transition placeholder:text-[#9b97aa] focus:border-[#5a4be7] focus:ring-2 focus:ring-[#ece6ff]"
                />
                <button
                  onClick={handleSendText}
                  disabled={!input.trim()}
                  className="grid h-12 w-12 place-items-center rounded-[8px] bg-[#5a4be7] text-white transition hover:bg-[#493bd0] disabled:opacity-40"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  )
}
