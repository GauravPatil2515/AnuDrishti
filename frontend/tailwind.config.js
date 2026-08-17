/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
       colors: {
         canvas: {
           DEFAULT: 'var(--color-canvas)',
           elevated: 'var(--color-canvas-elevated)',
           overlay: 'var(--color-canvas-overlay)',
         },
         surface: {
           DEFAULT: 'var(--color-surface)',
           elevated: 'var(--color-surface-elevated)',
           hover: 'var(--color-surface-hover)',
         },
         border: {
           DEFAULT: 'var(--color-border)',
           hover: 'var(--color-border-hover)',
           strong: 'var(--color-border-strong)',
         },
         text: {
           primary: 'var(--color-text-primary)',
           secondary: 'var(--color-text-secondary)',
           muted: 'var(--color-text-muted)',
           inverse: 'var(--color-text-inverse)',
         },
         'accent-emerald': 'var(--color-accent-emerald)',
         'accent-amber':   'var(--color-accent-amber)',
         'accent-red':     'var(--color-accent-red)',
         'accent-green':   'var(--color-accent-green)',
       },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'micro': '0 0 0 1px var(--color-border)',
        'micro-hover': '0 0 0 1px var(--color-border-hover)',
        'card': '0 2px 8px var(--shadow-color-1), 0 0 0 1px var(--color-border)',
        'card-hover': '0 4px 16px var(--shadow-color-2), 0 0 0 1px var(--color-border-hover)',
        'dropdown': '0 8px 32px var(--shadow-color-3), 0 0 0 1px var(--color-border)',
        'glow-green': '0 0 0 1px var(--color-accent-green-glow), 0 0 16px var(--color-accent-green-glow)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(-8px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.98)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out forwards',
        'slide-in': 'slide-in 150ms ease-out forwards',
        'scale-in': 'scale-in 100ms ease-out forwards',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
  }