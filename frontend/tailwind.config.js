/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        shield: {
          950: '#0a0e1a',
          900: '#0f1629',
          800: '#1a2236',
          700: '#243049',
          600: '#3b82f6',
          500: '#60a5fa',
          400: '#93c5fd',
          accent: '#6366f1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
