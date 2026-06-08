/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(34,211,238,0.18), 0 18px 60px rgba(2,8,23,0.55)",
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.10) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

