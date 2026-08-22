import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        term: {
          bg: '#000000',
          panel: '#0A0A0A',
          amber: '#FFB000',
          green: '#00FF00',
          red: '#FF3333',
          border: '#333333'
        }
      }
    },
  },
  plugins: [],
}
export default config