/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef8ff',
          100: '#d9efff',
          500: '#1682d4',
          600: '#0d68ad',
          700: '#0b548d',
          900: '#0b3558',
        },
      },
    },
  },
  plugins: [],
}
