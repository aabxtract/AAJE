import { Link } from 'react-router-dom'
import { ArrowRight, Check, MessageCircle, Sparkles } from 'lucide-react'
import PublicFooter from '../components/PublicFooter'

const plans = [
  {
    name: 'Free',
    price: '₦0',
    cadence: 'forever',
    description: 'Start selling with a complete storefront and core operations.',
    cta: 'Create Your Store',
    to: '/signup',
    features: [
      '1 storefront',
      'Product listings',
      'Squad payments',
      'Basic inventory',
      'Dashboard access',
      'WhatsApp sales notifications',
    ],
  },
  {
    name: 'Premium',
    price: '₦3,000',
    cadence: 'per month',
    description: 'Unlock deeper visibility, smarter operations, and richer growth tools.',
    cta: 'Upgrade with AAJE',
    to: '/signup',
    featured: true,
    features: [
      'Campaign analytics',
      'Advanced WhatsApp operations',
      'Richer BizPrint visibility',
      'AI operational insights',
      'Advanced business visibility features',
      'Premium growth tools',
    ],
  },
]

const comparisons = [
  'AI-assisted storefront setup',
  'Secure Squad-powered checkout',
  'Inventory and order dashboard',
  'WhatsApp operational updates',
  'BizPrint business activity profile',
]

function PricingNav() {
  return (
    <nav className="border-b border-[#e7e1ef] bg-[#fbf8ff]/95 px-5 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6">
        <Link to="/" aria-label="AAJE home">
          <img src="/IMG_5663.PNG" alt="AAJE" className="h-32 object-contain" />
        </Link>
        <div className="hidden items-center gap-8 text-xs font-medium text-[#4f4b63] md:flex">
          <Link to="/#solutions" className="transition hover:text-[#077ef6]">Features</Link>
          <Link to="/pricing" className="text-[#077ef6]">Pricing</Link>
          <Link to="/faqs" className="transition hover:text-[#077ef6]">FAQs</Link>
          <Link to="/contact" className="transition hover:text-[#077ef6]">Contact Us</Link>
        </div>
        <Link to="/signup" className="inline-flex h-8 items-center rounded-[7px] bg-[#077ef6] px-4 text-xs font-bold text-white transition hover:bg-[#0269d2]">
          Get started
        </Link>
      </div>
    </nav>
  )
}

export default function Pricing() {
  return (
    <main className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <PricingNav />

      <section className="px-5 py-20 text-center lg:px-8">
        <div className="mx-auto max-w-4xl">
          <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">AAJE pricing</p>
          <h1 className="mt-4 font-poppins text-5xl font-[600] leading-tight text-[#05051f]">
            Start free, upgrade when your operations need more power.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-[#625d75]">
            Launch a storefront with payments, inventory, dashboard access, and WhatsApp sales notifications. Premium adds deeper intelligence for growing businesses.
          </p>
        </div>
      </section>

      <section className="px-5 pb-20 lg:px-8">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          {plans.map((plan) => (
            <article key={plan.name} className={`rounded-[8px] border p-8 ${plan.featured ? 'border-[#077ef6] bg-[#030328] text-white shadow-[0_28px_70px_rgba(3,3,40,0.18)]' : 'border-[#e3ddec] bg-white text-[#030328]'}`}>
              <div className="flex items-start justify-between gap-6">
                <div>
                  <p className={`text-[0.68rem] font-black uppercase ${plan.featured ? 'text-[#93c5fd]' : 'text-[#077ef6]'}`}>{plan.name}</p>
                  <h2 className="mt-4 text-4xl font-black">{plan.price}</h2>
                  <p className={`mt-1 text-sm ${plan.featured ? 'text-white/60' : 'text-[#625d75]'}`}>{plan.cadence}</p>
                </div>
                <span className={`grid h-10 w-10 place-items-center rounded-[8px] ${plan.featured ? 'bg-white/10 text-[#93c5fd]' : 'bg-[#eef6ff] text-[#077ef6]'}`}>
                  {plan.featured ? <Sparkles className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
                </span>
              </div>
              <p className={`mt-6 text-sm leading-7 ${plan.featured ? 'text-white/70' : 'text-[#625d75]'}`}>{plan.description}</p>
              <div className="mt-8 space-y-4">
                {plan.features.map((feature) => (
                  <div key={feature} className={`flex items-center gap-3 text-sm font-semibold ${plan.featured ? 'text-white/82' : 'text-[#4f4b63]'}`}>
                    <span className={`grid h-5 w-5 place-items-center rounded-full ${plan.featured ? 'bg-white/12 text-[#93c5fd]' : 'bg-[#eef6ff] text-[#077ef6]'}`}>
                      <Check className="h-3.5 w-3.5" />
                    </span>
                    {feature}
                  </div>
                ))}
              </div>
              <Link to={plan.to} className={`mt-9 inline-flex h-11 w-full items-center justify-center gap-2 rounded-[8px] text-sm font-bold transition ${plan.featured ? 'bg-white text-[#030328] hover:bg-[#eef6ff]' : 'bg-[#077ef6] text-white hover:bg-[#0269d2]'}`}>
                {plan.cta}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-[#e3ddec] bg-white px-5 py-16 lg:px-8">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.8fr_1fr] lg:items-center">
          <div>
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Included foundation</p>
            <h2 className="mt-3 text-3xl font-black leading-tight text-[#05051f]">
              Every plan keeps your business ready to sell.
            </h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {comparisons.map((item) => (
              <div key={item} className="rounded-[8px] border border-[#e3ddec] bg-[#fbf8ff] p-4 text-sm font-bold text-[#4f4b63]">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <PublicFooter />
    </main>
  )
}
