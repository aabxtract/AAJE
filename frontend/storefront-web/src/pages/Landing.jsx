import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import PublicFooter from '../components/PublicFooter'
import {
  ArrowRight,
  Bot,
  Check,
  ChevronDown,
  CreditCard,
  FileCheck2,
  Send,
  TrendingUp,
} from 'lucide-react'

const featureLinks = [
  { label: 'AI storefront setup', href: '#solutions' },
  { label: 'WhatsApp operations', href: '#whatsapp-operations' },
  { label: 'Payments and analytics', href: '#payments-analytics' },
  { label: 'BizPrint identity', href: '#bizprint' },
]

const featureCards = [
  {
    title: 'WhatsApp native',
    body: 'Manage orders, answer queries, and send updates directly through WhatsApp.',
    icon: '/whatsapp (1).png',
  },
  {
    title: 'Super powered payments',
    body: 'Fast checkout with integrated payments and instant transaction records.',
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
  const [isVisible, setIsVisible] = useState(false)
  const [isSolutionsVisible, setIsSolutionsVisible] = useState(false)
  const [isConversationalVisible, setIsConversationalVisible] = useState(false)
  const [isFinanceVisible, setIsFinanceVisible] = useState(false)
  const heroRef = useRef(null)
  const solutionsRef = useRef(null)
  const conversationalRef = useRef(null)
  const financeRef = useRef(null)

  useEffect(() => {
    const heroObserver = new IntersectionObserver(
      ([entry]) => setIsVisible(entry.isIntersecting),
      { threshold: 0.1 }
    )
    if (heroRef.current) heroObserver.observe(heroRef.current)

    const solutionsObserver = new IntersectionObserver(
      ([entry]) => setIsSolutionsVisible(entry.isIntersecting),
      { threshold: 0.1 }
    )
    if (solutionsRef.current) solutionsObserver.observe(solutionsRef.current)

    const conversationalObserver = new IntersectionObserver(
      ([entry]) => setIsConversationalVisible(entry.isIntersecting),
      { threshold: 0.1 }
    )
    if (conversationalRef.current) conversationalObserver.observe(conversationalRef.current)

    const financeObserver = new IntersectionObserver(
      ([entry]) => setIsFinanceVisible(entry.isIntersecting),
      { threshold: 0.1 }
    )
    if (financeRef.current) financeObserver.observe(financeRef.current)

    return () => {
      heroObserver.disconnect()
      solutionsObserver.disconnect()
      conversationalObserver.disconnect()
      financeObserver.disconnect()
    }
  }, [])

  return (
    <main className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <section id="product" className="relative flex min-h-[120dvh] flex-col overflow-hidden px-5 pt-0 lg:px-8">
        <nav className="z-50 w-full">
          <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto_1fr] items-center gap-6">
            <Link to="/" className="justify-self-start" aria-label="AAJE home">
              <img src="/IMG_5663.PNG" alt="AAJE" className="h-48 object-contain" />
            </Link>

            <div className="hidden items-center justify-center gap-8 text-xs font-medium text-[#4f4b63] md:flex">
              <div className="group relative">
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 py-3 transition hover:text-[#077ef6]"
                  aria-haspopup="true"
                >
                  Features
                  <ChevronDown className="h-3.5 w-3.5 transition group-hover:rotate-180" />
                </button>
                <div className="invisible absolute left-1/2 top-full z-50 w-56 -translate-x-1/2 rounded-[8px] border border-[#e3ddec] bg-white p-2 text-left opacity-0 shadow-[0_18px_45px_rgba(35,18,82,0.12)] transition group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100">
                  {featureLinks.map((item) => (
                    <a
                      key={item.href}
                      href={item.href}
                      className="block rounded-[7px] px-3 py-2.5 text-xs font-semibold text-[#4f4b63] transition hover:bg-[#eef6ff] hover:text-[#077ef6]"
                    >
                      {item.label}
                    </a>
                  ))}
                </div>
              </div>
              <Link to="/pricing" className="transition hover:text-[#077ef6]">
                Pricing
              </Link>
              <Link to="/faqs" className="transition hover:text-[#077ef6]">
                FAQs
              </Link>
              <Link to="/contact" className="transition hover:text-[#077ef6]">
                Contact Us
              </Link>
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
        </nav>

        <div className="mx-auto mt-4 max-w-5xl text-center">
          <h1 className="mx-auto max-w-4xl font-poppins text-5xl font-[600] leading-[1.04] tracking-normal text-[#05051f]">
            Create your AI-powered storefront and run your business through WhatsApp.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl font-poppins text-sm leading-6 text-[#625d75]">
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
            <Link
              to="/contact-us"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] border border-[#dcd6ea] bg-white/70 px-5 text-sm font-semibold text-[#4f4b63] transition hover:border-[#077ef6] hover:text-[#077ef6]"
            >
              <Send className="h-4 w-4" />
              Talk to sales
            </Link>
          </div>
        </div>

        <div ref={heroRef} className="relative mx-auto mt-8 w-full max-w-5xl flex-1">
          <img 
            src="/hero-image.png" 
            alt="AAJE Dashboard" 
            className={`absolute left-0 top-0 w-full rounded-t-2xl border-x border-t border-[#e4e1ee] object-cover object-top shadow-[0_-10px_40px_rgba(42,25,91,0.08)] transition-all duration-1000 ease-out ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
            }`} 
          />
          <img 
            src="/output-onlinegiftools.gif" 
            alt="AI Interaction" 
            className={`absolute -right-4 top-8 z-10 w-48 transition-all duration-700 delay-500 ease-out sm:-right-8 sm:top-16 sm:w-64 ${
              isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
            }`}
          />
        </div>
      </section>

      <section id="solutions" ref={solutionsRef} className="bg-white px-5 py-24 lg:px-8 overflow-hidden">
        <div className="mx-auto max-w-7xl grid lg:grid-cols-2 items-center gap-16">
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
          <div className="relative">
            <img 
              src="/pc mkc.png" 
              alt="Storefront Preview" 
              className={`w-[140%] max-w-none drop-shadow-2xl rounded-xl lg:translate-x-[45%] transition-all duration-1000 ease-out ${
                isSolutionsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
              }`}
            />
          </div>
        </div>
      </section>

      <section id="whatsapp-operations" ref={conversationalRef} className="px-5 pt-32 pb-0 lg:px-8 overflow-hidden">
        <div className="mx-auto grid max-w-7xl items-end gap-20 lg:grid-cols-2">
          <div className={`relative lg:-ml-20 transition-all duration-1000 ease-out ${
            isConversationalVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'
          }`}>
            <img 
              src="/ChatGPT Image May 15, 2026, 07_05_05 PM.png" 
              alt="WhatsApp Operations Mockup" 
              className="w-[125%] max-w-none drop-shadow-2xl rounded-t-2xl"
            />
            <img 
              src="/whatsapp.png" 
              alt="WhatsApp Logo" 
              className="absolute bottom-24 right-[18%] w-14 sm:w-18 drop-shadow-[0_15px_30px_rgba(37,211,102,0.3)] transition-all duration-700 hover:rotate-[360deg] cursor-pointer z-20"
            />
          </div>
          <div className="pb-24 pt-[50px] lg:pl-12">
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

      <section id="payments-analytics" ref={financeRef} className="bg-[#030328] px-5 pt-24 text-white lg:px-8 overflow-hidden">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
            <div className="pb-24">
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

            <div className={`relative transition-all duration-1000 ease-out ${
              isFinanceVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'
            }`}>
              <img 
                src="/mock-pic.png" 
                alt="Finance Analytics Mockup" 
                className="w-[140%] max-w-none"
              />
              <img 
                src="/orders notification.png" 
                alt="Orders Notification" 
                className={`absolute -right-12 top-10 z-10 w-64 transition-all duration-700 delay-500 ease-out ${
                  isFinanceVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
                }`}
              />
              <img 
                src="/new withdrwal.png" 
                alt="New Withdrawal Notification" 
                className={`absolute left-40 bottom-60 z-10 w-60 transition-all duration-700 delay-700 ease-out ${
                  isFinanceVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
                }`}
              />
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="py-24 border-y border-[#e3ddec] bg-white overflow-hidden">
        <div className="mx-auto grid max-w-none px-6 sm:px-12 lg:px-24 items-center gap-20 lg:grid-cols-[1fr_0.8fr]">
          <div className="relative min-h-[640px] group">
            {featureCards.map((feature, index) => {
              const Icon = feature.icon
              const positions = [
                { top: 0, left: '3%', rotate: '-4deg', zIndex: 3 },
                { top: 155, left: '15%', rotate: '3deg', zIndex: 2 },
                { top: 310, left: '7%', rotate: '-2deg', zIndex: 1 },
              ]
              const hoverTransforms = [
                'group-hover:-translate-y-16 group-hover:-translate-x-8 group-hover:-rotate-[12deg]',
                'group-hover:scale-105',
                'group-hover:translate-y-16 group-hover:translate-x-8 group-hover:rotate-[12deg]',
              ]
              return (
                <article
                  key={feature.title}
                  className={`absolute w-[85%] max-w-[440px] rounded-[16px] border border-[#dcd4eb] bg-white p-8 shadow-[0_22px_55px_rgba(35,18,82,0.08)] transition-all duration-500 hover:z-10 hover:shadow-[0_32px_70px_rgba(35,18,82,0.12)] ${hoverTransforms[index]} ${index === 0 ? '-rotate-4' : index === 1 ? 'rotate-3' : '-rotate-2'}`}
                  style={{
                    top: positions[index].top,
                    left: positions[index].left,
                    zIndex: positions[index].zIndex,
                  }}
                >
                  <span className="grid h-10 w-10 place-items-center rounded-[8px] bg-[#f0eaff] text-[#077ef6]">
                    {typeof feature.icon === 'string' ? (
                      <img src={feature.icon} alt={feature.title} className="h-6 w-6 object-contain" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </span>
                  <h3 className="mt-7 text-lg font-black text-[#05051f]">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[#625d75]">{feature.body}</p>
                </article>
              )
            })}
          </div>

          <div className="lg:pl-6 relative">
            <img 
              src="/stroked.png" 
              alt="" 
              className="absolute right-0 top-1/2 -translate-y-1/2 w-[180%] max-w-none translate-x-[50%] opacity-30 z-0 pointer-events-none select-none"
            />
            <div className="relative z-10">
              <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Operational foundation</p>
              <h2 className="mt-4 max-w-xl text-4xl font-black leading-tight text-[#05051f]">
                Built for scale. Designed for simplicity.
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-7 text-[#625d75]">
                Everything you need to run a high-growth operation, unified in one elegant platform.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="bizprint" className="py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-7xl grid overflow-hidden bg-[#eee8f7] lg:grid-cols-2 items-center rounded-[32px] shadow-sm">
          <div className="p-12 sm:p-16 lg:p-20">
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Economic identity</p>
            <h2 className="mt-4 text-3xl font-black leading-tight text-[#05051f] lg:text-4xl">
              Give every business a trusted economic identity.
            </h2>
            <p className="mt-6 text-sm leading-7 text-[#625d75]">
              Build a verifiable profile around sales history, customer trust, receipts, authenticity records, and business activity, so merchants can look credible from their first storefront to their next stage of growth.
            </p>
            <Link to="/signup" className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-[#077ef6] transition hover:gap-3">
              Explore economic identity
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="relative flex items-center justify-center p-8 lg:p-16 h-full bg-[#e5deef]/50">
            <img 
              src="/ChatGPT Image May 16, 2026, 05_09_26 AM.png" 
              alt="Economic Identity" 
              className="w-full max-w-[440px] rounded-2xl shadow-[0_32px_64px_rgba(35,18,82,0.15)]"
            />
          </div>
        </div>
      </section>

      <section className="pb-20">
        <div className="max-w-none bg-[#077ef6] px-6 py-24 text-center text-white sm:px-12">
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

      <PublicFooter />
    </main>
  )
}
