/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './erickvale/templates/**/*.html',
    './htac/templates/**/*.html',
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
      },
      fontFamily: {
        sans: [
          '"DM Sans"',
          'ui-sans-serif',
          'system-ui',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
