/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './erickvale/templates/**/*.html',
    './htac/templates/**/*.html',
    './projects/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        htac: {
          navy: '#003865',
          teal: '#008EAA',
          sky: '#7ecde0',
          mist: '#e8f4f8',
        },
        navy: {
          900: '#111d2e',
          800: '#1B2B44',
          700: '#2D4057',
          600: '#3D5470',
          500: '#4D6888',
        },
        teal: {
          700: '#0f5c4e',
          600: '#1A7F6E',
          500: '#1f9880',
          400: '#2db89e',
          100: '#e0f4f0',
          50: '#f0faf8',
        },
        amber: {
          700: '#8a5210',
          600: '#C4771A',
          500: '#d4882a',
          100: '#fdf0dc',
          50: '#fef8ee',
        },
        parchment: {
          100: '#F7F6F2',
          200: '#EEECEA',
          300: '#E2E0DA',
        },
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: [
          '"Source Sans 3"',
          'system-ui',
          'sans-serif',
        ],
        dm: [
          '"DM Sans"',
          'ui-sans-serif',
          'system-ui',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', 'Menlo', 'monospace'],
      },
      backgroundImage: {
        'topo-pattern': "url('../img/topo-pattern.svg')",
        'grid-subtle': "url('../img/grid-subtle.svg')",
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
