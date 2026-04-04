/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg': '#0f172a',
        'bg-secondary': '#1a2744',
        'surface': '#1e293b',
        'surface-2': '#334155',
        'surface-3': '#475569',
        'primary': '#3b82f6',
        'primary-hover': '#2563eb',
        'primary-light': 'rgba(59, 130, 246, 0.08)',
        'accent': '#06b6d4',
        'success': '#10b981',
        'warning': '#f59e0b',
        'critical': '#ef4444',
        'danger': '#ef4444',
        'text': '#f1f5f9',
        'text-secondary': '#cbd5e1',
        'muted': '#94a3b8',
        'border': 'rgba(148, 163, 184, 0.12)',
        'card-shadow': 'rgba(0, 0, 0, 0.3)',
      },
      fontFamily: {
        sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['Geist Mono', 'SF Mono', 'Cascadia Code', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '16px',
        btn: '12px',
        badge: '8px',
      },
    },
  },
  plugins: [],
}
