/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── AAJE Brand Core ──────────────────────────────
        brand: {
          navy:     '#077EF6',   // electric blue — primary CTA
          dark:     '#030328',   // near-black navy — backgrounds, text
          white:    '#FFFFFF',
        },

        // ── Neo-brutalist Accent Palette ─────────────────
        accent: {
          yellow:   '#FFE45E',   // warm golden
          coral:    '#FF6B6B',   // lively red-orange
          green:    '#82F4A0',   // mint / soft lime
          lavender: '#C4B5FD',   // soft purple
          sky:      '#93C5FD',   // cool blue highlight
          cream:    '#FFF8F0',   // warm off-white bg
          peach:    '#FFD4C2',   // soft coral tint
        },

        // ── Surfaces ─────────────────────────────────────
        surface: {
          base:     '#FAFAFA',   // page background
          card:     '#FFFFFF',   // card fill
          muted:    '#F4F4F8',   // muted panels
          border:   '#111111',   // brutalist stroke
          subtle:   '#E8E8F0',   // light divider
        },

        // ── Semantic ─────────────────────────────────────
        ink: {
          DEFAULT:  '#030328',
          muted:    '#6B7280',
          faint:    '#9CA3AF',
        },

        // ── Status ───────────────────────────────────────
        ok:     '#16A34A',
        warn:   '#D97706',
        danger: '#DC2626',
      },

      // ── Typography ─────────────────────────────────────
      fontFamily: {
        display: ['"Montserrat Alternates"', 'system-ui', 'sans-serif'],
        body:    ['"Montserrat Alternates"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem',  { lineHeight: '0.875rem', letterSpacing: '0.05em' }],
        xs:    ['0.75rem',   { lineHeight: '1rem' }],
        sm:    ['0.875rem',  { lineHeight: '1.25rem' }],
        base:  ['1rem',      { lineHeight: '1.6rem' }],
        lg:    ['1.125rem',  { lineHeight: '1.75rem' }],
        xl:    ['1.25rem',   { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem',    { lineHeight: '2rem' }],
        '3xl': ['1.875rem',  { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem',   { lineHeight: '2.75rem', letterSpacing: '-0.02em' }],
        '5xl': ['3rem',      { lineHeight: '3.5rem',  letterSpacing: '-0.03em' }],
        '6xl': ['3.75rem',   { lineHeight: '4.25rem', letterSpacing: '-0.04em' }],
        '7xl': ['4.5rem',    { lineHeight: '5rem',    letterSpacing: '-0.04em' }],
        '8xl': ['6rem',      { lineHeight: '6.5rem',  letterSpacing: '-0.05em' }],
      },

      // ── Spacing ────────────────────────────────────────
      spacing: {
        '4.5': '1.125rem',
        '13':  '3.25rem',
        '15':  '3.75rem',
        '18':  '4.5rem',
        '22':  '5.5rem',
        '26':  '6.5rem',
        '30':  '7.5rem',
      },

      // ── Border radius ──────────────────────────────────
      borderRadius: {
        'none': '0',
        'sm':   '6px',
        DEFAULT:'10px',
        'md':   '14px',
        'lg':   '18px',
        'xl':   '22px',
        '2xl':  '28px',
        '3xl':  '36px',
        'full': '9999px',
      },

      // ── Border width ───────────────────────────────────
      borderWidth: {
        DEFAULT: '1px',
        '1.5':   '1.5px',
        '2':     '2px',
        '2.5':   '2.5px',
        '3':     '3px',
      },

      // ── Neo-brutalist shadows ──────────────────────────
      boxShadow: {
        'brut-sm':  '2px 2px 0px 0px #111111',
        'brut':     '4px 4px 0px 0px #111111',
        'brut-md':  '6px 6px 0px 0px #111111',
        'brut-lg':  '8px 8px 0px 0px #111111',
        'brut-xl':  '12px 12px 0px 0px #111111',
        'brut-navy':'4px 4px 0px 0px #077EF6',
        'brut-yellow':'4px 4px 0px 0px #FFE45E',
        'brut-coral':'4px 4px 0px 0px #FF6B6B',
        'soft-sm':  '0 1px 4px 0 rgba(3,3,40,0.08)',
        'soft':     '0 4px 16px 0 rgba(3,3,40,0.10)',
        'soft-md':  '0 8px 24px 0 rgba(3,3,40,0.12)',
        'soft-lg':  '0 16px 40px 0 rgba(3,3,40,0.14)',
        'glow-navy':'0 0 0 3px rgba(7,126,246,0.25)',
        'glow-yellow':'0 0 0 3px rgba(255,228,94,0.4)',
        'none': 'none',
      },

      // ── Animation ──────────────────────────────────────
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
        '500': '500ms',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideRight: {
          '0%':   { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%':      { transform: 'translateY(-12px) rotate(3deg)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.5' },
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-2deg)' },
          '50%':      { transform: 'rotate(2deg)' },
        },
        pop: {
          '0%':   { transform: 'scale(0.92)' },
          '60%':  { transform: 'scale(1.06)' },
          '100%': { transform: 'scale(1)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%':           { transform: 'scale(1)',   opacity: '1'   },
        },
      },
      animation: {
        'fade-up':    'fadeUp 0.4s cubic-bezier(0.34,1.56,0.64,1) both',
        'fade-in':    'fadeIn 0.3s ease both',
        'slide-right':'slideRight 0.35s cubic-bezier(0.34,1.56,0.64,1) both',
        'float':      'float 3s ease-in-out infinite',
        'float-slow': 'floatSlow 5s ease-in-out infinite',
        'float-delay':'floatSlow 4s ease-in-out 1s infinite',
        'wiggle':     'wiggle 0.4s ease-in-out',
        'pop':        'pop 0.3s cubic-bezier(0.34,1.56,0.64,1)',
        'shimmer':    'shimmer 1.4s linear infinite',
        'bounce-dot': 'bounceDot 1.2s ease-in-out infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
