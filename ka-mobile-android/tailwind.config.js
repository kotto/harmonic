/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soul: {
          DEFAULT: '#2dd4bf',
          light: '#5eead4',
          dark: 'rgba(45,212,191,0.20)',
          glow: 'rgba(45,212,191,0.40)',
        },
        teal: {
          DEFAULT: '#2dd4bf',
          light: '#5eead4',
          dark: 'rgba(45,212,191,0.20)',
          glow: 'rgba(45,212,191,0.40)',
        },
        life: {
          DEFAULT: '#4de8ae',
          dark: 'rgba(77,232,174,0.18)',
          glow: 'rgba(77,232,174,0.35)',
        },
        wisdom: {
          DEFAULT: '#f5cc6a',
          dark: 'rgba(245,204,106,0.18)',
          glow: 'rgba(245,204,106,0.35)',
        },
        rose: {
          DEFAULT: '#f2a8c4',
          dark: 'rgba(242,168,196,0.18)',
          glow: 'rgba(242,168,196,0.35)',
        },
        sky: {
          DEFAULT: '#67e8f9',
          dark: 'rgba(103,232,249,0.18)',
          glow: 'rgba(103,232,249,0.35)',
        },
        coral: {
          DEFAULT: '#f07040',
        },
        void: {
          DEFAULT: '#000508',
          light: '#001923',
        },
        abyss: {
          DEFAULT: '#001f2a',
        },
        deep: {
          DEFAULT: '#01202c',
        },
        glass: {
          1: 'rgba(45,212,191,0.05)',
          2: 'rgba(45,212,191,0.09)',
          3: 'rgba(45,212,191,0.14)',
        },
        border: {
          1: 'rgba(45,212,191,0.08)',
          2: 'rgba(45,212,191,0.14)',
          3: 'rgba(45,212,191,0.22)',
        },
        text: {
          1: 'rgba(230,255,250,0.97)',
          2: 'rgba(230,255,250,0.78)',
          3: 'rgba(230,255,250,0.52)',
          4: 'rgba(230,255,250,0.30)',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          '"SF Pro Display"',
          '"Inter"',
          'system-ui',
          'sans-serif',
        ],
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '26px',
        '4xl': '48px',
      },
      width: {
        'device': '375px',
      },
      height: {
        'device': '812px',
      },
      animation: {
        'breathe': 'breathe 4s ease-in-out infinite',
        'drift': 'drift 11s ease-in-out infinite',
        'drift-reverse': 'drift 14s ease-in-out infinite reverse',
        'drift-slow': 'drift 18s ease-in-out infinite',
        'pulse': 'pulse 1.2s ease-in-out infinite',
        'blink': 'blink 1.1s ease-in-out infinite',
        'fu': 'fu 0.25s ease-out',
        'pring': 'pring 2.6s ease-out infinite',
        'wave': 'wave 0.4s ease-in-out infinite alternate',
        'sc-in': 'scIn 0.32s cubic-bezier(0,0,0.2,1) forwards',
        'bar-grow': 'barGrow 0.8s ease-out 0.4s backwards',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.09)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        drift: {
          '0%, 100%': { transform: 'translate(0,0) scale(1)' },
          '33%': { transform: 'translate(7px,-10px) scale(1.04)' },
          '66%': { transform: 'translate(-5px,7px) scale(0.97)' },
        },
        fu: {
          'from': { opacity: '0', transform: 'translateY(7px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        pring: {
          '0%': { transform: 'scale(1)', opacity: '0.5' },
          '100%': { transform: 'scale(2.4)', opacity: '0' },
        },
        wave: {
          '0%, 100%': { height: '3px' },
          '50%': { height: 'var(--wh, 18px)' },
        },
        scIn: {
          'from': { opacity: '0', transform: 'translateY(12px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        barGrow: {
          'from': { width: '0' },
        },
      },
    },
  },
  plugins: [],
}
