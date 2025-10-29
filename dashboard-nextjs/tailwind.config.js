/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // INSTITUTIONAL BLOOMBERG TERMINAL AESTHETIC
        background: {
          primary: '#0a0e17',      // Very dark navy background
          secondary: '#161b27',    // Dark navy card backgrounds
          tertiary: '#1f2937',     // Slightly lighter for depth
        },
        text: {
          primary: '#E0E0E3',      // Bright primary text
          secondary: '#9099a6',    // Muted secondary text  
          tertiary: '#6b7280',     // Subtle tertiary text
        },
        border: {
          primary: 'rgba(255, 255, 255, 0.1)',    // Thin subtle borders
          secondary: 'rgba(255, 255, 255, 0.05)', // Ultra-subtle dividers
        },
        // ELECTRIFIED BUY SPECTRUM (Blues)
        buy: {
          primary: '#0055FF',      // Electric cobalt
          secondary: '#00A1FF',    // Vibrant cerulean  
          accent: '#00C8FF',       // Electric azure
          subtle: '#002966',       // Deep navy differentiation
        },
        // ELECTRIFIED SELL SPECTRUM (Reds)
        sell: {
          critical: '#BF0000',     // Deep blood red
          primary: '#E50000',      // Intense scarlet
          urgent: '#FF2500',       // Burning red
          caution: '#FF5D00',      // Fiery orange
        },
        // ACCENT POPS
        accent: {
          purple: '#9000FF',       // Electric purple
          green: '#00FF66',        // Neon green
          glow: 'rgba(0, 85, 255, 0.3)',  // Blue glow
        },
        // LEGACY COMPATIBILITY (Updated with new palette)
        bull: {
          400: '#00C8FF',          // Electric azure
          500: '#00A1FF',          // Vibrant cerulean
          600: '#0055FF',          // Electric cobalt
        },
        bear: {
          400: '#FF5D00',          // Fiery orange
          500: '#E50000',          // Intense scarlet
          600: '#BF0000',          // Deep blood red
        },
        neutral: {
          500: '#9099a6',          // Muted secondary
          600: '#6b7280',          // Subtle tertiary
        },
        // SOPHISTICATED CHART COLORS
        chart: {
          grid: 'rgba(255, 255, 255, 0.05)',
          candleUp: '#00C8FF',     // Electric azure for up candles
          candleDown: '#E50000',   // Intense scarlet for down candles
          volume: 'rgba(255, 255, 255, 0.1)',
          ma20: '#0055FF',         // Electric cobalt
          ma50: '#9000FF',         // Electric purple
          ma200: '#FF5D00',        // Fiery orange
        }
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-green': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        // LUMINOUS ANIMATIONS
        'electric-pulse': 'electric-pulse 3s ease-in-out infinite',
        'neon-flicker': 'neon-flicker 0.15s ease-in-out infinite alternate',
        'luminous-glow': 'luminous-glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        // LUMINOUS KEYFRAMES
        'electric-pulse': {
          '0%, 100%': { 
            boxShadow: '0 0 8px currentColor, 0 0 16px currentColor',
            opacity: '1' 
          },
          '50%': { 
            boxShadow: '0 0 16px currentColor, 0 0 32px currentColor, 0 0 48px currentColor',
            opacity: '0.8' 
          },
        },
        'neon-flicker': {
          '0%': { opacity: '1' },
          '100%': { opacity: '0.95' },
        },
        'luminous-glow': {
          '0%': { 
            textShadow: '0 0 10px currentColor',
            filter: 'brightness(1)' 
          },
          '100%': { 
            textShadow: '0 0 20px currentColor, 0 0 30px currentColor',
            filter: 'brightness(1.1)' 
          },
        },
      },
      boxShadow: {
        'institutional': '0 8px 25px -5px rgba(0, 0, 0, 0.4)',
        'glow-blue': '0 0 20px rgba(0, 85, 255, 0.3)',
        'glow-red': '0 0 20px rgba(229, 0, 0, 0.3)',
        'glow-purple': '0 0 20px rgba(144, 0, 255, 0.3)',
        'glow-green': '0 0 20px rgba(0, 255, 102, 0.4)',
        'subtle': '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
        'depth': '0 8px 25px -5px rgba(0, 0, 0, 0.4)',
        // LUMINOUS EFFECTS
        'luminous-card': '0 0 32px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        'electric-glow': '0 0 16px rgba(0, 85, 255, 0.3), 0 0 32px rgba(0, 85, 255, 0.1)',
        'neon-pulse': '0 0 8px currentColor, 0 0 16px currentColor',
        'hairline-glow': '0 0 4px currentColor, inset 0 0 2px currentColor',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
