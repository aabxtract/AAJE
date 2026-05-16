import { Link } from 'react-router-dom'
import { Check, Plus } from 'lucide-react'

export function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
      <path fill="#4285F4" d="M22.6 12.2c0-.8-.1-1.6-.2-2.3H12v4.4h5.9c-.3 1.4-1 2.5-2.1 3.2v2.7h3.4c2-1.8 3.4-4.5 3.4-8z" />
      <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.4-2.7c-.9.6-2.1 1-3.9 1-3 0-5.5-2-6.4-4.8H2.1v2.8C3.9 20.4 7.6 23 12 23z" />
      <path fill="#FBBC05" d="M5.6 13.8c-.2-.6-.4-1.2-.4-1.8s.1-1.3.4-1.8V7.4H2.1C1.4 8.8 1 10.4 1 12s.4 3.2 1.1 4.6l3.5-2.8z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.6l3.1-3.1C17.5 2.1 15 1 12 1 7.6 1 3.9 3.6 2.1 7.4l3.5 2.8C6.5 7.4 9 5.4 12 5.4z" />
    </svg>
  )
}

export function GoogleAuthButton({ label = 'Continue with Google' }) {
  return (
    <button
      type="button"
      className="inline-flex h-11 w-full items-center justify-center gap-3 rounded-[8px] border border-[#e4e1ee] bg-white text-sm font-semibold text-[#17142f] transition hover:border-[#cfc8e3] hover:bg-[#fbf9ff]"
    >
      <GoogleIcon />
      {label}
    </button>
  )
}

export function AuthShell({ title, subtitle, children, footer }) {
  return (
    <main className="min-h-screen bg-white text-[#12102b] [font-family:'Montserrat_Alternates',_system-ui,_sans-serif]">
      <div className="grid min-h-screen lg:grid-cols-[1fr_1fr]">
        <section className="relative hidden overflow-hidden bg-[#5a4be7] lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_16%,rgba(255,255,255,0.18),transparent_30%)]" />
          <div className="relative z-10 flex h-full flex-col justify-between px-14 py-12 text-white">
            <Link to="/" className="inline-flex items-center">
              <img src="/IMG_5672.PNG" alt="AAJE" className="h-14" />
            </Link>

            <div className="max-w-xl">
              <h1 className="text-5xl font-semibold leading-tight">
                Start selling smarter with AAJE.
              </h1>
              <p className="mt-5 max-w-lg text-sm leading-7 text-white/82">
                Create a free account and unlock AI storefront generation, WhatsApp operations, payment tools, and business intelligence.
              </p>
            </div>

            <div className="overflow-hidden rounded-t-[8px] bg-white shadow-[0_30px_100px_rgba(17,10,75,0.26)]">
              <div className="flex h-10 items-center gap-2 border-b border-[#ece9f7] px-4">
                <span className="h-2.5 w-2.5 rounded-full bg-[#ff6b6b]" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#ffe45e]" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#82f4a0]" />
                <span className="ml-4 h-3 w-20 rounded-full bg-[#e8edf2]" />
                <Plus className="ml-auto h-4 w-4 text-[#12102b]" />
              </div>
              <div className="grid h-[390px] grid-cols-[74px_1fr]">
                <div className="bg-[#17124c] px-4 py-5">
                  <div className="grid h-9 w-9 place-items-center rounded-[8px] bg-white text-[#5a4be7]">
                    <Check className="h-4 w-4" />
                  </div>
                  <div className="mt-6 space-y-5">
                    {Array.from({ length: 8 }).map((_, index) => (
                      <span key={index} className={`block h-5 w-5 rounded-full ${index === 0 ? 'bg-[#6b5cff]' : 'bg-white'}`} />
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-[0.8fr_1.2fr] bg-[#f7f8fb] p-7">
                  <div className="space-y-5">
                    <div className="h-10 rounded-[8px] bg-[#17124c]" />
                    {Array.from({ length: 7 }).map((_, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <span className="h-4 w-4 rounded-full bg-[#dfe7ec]" />
                        <span className="h-2.5 w-24 rounded-full bg-[#dfe7ec]" />
                      </div>
                    ))}
                  </div>
                  <div className="rounded-[8px] bg-white/72 p-5">
                    <div className="h-8 w-32 rounded-full bg-[#dfe7ec]" />
                    <div className="mt-7 space-y-5">
                      {Array.from({ length: 6 }).map((_, index) => (
                        <div key={index} className="flex items-center gap-4">
                          <span className="h-4 w-4 rounded-full bg-[#dfe7ec]" />
                          <span className="h-3 w-20 rounded-full bg-[#dfe7ec]" />
                          <span className="h-5 w-5 rounded-full bg-[#dfe7ec]" />
                          <span className="h-2.5 flex-1 rounded-full bg-[#dfe7ec]" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-md">
            <Link to="/" className="mb-8 inline-flex">
              <img src="/IMG_5672.PNG" alt="AAJE" className="h-20" />
            </Link>
            <h2 className="text-3xl font-semibold tracking-[-0.01em] text-[#12102b]">{title}</h2>
            {subtitle && <p className="mt-3 text-sm leading-6 text-[#74708a]">{subtitle}</p>}
            <div className="mt-8">{children}</div>
            {footer && <div className="mt-6 text-center text-sm text-[#625d75]">{footer}</div>}
          </div>
        </section>
      </div>
    </main>
  )
}
