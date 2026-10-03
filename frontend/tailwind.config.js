/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        industrial: {
          950: '#06090e',
          900: '#0b111c',
          850: '#101827',
          800: '#162235',
          700: '#23354f',
          600: '#354c6d',
          accent: '#f59e0b',
          danger: '#ef4444',
          warning: '#f97316',
          success: '#10b981',
          cyan: '#06b6d4',
          purple: '#8b5cf6',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'hazard': '0 0 15px -3px rgba(245, 158, 11, 0.25)',
        'danger-glow': '0 0 18px -2px rgba(239, 68, 68, 0.35)',
        'success-glow': '0 0 15px -3px rgba(16, 185, 129, 0.25)',
        'panel': '0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
}
