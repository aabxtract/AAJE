const footerLinks = [
  { label: 'Terms', href: '#' },
  { label: 'Privacy Policy', href: '#' },
  { label: 'Ambassadors', href: '#' },
  { label: 'Careers', href: '#' },
  { label: 'Twitter', href: '#' },
  { label: 'Facebook', href: '#' },
]

export default function PublicFooter() {
  return (
    <footer className="relative h-[520px] overflow-hidden border-t border-[#e8edf5] bg-[#f8fafc] px-6 pt-[105px] sm:px-12 lg:px-24">
      <div className="relative z-10 mx-auto flex max-w-7xl flex-col gap-8 text-[15px] font-semibold text-[#030328] md:flex-row md:items-start md:justify-between">
        <nav className="flex flex-wrap gap-x-10 gap-y-4" aria-label="Footer navigation">
          {footerLinks.map((link) => (
            <a key={link.label} href={link.href} className="transition hover:text-[#077ef6]">
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex flex-col gap-1 md:items-end">
          <p className="text-[#7a8494]">&copy; 2026 copyright all rights reserved.</p>
          <p className="text-xs text-[#7a8494] font-medium">Operated by WEB3 LAB CONCEPT.</p>
        </div>
      </div>

      <img
        src="/IMG_5663.PNG"
        alt="AAJE"
        className="pointer-events-none absolute left-1/2 top-[180px] w-[1800px] max-w-none -translate-x-1/2 select-none opacity-100 z-0 sm:w-[2200px] lg:w-[3200px]"
      />
    </footer>
  )
}
