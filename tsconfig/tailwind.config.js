/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#fcfcfb',
        plane: '#f9f9f7',
        ink: {
          primary: '#0b0b0b',
          secondary: '#52514e',
          muted: '#898781',
        },
        line: {
          grid: '#e1e0d9',
          axis: '#c3c2b7',
          border: 'rgba(11,11,11,0.10)',
        },
        series: {
          1: '#2a78d6',
          2: '#008300',
          3: '#e87ba4',
          4: '#eda100',
          5: '#1baf7a',
          6: '#eb6834',
          7: '#4a3aa7',
          8: '#e34948',
        },
        status: {
          good: '#0ca30c',
          warning: '#fab219',
          serious: '#ec835a',
          critical: '#d03b3b',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', '"Segoe UI"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
