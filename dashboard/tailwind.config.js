/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        disney: {
          blue: '#006EBA',
          'blue-dark': '#00459B',
          gold: '#C8A951',
          'gold-light': '#F0D080',
          navy: '#0D1B2A',
          'navy-light': '#162032',
          slate: '#1E2D3D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
