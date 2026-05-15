import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Bot,
  Check,
  CreditCard,
  FileCheck2,
  MessageCircle,
  Send,
  TrendingUp,
} from 'lucide-react'

const navItems = ['Product', 'Solutions', 'Pricing', 'Resources']

const featureCards = [
  {
    title: 'WhatsApp native',
    body: 'Manage orders, answer queries, and send updates directly through WhatsApp.',
    icon: MessageCircle,
  },
  {
    title: 'Squad-powered payments',
    body: 'Fast checkout with integrated Squad payments and instant transaction records.',
    icon: CreditCard,
  },
  {
    title: 'Growth intelligence',
    body: 'AI turns sales activity into insights you can act on immediately.',
    icon: TrendingUp,
  },
]

const advancedCards = [
  {
    title: 'Advanced AI-driven analytics',
    body: 'Spot revenue patterns, campaign lift, product demand, and customer behavior without building spreadsheets.',
    icon: TrendingUp,
  },
  {
    title: 'Virtual accounts for businesses',
    body: 'Give every storefront cleaner payment collection, reconciliation, and business-ready money movement.',
    icon: CreditCard,
  },
  {
    title: 'Advanced AI features',
    body: 'Use AI to optimize product copy, recommend next actions, summarize operations, and surface growth opportunities.',
    icon: Bot,
  },
]

