/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // 2026 Modernist Color System
      colors: {
        // Soft Dark Foundation
        void: {
          DEFAULT: '#121212',
          50: '#1E1E1E',
          100: '#252525',
          200: '#2A2A2A',
          300: '#333333',
          400: '#404040',
          500: '#525252',
          600: '#6B6B6B',
          700: '#8A8A8A',
          800: '#A3A3A3',
          900: '#D4D4D4',
        },
        // Electric Neon Accents
        neon: {
          cyan: '#00F5FF',
          magenta: '#FF00E5',
          lime: '#ADFF00',
          orange: '#FF6B00',
          violet: '#8B5CF6',
        },
        // Semantic colors adapted for dark mode
        success: {
          DEFAULT: '#10B981',
          muted: 'rgba(16, 185, 129, 0.15)',
          glow: 'rgba(16, 185, 129, 0.4)',
        },
        warning: {
          DEFAULT: '#F59E0B',
          muted: 'rgba(245, 158, 11, 0.15)',
          glow: 'rgba(245, 158, 11, 0.4)',
        },
        danger: {
          DEFAULT: '#EF4444',
          muted: 'rgba(239, 68, 68, 0.15)',
          glow: 'rgba(239, 68, 68, 0.4)',
        },
        // Glass effects
        glass: {
          DEFAULT: 'rgba(30, 30, 30, 0.7)',
          light: 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.08)',
          hover: 'rgba(255, 255, 255, 0.1)',
        },
      },
      // Typography with Variable Font support
      fontFamily: {
        display: ['Outfit', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'display-lg': ['3.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '600' }],
        'display-md': ['2.5rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
        'display-sm': ['1.875rem', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
      },
      // Spatial Shadow System (hierarchical)
      boxShadow: {
        // Base layer shadows
        'spatial-sm': '0 1px 2px rgba(0, 0, 0, 0.5), 0 1px 3px rgba(0, 0, 0, 0.3)',
        'spatial-md': '0 4px 6px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)',
        'spatial-lg': '0 10px 15px rgba(0, 0, 0, 0.3), 0 4px 6px rgba(0, 0, 0, 0.2)',
        'spatial-xl': '0 20px 25px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.2)',
        'spatial-2xl': '0 25px 50px rgba(0, 0, 0, 0.35), 0 12px 24px rgba(0, 0, 0, 0.25)',
        // Neon glow shadows
        'neon-cyan': '0 0 20px rgba(0, 245, 255, 0.3), 0 0 40px rgba(0, 245, 255, 0.1)',
        'neon-magenta': '0 0 20px rgba(255, 0, 229, 0.3), 0 0 40px rgba(255, 0, 229, 0.1)',
        'neon-lime': '0 0 20px rgba(173, 255, 0, 0.3), 0 0 40px rgba(173, 255, 0, 0.1)',
        'neon-orange': '0 0 20px rgba(255, 107, 0, 0.3), 0 0 40px rgba(255, 107, 0, 0.1)',
        // Inner shadows for depth
        'inner-soft': 'inset 0 2px 4px rgba(0, 0, 0, 0.3)',
        'inner-deep': 'inset 0 4px 8px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(0, 0, 0, 0.3)',
        // Card glass effect
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'glass-hover': '0 12px 40px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
      },
      // Gradient backgrounds
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, transparent 50%, rgba(0, 245, 255, 0.1) 100%)',
        'gradient-glow': 'radial-gradient(ellipse at center, rgba(139, 92, 246, 0.15) 0%, transparent 70%)',
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E\")",
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg stroke='%23ffffff' stroke-opacity='0.03'%3E%3Cpath d='M0 0h60v60H0z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
      },
      // Spring physics animations
      animation: {
        'spring-bounce': 'springBounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'spring-scale': 'springScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'fade-in': 'fadeIn 0.4s ease-out',
        'fade-up': 'fadeUp 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'kinetic-weight': 'kineticWeight 0.3s ease-out forwards',
      },
      keyframes: {
        springBounce: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '50%': { transform: 'scale(1.02)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        springScale: {
          '0%': { transform: 'scale(0.9)' },
          '50%': { transform: 'scale(1.05)' },
          '100%': { transform: 'scale(1)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 245, 255, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 245, 255, 0.5)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        kineticWeight: {
          '0%': { fontWeight: '400', letterSpacing: '0' },
          '100%': { fontWeight: '700', letterSpacing: '0.02em' },
        },
      },
      // Timing functions for spring physics
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.25, 0.1, 0.25, 1)',
        'bounce-out': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      // Backdrop blur levels
      backdropBlur: {
        xs: '2px',
        '2xl': '40px',
        '3xl': '64px',
      },
      // Border radius for squishy feel
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      // Z-index for spatial layering
      zIndex: {
        'base': '0',
        'elevated': '10',
        'floating': '20',
        'overlay': '30',
        'modal': '40',
        'toast': '50',
        'tooltip': '60',
      },
    },
  },
  plugins: [],
}
