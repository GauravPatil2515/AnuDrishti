/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Linear-inspired dark palette
        canvas: {
          DEFAULT: '#08090a',
          elevated: '#0d0e11',
          overlay: 'rgba(8, 9, 10, 0.8)',
        },
        surface: {
          DEFAULT: 'rgba(255, 255, 255, 0.03)',
          elevated: 'rgba(255, 255, 255, 0.05)',
          hover: 'rgba(255, 255, 255, 0.08)',
        },
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.08)',
          hover: 'rgba(255, 255, 255, 0.15)',
          strong: 'rgba(255, 255, 255, 0.2)',
        },
        text: {
          primary: '#ffffff',
          secondary: 'rgba(255, 255, 255, 0.7)',
          muted: 'rgba(255, 255, 255, 0.45)',
          inverse: '#08090a',
        },
        accent: {
          indigo: '#6366f1',
          indigoHover: '#4f46e5',
          indigoGlow: 'rgba(99, 102, 241, 0.5)',
          emerald: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
          rose: '#f43f5e',
          violet: '#818cf8',
        },
        // Semantic colors for toxicity
        toxicity: {
          safe: '#10b981',
          low: '#84cc16',
          moderate: '#f59e0b',
          high: '#ef4444',
          critical: '#dc2626',
        },
        triage: {
          green: '#10b981',
          yellow: '#f59e0b',
          red: '#ef4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'xs': ['0.7rem', { lineHeight: '1.4', letterSpacing: '0.02em' }],
        'sm': ['0.75rem', { lineHeight: '1.5', letterSpacing: '0.01em' }],
        'base': ['0.8125rem', { lineHeight: '1.6', letterSpacing: '0' }],
        'lg': ['0.875rem', { lineHeight: '1.5', letterSpacing: '0' }],
        'xl': ['1rem', { lineHeight: '1.4', letterSpacing: '-0.01em' }],
        '2xl': ['1.125rem', { lineHeight: '1.3', letterSpacing: '-0.02em' }],
        '3xl': ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.03em' }],
      },
      spacing: {
        '0.5': '0.125rem',
        '1': '0.25rem',
        '1.5': '0.375rem',
        '2': '0.5rem',
        '2.5': '0.625rem',
        '3': '0.75rem',
        '3.5': '0.875rem',
        '4': '1rem',
        '5': '1.25rem',
        '6': '1.5rem',
        '7': '1.75rem',
        '8': '2rem',
        '9': '2.25rem',
        '10': '2.5rem',
      },
      borderRadius: {
        'none': '0',
        'xs': '0.125rem',
        'sm': '0.25rem',
        'DEFAULT': '0.375rem',
        'md': '0.5rem',
        'lg': '0.625rem',
        'xl': '0.75rem',
        '2xl': '1rem',
        'full': '9999px',
      },
      boxShadow: {
        'micro': '0 0 0 1px rgba(255, 255, 255, 0.08)',
        'micro-hover': '0 0 0 1px rgba(255, 255, 255, 0.15)',
        'card': '0 2px 8px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.08)',
        'card-hover': '0 4px 16px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.15)',
        'dropdown': '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.08)',
        'glow-indigo': '0 0 0 1px rgba(94, 106, 210, 0.5), 0 0 16px rgba(94, 106, 210, 0.15)',
        'glow-emerald': '0 0 0 1px rgba(16, 185, 129, 0.5), 0 0 16px rgba(16, 185, 129, 0.15)',
        'glow-amber': '0 0 0 1px rgba(245, 158, 11, 0.5), 0 0 16px rgba(245, 158, 11, 0.15)',
        'glow-red': '0 0 0 1px rgba(239, 68, 68, 0.5), 0 0 16px rgba(239, 68, 68, 0.15)',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'DEFAULT': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
        '2xl': '40px',
      },
      transitionDuration: {
        '50': '50ms',
        '100': '100ms',
        '150': '150ms',
        '200': '200ms',
        '250': '250ms',
        '300': '300ms',
      },
      transitionTimingFunction: {
        'ease-out-cubic': 'cubic-bezier(0.22, 1, 0.36, 1)',
        'ease-in-out-cubic': 'cubic-bezier(0.65, 0, 0.35, 1)',
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
        'pulse-border': {
          '0%, 100%': { borderColor: 'rgba(255, 255, 255, 0.08)' },
          '50%': { borderColor: 'rgba(255, 255, 255, 0.15)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out-cubic',
        'slide-in': 'slide-in 150ms ease-out-cubic',
        'scale-in': 'scale-in 100ms ease-out-cubic',
        'pulse-border': 'pulse-border 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, transparent 50%)',
        'shimmer': 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent)',
      },
      backgroundSize: {
        'shimmer': '200% 100%',
      },
    },
  },
  plugins: [],
}