/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        status: {
          empty: '#9CA3AF',
          low: '#22C55E',
          medium: '#EAB308',
          high: '#F97316',
          full: '#EF4444',
        },
      },
    },
  },
  plugins: [],
}
