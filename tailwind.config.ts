import type {Config} from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Noto Sans HK"', 'sans-serif'],
        body: ['"Noto Sans HK"', 'sans-serif'],
        headline: ['"Noto Sans HK"', 'sans-serif'],
        code: ['monospace'],
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          hover: '#FF8A00',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        dark: '#0F172A',
        slate: {
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'flow-line': {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        'video-slide-in': {
          '0%': { transform: 'translateX(-200%)', opacity: '0' },
          '15%': { transform: 'translateX(-200%)', opacity: '1' },
          '40%': { transform: 'translateX(0%) scale(0.5)', opacity: '0' },
          '100%': { transform: 'translateX(0%) scale(0.5)', opacity: '0' },
        },
        'srt-slide-out': {
          '0%, 60%': { transform: 'translateX(0%) scale(0.5)', opacity: '0' },
          '65%': { transform: 'translateX(0%) scale(1)', opacity: '1' },
          '90%': { transform: 'translateX(200%)', opacity: '1' },
          '100%': { transform: 'translateX(220%)', opacity: '0' },
        },
        'chip-pulse': {
          '0%, 35%': { transform: 'scale(1)', boxShadow: '0 0 0 rgba(255,84,0,0)', borderColor: '#475569' },
          '40%, 60%': { transform: 'scale(1.05)', boxShadow: '0 0 40px rgba(255,84,0,0.3)', borderColor: '#FF5400' },
          '65%, 100%': { transform: 'scale(1)', boxShadow: '0 0 0 rgba(255,84,0,0)', borderColor: '#475569' },
        },
        'wave': {
          '0%': { height: '20%' },
          '100%': { height: '100%' },
        },
        'typing': {
          '0%': { width: '0%' },
          '100%': { width: '80%' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'idle-state': {
          '0%, 35%': { opacity: '0.4' },
          '40%, 60%': { opacity: '0' },
          '65%, 100%': { opacity: '0.4' },
        },
        'processing-state': {
          '0%, 35%': { opacity: '0', transform: 'scale(0.9)' },
          '40%, 60%': { opacity: '1', transform: 'scale(1)' },
          '65%, 100%': { opacity: '0', transform: 'scale(0.9)' },
        },
        'cycle-text': {
          '0%, 35%': { content: '"1. 拖入影片檔案..."', color: '#94a3b8' },
          '40%, 60%': { content: '"2. 生成器 AI 運算中..."', color: '#FF5400' },
          '65%, 100%': { content: '"3. 成功匯出 SRT 字幕！"', color: '#4ade80' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'flow-line': 'flow-line 2s linear infinite',
        'video-slide-in': 'video-slide-in 4s ease-in-out infinite',
        'srt-slide-out': 'srt-slide-out 4s ease-in-out infinite',
        'chip-pulse': 'chip-pulse 4s ease-in-out infinite',
        'wave': 'wave 0.5s ease-in-out infinite alternate',
        'typing': 'typing 1s steps(3, end) infinite alternate',
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
        'float': 'float 3s ease-in-out infinite',
        'float-delayed': 'float 3s ease-in-out 1.5s infinite',
        'idle-state': 'idle-state 4s step-end infinite',
        'processing-state': 'processing-state 4s step-end infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config;
