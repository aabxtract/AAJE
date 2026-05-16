import { Link } from 'react-router-dom'
import { ArrowRight, Mail, MessageCircle, Send } from 'lucide-react'
import PublicFooter from '../components/PublicFooter'

const contactOptions = [
  {
    title: 'Support',
    body: 'Get help with storefront setup, payments, dashboard access, and WhatsApp operations.',
    action: 'support@aaje.store',
    href: 'mailto:support@aaje.store',
    icon: Mail,
  },
  {
    title: 'Sales',
    body: 'Talk to the team about Premium, BizPrint visibility, and operational growth features.',
    action: 'sales@aaje.store',
    href: 'mailto:sales@aaje.store',
    icon: Send,
  },
  {
    title: 'WhatsApp',
    body: 'Reach out for lightweight setup guidance and business operations questions.',
    action: 'Contact support',
    href: 'mailto:support@aaje.store?subject=AAJE%20WhatsApp%20support',
    icon: MessageCircle,
  },
]

function ContactNav() {
  return (
    <nav className="border-b border-[#e7e1ef] bg-[#fbf8ff]/95 px-5 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6">
        <Link to="/" aria-label="AAJE home">
          <img src="/IMG_5663.PNG" alt="AAJE" className="h-32 object-contain" />
        </Link>
        <div className="hidden items-center gap-8 text-xs font-medium text-[#4f4b63] md:flex">
          <Link to="/#solutions" className="transition hover:text-[#077ef6]">Features</Link>
          <Link to="/pricing" className="transition hover:text-[#077ef6]">Pricing</Link>
          <Link to="/faqs" className="transition hover:text-[#077ef6]">FAQs</Link>
          <Link to="/contact" className="text-[#077ef6]">Contact Us</Link>
        </div>
        <Link to="/signup" className="inline-flex h-8 items-center rounded-[7px] bg-[#077ef6] px-4 text-xs font-bold text-white transition hover:bg-[#0269d2]">
          Get started
        </Link>
      </div>
    </nav>
  )
}

export default function Contact() {
  return (
    <main className="min-h-screen bg-[#fbf8ff] text-[#030328]">
      <ContactNav />

      <section className="px-5 py-20 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p className="text-[0.68rem] font-black uppercase text-[#077ef6]">Contact AAJE</p>
            <h1 className="mt-4 font-poppins text-5xl font-[600] leading-tight text-[#05051f]">
              Reach the team building your storefront operating system.
            </h1>
            <p className="mt-6 max-w-2xl text-sm leading-7 text-[#625d75]">
              Ask about storefront setup, Squad payments, WhatsApp operations, Premium, or BizPrint. The AAJE team will help route your question to the right place.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/signup" className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] bg-[#077ef6] px-5 text-sm font-bold text-white transition hover:bg-[#0269d2]">
                Create Your Store
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a href="mailto:support@aaje.store" className="inline-flex h-11 items-center justify-center gap-2 rounded-[8px] border border-[#dcd6ea] bg-white px-5 text-sm font-bold text-[#4f4b63] transition hover:border-[#077ef6] hover:text-[#077ef6]">
                <Mail className="h-4 w-4" />
                Email Support
              </a>
            </div>
          </div>

          <div className="grid gap-4">
            {contactOptions.map((option) => {
              const Icon = option.icon
              return (
                <a key={option.title} href={option.href} className="group rounded-[8px] border border-[#e3ddec] bg-white p-6 transition hover:-translate-y-1 hover:border-[#077ef6] hover:shadow-[0_18px_45px_rgba(35,18,82,0.1)]">
                  <div className="flex items-start gap-4">
                    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[8px] bg-[#eef6ff] text-[#077ef6]">
                      <Icon className="h-5 w-5" />
                    </span>
                    <div>
                      <h2 className="text-lg font-black text-[#05051f]">{option.title}</h2>
                      <p className="mt-2 text-sm leading-6 text-[#625d75]">{option.body}</p>
                      <p className="mt-4 text-sm font-black text-[#077ef6]">{option.action}</p>
                    </div>
                  </div>
                </a>
              )
            })}
          </div>
        </div>
      </section>

      <section className="border-t border-[#e3ddec] bg-white px-5 py-16 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-3">
          {['Storefront setup', 'Payment questions', 'WhatsApp operations'].map((item) => (
            <div key={item} className="rounded-[8px] border border-[#e3ddec] bg-[#fbf8ff] p-6">
              <h2 className="text-lg font-black text-[#05051f]">{item}</h2>
              <p className="mt-3 text-sm leading-7 text-[#625d75]">
                The team can help you understand how AAJE fits your current business workflow.
              </p>
            </div>
          ))}
        </div>
      </section>

      <PublicFooter />
    </main>
  )
}
