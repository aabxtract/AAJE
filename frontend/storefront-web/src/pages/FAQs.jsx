import { Link } from 'react-router-dom'
import { ArrowRight, ChevronDown } from 'lucide-react'
import PublicFooter from '../components/PublicFooter'

const faqSections = [
  {
    category: 'General',
    items: [
      {
        question: 'What is AAJE?',
        answer: 'AAJE is an AI-native storefront platform that helps businesses create online stores, accept payments, track inventory, and manage operations through WhatsApp.',
      },
      {
        question: 'Who is AAJE built for?',
        answer: (
          <>
            <p>AAJE is built for WhatsApp sellers, Instagram businesses, creators, freelancers, vendors, small businesses, and social commerce businesses.</p>
            <p className="mt-3">If you already sell online but still manage operations manually, AAJE is built for you.</p>
          </>
        ),
      },
      {
        question: 'Do I need technical skills to use AAJE?',
        answer: (
          <>
            <p>No.</p>
            <p className="mt-3">AAJE is designed to simplify setup and operations. The AI onboarding assistant helps configure your storefront, products, and branding in minutes.</p>
          </>
        ),
      },
      {
        question: 'Is AAJE a marketplace?',
        answer: 'No. AAJE gives businesses their own storefront and operational tools. Customers buy directly from your store.',
      },
    ],
  },
  {
    category: 'Storefronts',
    items: [
      {
        question: 'How does the AI storefront setup work?',
        answer: (
          <>
            <p>During onboarding, AAJE asks questions about your business, products, style, and audience.</p>
            <p className="mt-3">The AI then helps generate your storefront structure, product categories, branding, starter products, and store descriptions. You can edit everything afterward.</p>
          </>
        ),
      },
      {
        question: 'Can I customize my storefront?',
        answer: 'Yes. You can edit products, change descriptions, upload images, update inventory, and modify sections and branding.',
      },
      {
        question: 'What type of businesses can use AAJE?',
        answer: (
          <>
            <p>AAJE supports products, services, creators, freelancers, digital sellers, and physical businesses.</p>
            <p className="mt-3">Examples include gadget sellers, fashion vendors, food businesses, beauty brands, photographers, and designers.</p>
          </>
        ),
      },
      {
        question: 'Will my store have a public link?',
        answer: (
          <>
            <p>Yes. Every store receives a public link like aaje.store/yourbusiness.</p>
            <p className="mt-3">You can share it across WhatsApp, Instagram, TikTok, Facebook, and X/Twitter.</p>
          </>
        ),
      },
    ],
  },
  {
    category: 'Payments',
    items: [
      {
        question: 'How do payments work?',
        answer: 'AAJE uses Squad APIs for payment processing. Customers can add items to cart, checkout securely, and pay online through Squad-powered checkout.',
      },
      {
        question: 'Does AAJE hold my money?',
        answer: 'No. Payments are processed through Squad infrastructure and routed according to your setup.',
      },
      {
        question: 'Can I connect my bank account?',
        answer: 'Yes. Businesses can connect their payout bank accounts during setup.',
      },
      {
        question: 'What are Squad virtual accounts?',
        answer: 'Businesses can optionally activate Squad virtual accounts for cleaner payment collection and operational visibility.',
      },
      {
        question: 'What happens after a successful payment?',
        answer: 'Once payment succeeds, the order is confirmed, inventory updates automatically, your dashboard updates, and WhatsApp notifications can be triggered.',
      },
    ],
  },
  {
    category: 'WhatsApp Operations',
    items: [
      {
        question: 'What can I do through WhatsApp?',
        answer: 'AAJE supports lightweight conversational business operations, including sales notifications, low stock alerts, operational summaries, and sales questions like "What sold today?" or "Show low stock".',
      },
      {
        question: 'Is the WhatsApp assistant a chatbot?',
        answer: "AAJE's WhatsApp assistant is designed as an operational business layer, not a generic chatbot. It focuses on helping businesses monitor and manage operations conversationally.",
      },
      {
        question: 'Do I need WhatsApp to use AAJE?',
        answer: 'No. WhatsApp operations are optional, but recommended for operational updates and conversational workflows.',
      },
      {
        question: 'Can I receive sales notifications on WhatsApp?',
        answer: 'Yes. You can receive sales summaries, order notifications, low stock alerts, and operational updates.',
      },
    ],
  },
  {
    category: 'Pricing',
    items: [
      {
        question: 'Is AAJE free?',
        answer: 'Yes. AAJE offers a free plan that includes 1 storefront, product listings, Squad payments, basic inventory, dashboard access, and WhatsApp sales notifications.',
      },
      {
        question: 'What is included in Premium?',
        answer: 'Premium unlocks campaign analytics, advanced WhatsApp operations, richer BizPrint visibility, AI operational insights, and advanced business visibility features.',
      },
      {
        question: 'How much is Premium?',
        answer: 'Premium currently costs ₦3,000/month.',
      },
      {
        question: 'Can I upgrade later?',
        answer: 'Yes. You can upgrade from Free to Premium anytime.',
      },
    ],
  },
  {
    category: 'BizPrint',
    items: [
      {
        question: 'What is BizPrint?',
        answer: "BizPrint is AAJE's measurable business activity profile. It helps businesses track operational consistency and activity across sales, inventory, orders, storefront activity, and campaign performance.",
      },
      {
        question: 'Is BizPrint a credit score?',
        answer: 'No. BizPrint is not a traditional credit score. It is a lightweight operational business activity profile.',
      },
      {
        question: 'What affects my BizPrint?',
        answer: 'BizPrint may consider completed sales, inventory activity, operational consistency, storefront setup, and campaign engagement.',
      },
    ],
  },
  {
    category: 'Security & Accounts',
    items: [
      {
        question: 'Is my data secure?',
        answer: 'AAJE uses secure authentication and trusted payment infrastructure through Squad APIs.',
      },
      {
        question: 'Can customers checkout without creating accounts?',
        answer: 'Yes. AAJE supports guest checkout for faster purchases.',
      },
      {
        question: 'Can I manage multiple stores?',
        answer: 'Multiple storefront support is planned for future premium expansion.',
      },
      {
        question: 'Is AAJE available on mobile?',
        answer: 'Yes. AAJE is designed mobile-first and optimized for modern mobile browsers.',
      },
    ],
  },
]

