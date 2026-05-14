import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  CreditCard,
  ExternalLink,
  MessageCircle,
  PackageCheck,
  Sparkles,
  Store,
  TrendingUp,
} from 'lucide-react'

const heroImage =
  'https://images.unsplash.com/photo-1556740758-90de374c12ad?auto=format&fit=crop&w=1800&q=85'

const storeImage =
  'https://images.unsplash.com/photo-1607083206968-13611e3d76db?auto=format&fit=crop&w=1200&q=85'

const productImage =
  'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85'

const campaignImage =
  'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=85'

const flowSteps = [
  { label: 'Describe your business', icon: Sparkles },
  { label: 'AI drafts your store', icon: Store },
  { label: 'Add products or services', icon: PackageCheck },
  { label: 'Customer checks out', icon: CreditCard },
  { label: 'WhatsApp updates you', icon: MessageCircle },
]

const metrics = [
  { value: '1', label: 'free storefront to launch' },
  { value: '4', label: 'items per guest checkout' },
  { value: '8PM', label: 'daily WhatsApp summary' },
]

const operations = [
  {
    title: 'AI storefront generation',
    body: 'Turn a short business description into store copy, categories, layout, and starter products.',
    icon: Sparkles,
  },
  {
    title: 'Squad checkout loop',
    body: 'Create pending orders, initiate sandbox payments, mark paid orders, and reduce inventory after success.',
    icon: CreditCard,
  },
  {
    title: 'WhatsApp operations',
    body: 'Send order, payment, low-stock, and daily sales notifications from the same central backend.',
    icon: MessageCircle,
  },
  {
    title: 'Campaign attribution',
    body: 'Track Instagram, WhatsApp Status, Facebook, and TikTok links through visits and conversions.',
    icon: TrendingUp,
  },
]

