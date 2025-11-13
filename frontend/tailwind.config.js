/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        huawei: {
          red: '#E60012',
          darkred: '#C50010',
        }
      }
    },
  },
  plugins: [],
}