const faqCategoryId = (category) => category.toLowerCase().replace(/&/g, 'and').replace(/\s+/g, '-')

function PublicNav() {
  return (
    <nav className="border-b border-[#e7e1ef] bg-[#fbf8ff]/95 px-5 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6">
        <Link to="/" aria-label="AAJE home">
          <img src="/IMG_5663.PNG" alt="AAJE" className="h-32 object-contain" />
        </Link>
        <div className="hidden items-center gap-8 text-xs font-medium text-[#4f4b63] md:flex">
          <Link to="/#solutions" className="transition hover:text-[#077ef6]">Features</Link>
          <Link to="/pricing" className="transition hover:text-[#077ef6]">Pricing</Link>
          <Link to="/faqs" className="text-[#077ef6]">FAQs</Link>
          <Link to="/contact" className="transition hover:text-[#077ef6]">Contact Us</Link>
        </div>
        <Link to="/signup" className="inline-flex h-8 items-center rounded-[7px] bg-[#077ef6] px-4 text-xs font-bold text-white transition hover:bg-[#0269d2]">
          Get started
        </Link>
      </div>
    </nav>
  )
}

export default function FAQs() {
  return (
    <main className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <PublicNav />

      <section className="px-5 py-20 text-center lg:px-8">
        <div className="mx-auto max-w-4xl">
          <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">AAJE support</p>
          <h1 className="mt-4 font-poppins text-5xl font-[600] leading-tight text-[#05051f]">
            Frequently Asked Questions
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-[#625d75]">
            Everything you need to know about creating storefronts, accepting payments, and managing your business with AAJE.
          </p>
        </div>
      </section>

      <section className="px-5 pb-24 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[260px_1fr]">
          <aside className="hidden lg:block">
            <div className="sticky top-6 space-y-2 rounded-[8px] border border-[#e3ddec] bg-white p-3">
              {faqSections.map((section) => (
                <a key={section.category} href={`#${faqCategoryId(section.category)}`} className="block rounded-[7px] px-3 py-2 text-xs font-bold text-[#625d75] transition hover:bg-[#eef6ff] hover:text-[#077ef6]">
                  {section.category}
                </a>
              ))}
            </div>
          </aside>

          <div className="space-y-10">
            {faqSections.map((section) => (
              <section key={section.category} id={faqCategoryId(section.category)} className="scroll-mt-8">
                <h2 className="mb-4 text-2xl font-black text-[#05051f]">{section.category}</h2>
                <div className="divide-y divide-[#e3ddec] overflow-hidden rounded-[8px] border border-[#e3ddec] bg-white">
                  {section.items.map((item, index) => (
                    <details key={item.question} className="group" open={index === 0}>
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-5 text-left text-sm font-black text-[#05051f] transition hover:bg-[#f7f2ff]">
                        {item.question}
                        <ChevronDown className="h-4 w-4 shrink-0 text-[#077ef6] transition group-open:rotate-180" />
                      </summary>
                      <div className="px-5 pb-5 text-sm leading-7 text-[#625d75]">
                        {typeof item.answer === 'string' ? <p>{item.answer}</p> : item.answer}
                      </div>
                    </details>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      </section>

      <section className="px-5 pb-20 lg:px-8">
        <div className="mx-auto max-w-5xl rounded-[8px] bg-[#030328] px-6 py-14 text-center text-white sm:px-12">
          <h2 className="mx-auto max-w-3xl text-4xl font-black leading-tight">
            Still have questions?
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-white/72">
            Reach out to the AAJE team or create your storefront to explore the platform yourself.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link to="/signup" className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] bg-white px-5 text-sm font-bold text-[#030328] transition hover:bg-[#eef6ff]">
              Create Your Store
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/contact" className="inline-flex h-11 items-center justify-center rounded-[8px] border border-white/35 px-5 text-sm font-bold text-white transition hover:bg-white/10">
              Contact Support
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </main>
  )
}