function CertificateMockup() {
  return (
    <div className="rounded-[8px] border border-[#dcd4eb] bg-white p-7 shadow-[0_18px_45px_rgba(35,18,82,0.1)]">
      <div className="flex items-center justify-between border-b border-[#eee8f7] pb-5">
        <div>
          <p className="text-[0.68rem] font-bold uppercase text-[#030328]">Certificate of Authenticity</p>
          <p className="mt-1 text-[0.68rem] text-[#77738c]">AAJE-BIZ-093481</p>
        </div>
        <FileCheck2 className="h-5 w-5 text-[#077ef6]" />
      </div>
      <div className="mt-6 grid gap-4 text-xs text-[#030328]">
        <div className="flex justify-between">
          <span className="text-[#77738c]">Item</span>
          <span>Artisan Leather Tote</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#77738c]">Date</span>
          <span>Oct 24, 2026</span>
        </div>
      </div>
      <div className="mx-auto mt-8 grid h-16 w-16 place-items-center rounded-[8px] border border-[#cfc8de] bg-[#f6f2fb]">
        <div className="grid h-10 w-10 grid-cols-3 gap-0.5">
          {Array.from({ length: 9 }).map((_, index) => (
            <span key={index} className={index % 2 === 0 ? 'bg-[#030328]' : 'bg-[#cfc8de]'} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Landing() {
  return (
    <main className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <section id="product" className="flex min-h-screen flex-col px-5 pb-16 pt-7 lg:px-8">
        <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto_1fr] items-center gap-6">
          <Link to="/" className="justify-self-start text-sm font-black text-[#077ef6]" aria-label="AAJE home">
            AAJE
          </Link>

          <div className="hidden items-center justify-center gap-8 text-xs font-medium text-[#4f4b63] md:flex">
            {navItems.map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`} className="transition hover:text-[#077ef6]">
                {item}
              </a>
            ))}
          </div>

          <div className="flex items-center justify-self-end gap-3">
            <Link to="/login" className="hidden text-xs font-semibold text-[#4f4b63] transition hover:text-[#077ef6] sm:inline-flex">
              Log in
            </Link>
            <Link
              to="/signup"
              className="inline-flex h-8 items-center rounded-[7px] bg-[#077ef6] px-4 text-xs font-bold text-white transition hover:bg-[#0269d2]"
            >
              Get started
            </Link>
          </div>
        </div>

        <div className="mx-auto mt-[12vh] max-w-5xl text-center">
          <h1 className="mx-auto max-w-4xl text-5xl font-[300] leading-[1.04] tracking-normal text-[#05051f]">
            Create your AI-powered storefront and run your business through WhatsApp.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-sm leading-6 text-[#625d75]">
            Operational excellence built for modern commerce. Launch seamlessly, accept payments, and let AI handle the heavy lifting while you connect directly with customers.
          </p>

          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/signup"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] bg-[#077ef6] px-5 text-sm font-bold text-white shadow-[0_16px_32px_rgba(7,126,246,0.25)] transition hover:bg-[#0269d2]"
            >
              Start building free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#solutions"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] border border-[#dcd6ea] bg-white/70 px-5 text-sm font-semibold text-[#4f4b63] transition hover:border-[#077ef6] hover:text-[#077ef6]"
            >
              <Send className="h-4 w-4" />
              Talk to sales
            </a>
          </div>
        </div>

        <div className="flex-1" aria-hidden="true" />
      </section>

      <section id="solutions" className="px-5 py-24 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div>
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Generative AI</p>
            <h2 className="mt-3 max-w-lg text-4xl font-black leading-tight text-[#05051f]">
              Instantly generate a premium storefront.
            </h2>
            <p className="mt-5 max-w-xl text-sm leading-7 text-[#625d75]">
              Describe your business, and our AI engine crafts a high-conversion storefront with polished copy, product sections, checkout flows, and a brand system that feels ready from day one.
            </p>
            <div className="mt-8 space-y-4">
              {['Auto-generated brand identity and copy.', 'Mobile-first, lightning-fast performance.', 'Inventory, payment, and notification logic included.'].map((item) => (
                <div key={item} className="flex items-center gap-3 text-sm font-medium text-[#4f4b63]">
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-[#ece6ff] text-[#077ef6]">
                    <Check className="h-3.5 w-3.5" />
                  </span>
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="px-5 pb-24 lg:px-8">
        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Placeholder removed */}

          <div className="lg:pl-6">
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Conversational business operation</p>
            <h2 className="mt-3 max-w-xl text-4xl font-black leading-tight text-[#05051f]">
              Manage your storefront from the WhatsApp conversations you already use.
            </h2>
            <p className="mt-5 max-w-xl text-sm leading-7 text-[#625d75]">
              AAJE turns WhatsApp into a business command center, so you can manage orders, confirm payments, update products, follow up with customers, and operate your storefront without switching tools.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {[
                'Reply to buyers and manage orders in one place.',
                'Receive payment, inventory, and delivery updates instantly.',
                'Run daily storefront tasks through simple chat actions.',
                'Keep customer conversations connected to every sale.',
              ].map((item) => (
                <div key={item} className="rounded-[8px] border border-[#e3ddec] bg-white/70 p-4 text-sm font-medium leading-6 text-[#4f4b63]">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="px-5 pb-24 lg:px-8">
        <div className="mx-auto max-w-7xl rounded-[8px] border border-[#030328] bg-[#030328] p-8 text-white sm:p-12">
          <div className="grid gap-12 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
            <div>
              <p className="text-[0.68rem] font-black uppercase text-[#93c5fd]">Intelligent finance layer</p>
              <h2 className="mt-4 max-w-xl text-4xl font-black leading-tight">
                Analytics, accounts, and AI tools for businesses ready to grow.
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-7 text-white/65">
                Move beyond a basic storefront with smarter financial infrastructure, stronger operational visibility, and AI features that help merchants make better decisions every day.
              </p>
              <div className="mt-8 space-y-4">
                {advancedCards.map((card) => (
                  <div key={card.title} className="flex gap-3 text-sm leading-6 text-white/74">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#077ef6]" />
                    <p>
                      <span className="font-bold text-white">{card.title}:</span> {card.body}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Placeholder removed */}
          </div>
        </div>
      </section>

      <section id="pricing" className="px-5 py-20 lg:px-8">
        <div className="mx-auto grid max-w-7xl items-center gap-12 rounded-[8px] border border-[#e3ddec] bg-white p-8 sm:p-12 lg:grid-cols-[1fr_0.9fr]">
          <div className="relative min-h-[560px]">
            {featureCards.map((feature, index) => {
              const Icon = feature.icon
              const positions = [
                { top: 0, left: '3%', rotate: '-4deg', zIndex: 3 },
                { top: 155, left: '15%', rotate: '3deg', zIndex: 2 },
                { top: 310, left: '7%', rotate: '-2deg', zIndex: 1 },
              ]
              return (
                <article
                  key={feature.title}
                  className="absolute w-[86%] rounded-[8px] border border-[#dcd4eb] bg-[#fcf9ff] p-6 shadow-[0_22px_55px_rgba(35,18,82,0.08)] transition hover:z-10 hover:-translate-y-1"
                  style={{
                    top: positions[index].top,
                    left: positions[index].left,
                    transform: `rotate(${positions[index].rotate})`,
                    zIndex: positions[index].zIndex,
                  }}
                >
                  <span className="grid h-10 w-10 place-items-center rounded-[8px] bg-[#f0eaff] text-[#077ef6]">
                    <Icon className="h-5 w-5" />
                  </span>
                  <h3 className="mt-7 text-lg font-black text-[#05051f]">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[#625d75]">{feature.body}</p>
                </article>
              )
            })}
          </div>

          <div className="lg:pl-6">
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Operational foundation</p>
            <h2 className="mt-4 max-w-xl text-4xl font-black leading-tight text-[#05051f]">
              Built for scale. Designed for simplicity.
            </h2>
            <p className="mt-5 max-w-xl text-sm leading-7 text-[#625d75]">
              Everything you need to run a high-growth operation, unified in one elegant platform.
            </p>
            {/* Placeholder removed */}
          </div>
        </div>
      </section>

      <section id="resources" className="px-5 py-20 lg:px-8">
        <div className="mx-auto grid max-w-7xl overflow-hidden rounded-[8px] border border-[#e3ddec] bg-[#eee8f7] lg:grid-cols-[1.15fr_0.85fr]">
          <div className="p-8 sm:p-12">
            <p className="text-[0.68rem] font-black uppercase text-[#625d75]">Economic identity</p>
            <h2 className="mt-4 max-w-xl text-3xl font-black leading-tight text-[#05051f]">
              Give every business a trusted economic identity.
            </h2>
            <p className="mt-5 max-w-xl text-sm leading-7 text-[#625d75]">
              Build a verifiable profile around sales history, customer trust, receipts, authenticity records, and business activity, so merchants can look credible from their first storefront to their next stage of growth.
            </p>
            <Link to="/signup" className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-[#077ef6]">
              Explore economic identity
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="bg-[#e5deef] p-8 sm:p-12">
            <CertificateMockup />
          </div>
        </div>
      </section>

      <section className="px-5 pb-20 lg:px-8">
        <div className="mx-auto max-w-5xl rounded-[8px] bg-[#077ef6] px-6 py-14 text-center text-white sm:px-12">
          <h2 className="mx-auto max-w-3xl text-4xl font-black leading-tight">
            Build the storefront, manage the operation, and grow from one place.
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-white/78">
            Start with an AI-generated storefront today, then unlock WhatsApp operations, analytics, virtual accounts, and business identity as you grow.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link
              to="/signup"
              className="inline-flex h-11 items-center justify-center rounded-[8px] bg-white px-5 text-sm font-bold text-[#077ef6] transition hover:bg-[#eef6ff]"
            >
              Start building free
            </Link>
            <Link
              to="/login"
              className="inline-flex h-11 items-center justify-center rounded-[8px] border border-white/35 px-5 text-sm font-bold text-white transition hover:bg-white/10"
            >
              Log in
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#e7e1ef] px-5 py-8 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 text-xs text-[#625d75] md:flex-row md:items-center md:justify-between">
          <Link to="/" className="font-black text-[#077ef6]">AAJE</Link>
          <div className="flex flex-wrap gap-5">
            <a href="#resources" className="hover:text-[#077ef6]">Terms of service</a>
            <a href="#resources" className="hover:text-[#077ef6]">Privacy policy</a>
            <a href="#resources" className="hover:text-[#077ef6]">Contact support</a>
            <a href="#solutions" className="hover:text-[#077ef6]">WhatsApp integration</a>
          </div>
          <p>© 2026 AAJE Commerce Platform.</p>
        </div>
      </footer>
    </main>
  )
}
