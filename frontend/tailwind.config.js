/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular'],
      },
      colors: {
        premium: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        accent: {
          50: '#f5f3ff',
          100: '#ede9fe',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          900: '#4c1d95',
        }
      },
      boxShadow: {
        card: '0 4px 24px -6px rgba(15, 23, 42, 0.08)',
        elevated: '0 12px 32px -8px rgba(15, 23, 42, 0.12)',
      },
      backgroundImage: {
        'hero-grid': 'radial-gradient(circle at 1px 1px, rgba(15, 23, 42, 0.05) 1px, transparent 0)',
        'premium-gradient': 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      },
    },
  },
  plugins: [],
}