export default function Landing() {
  return (
    <main className="min-h-screen bg-[#f7f8f4] text-[#111827]">
      <header className="fixed left-0 right-0 top-0 z-30 border-b border-white/20 bg-[#0f172a]/70 backdrop-blur-xl">
        <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-2 text-white" aria-label="AAJE home">
            <span className="grid h-8 w-8 place-items-center rounded-md bg-white text-sm font-black text-[#0f172a]">
              A
            </span>
            <span className="text-sm font-semibold tracking-wide">AAJE</span>
          </Link>

          <div className="hidden items-center gap-7 text-sm text-white/78 md:flex">
            <a href="#platform" className="transition hover:text-white">Platform</a>
            <a href="#flow" className="transition hover:text-white">Flow</a>
            <a href="#pricing" className="transition hover:text-white">Access</a>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/signup"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-white px-4 text-sm font-semibold text-[#0f172a] transition hover:bg-[#dff7e8]"
            >
              Get started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </nav>
      </header>

      <section className="relative flex min-h-[92vh] items-end overflow-hidden">
        <img
          src={heroImage}
          alt="Merchant using a phone to run online sales"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-[#07111f]/70" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#f7f8f4] to-transparent" />

        <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-8 px-4 pb-16 pt-28 sm:px-6 lg:grid-cols-[1fr_420px] lg:px-8">
          <div className="max-w-4xl text-white">
            <p className="inline-flex items-center gap-2 rounded-md border border-white/25 bg-white/10 px-3 py-1 text-xs font-semibold uppercase text-[#dff7e8]">
              <Sparkles className="h-3.5 w-3.5" />
              AI-native storefronts for WhatsApp sellers
            </p>
            <h1 className="mt-6 max-w-4xl text-5xl font-semibold leading-[1.02] sm:text-6xl lg:text-7xl">
              Launch a store, collect payments, and run the business from WhatsApp.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
              AAJE creates a storefront from your business description, handles products, checkout, Squad sandbox payments, orders, inventory, BizPrint, and notifications through one backend.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/signup"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#dff7e8] px-5 text-sm font-bold text-[#0f172a] transition hover:bg-white"
              >
                Build my store
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#flow"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-white/25 px-5 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                See the flow
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>

          <div className="hidden self-end rounded-md border border-white/18 bg-white/12 p-4 shadow-2xl backdrop-blur-xl lg:block">
            <div className="rounded-md bg-[#f8fafc] p-4 text-[#111827]">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div>
                  <p className="text-xs font-semibold uppercase text-slate-500">Today</p>
                  <p className="text-xl font-bold">NGN 128,400</p>
                </div>
                <span className="rounded-md bg-[#0f172a] px-3 py-1 text-xs font-semibold text-white">Paid</span>
              </div>
              <div className="mt-4 space-y-3">
                {['WhatsApp order alert sent', 'Inventory reduced after payment', 'BizPrint score refreshed'].map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span className="text-sm font-medium">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-3 px-4 pb-16 sm:px-6 md:grid-cols-3 lg:px-8">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-md border border-[#d9dfd4] bg-white p-6">
            <p className="text-4xl font-semibold text-[#0f172a]">{metric.value}</p>
            <p className="mt-2 text-sm text-slate-600">{metric.label}</p>
          </div>
        ))}
      </section>

      <section id="platform" className="border-y border-[#d9dfd4] bg-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
          <div>
            <p className="text-xs font-bold uppercase text-emerald-700">One central backend</p>
            <h2 className="mt-4 max-w-xl text-4xl font-semibold leading-tight text-[#0f172a]">
              Storefront, WhatsApp, payments, inventory, and intelligence in one operating loop.
            </h2>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {operations.map((item) => {
              const Icon = item.icon
              return (
                <article key={item.title} className="rounded-md border border-slate-200 bg-[#fbfcf8] p-5">
                  <Icon className="h-5 w-5 text-[#0f766e]" />
                  <h3 className="mt-5 text-lg font-semibold text-[#0f172a]">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
                </article>
              )
            })}
          </div>
        </div>
      </section>

      <section id="flow" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="overflow-hidden rounded-md border border-[#d9dfd4] bg-white">
            <img src={storeImage} alt="Online product storefront preview" className="h-72 w-full object-cover" />
            <div className="grid gap-3 p-4 md:grid-cols-2">
              <div className="rounded-md bg-[#eef8f1] p-4">
                <p className="text-xs font-bold uppercase text-emerald-800">Store link</p>
                <p className="mt-2 font-mono text-sm text-[#0f172a]">aaje.store/ada-skincare</p>
              </div>
              <div className="rounded-md bg-[#eff6ff] p-4">
                <p className="text-xs font-bold uppercase text-blue-800">Campaign</p>
                <p className="mt-2 font-mono text-sm text-[#0f172a]">?ref=whatsapp_status</p>
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs font-bold uppercase text-emerald-700">Demo loop</p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight text-[#0f172a]">
              The user flow is built around one sale.
            </h2>
            <div className="mt-8 space-y-3">
              {flowSteps.map((step, index) => {
                const Icon = step.icon
                return (
                  <div key={step.label} className="flex items-center gap-4 rounded-md border border-[#d9dfd4] bg-white p-4">
                    <span className="grid h-10 w-10 place-items-center rounded-md bg-[#0f172a] text-sm font-bold text-white">
                      {index + 1}
                    </span>
                    <Icon className="h-5 w-5 text-[#0f766e]" />
                    <p className="font-semibold text-[#111827]">{step.label}</p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#101820] text-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-20 sm:px-6 lg:grid-cols-3 lg:px-8">
          <div className="lg:col-span-1">
            <p className="text-xs font-bold uppercase text-[#dff7e8]">Dashboard-ready</p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight">Your sales story becomes usable data.</h2>
          </div>

          <div className="grid gap-3 lg:col-span-2 md:grid-cols-3">
            <div className="rounded-md border border-white/12 bg-white/8 p-5">
              <BarChart3 className="h-5 w-5 text-[#dff7e8]" />
              <p className="mt-8 text-3xl font-semibold">NGN 0</p>
              <p className="mt-2 text-sm text-white/65">today sales before launch</p>
            </div>
            <div className="rounded-md border border-white/12 bg-white/8 p-5">
              <img src={productImage} alt="Product inventory item" className="h-24 w-full rounded-md object-cover" />
              <p className="mt-4 font-semibold">Low-stock alerts</p>
              <p className="mt-2 text-sm text-white/65">stock triggers when quantity reaches threshold</p>
            </div>
            <div className="rounded-md border border-white/12 bg-white/8 p-5">
              <img src={campaignImage} alt="Campaign analytics on laptop" className="h-24 w-full rounded-md object-cover" />
              <p className="mt-4 font-semibold">Premium attribution</p>
              <p className="mt-2 text-sm text-white/65">visits, carts, conversions, and revenue by source</p>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-xs font-bold uppercase text-emerald-700">Access rules</p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight text-[#0f172a]">
              Start free, then unlock deeper operations when the store grows.
            </h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-[#d9dfd4] bg-white p-6">
              <h3 className="text-2xl font-semibold">Free</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                One store, AI store generation, product limits, guest checkout, Squad payments, basic inventory, dashboard, daily WhatsApp summary, and basic BizPrint.
              </p>
            </div>
            <div className="rounded-md border border-[#0f172a] bg-[#0f172a] p-6 text-white">
              <h3 className="text-2xl font-semibold">Premium</h3>
              <p className="mt-3 text-sm leading-6 text-white/70">
                Campaign links, advanced WhatsApp operations, deeper analytics, AI product optimization, detailed BizPrint, and multi-store support later.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 flex justify-center">
          <Link
            to="/signup"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#0f172a] px-6 text-sm font-bold text-white transition hover:bg-[#0f766e]"
          >
            Create your AAJE account
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </main>
  )
}
