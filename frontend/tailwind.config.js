/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1DB954",
        background: "#0D0D0D",
        surface: "#1A1A1A",
        border: "#2A2A2A",
      },
    },
  },
  plugins: [],
}