/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'felt-green': '#1a472a',
        'felt-green-light': '#2d5a3d',
        'card-red': '#dc2626',
        'card-black': '#1f2937',
      },
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
      },
      animation: {
        'deal': 'deal 0.3s ease-out',
        'flip': 'flip 0.6s ease-in-out',
        'highlight': 'highlight 1s ease-in-out infinite',
      },
      keyframes: {
        deal: {
          '0%': { transform: 'translateY(-100px) scale(0.5)', opacity: '0' },
          '100%': { transform: 'translateY(0) scale(1)', opacity: '1' },
        },
        flip: {
          '0%': { transform: 'rotateY(0deg)' },
          '50%': { transform: 'rotateY(90deg)' },
          '100%': { transform: 'rotateY(0deg)' },
        },
        highlight: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 215, 0, 0)' },
          '50%': { boxShadow: '0 0 20px 5px rgba(255, 215, 0, 0.5)' },
        },
      },
    },
  },
  plugins: [],
};