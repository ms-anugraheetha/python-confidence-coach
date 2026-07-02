/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],

  theme: {
    extend: {
      fontFamily: {
        sans: ["'Inter'", "'Space Grotesk'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "monospace"],
      },

      colors: {
        surface: {
          DEFAULT: "#FAFAFA",   // page background
          raised:  "#FFFFFF",   // cards
          overlay: "#F4F4F4",   // hover states
          input:   "#FFFFFF",   // form inputs
        },
        border: {
          DEFAULT: "#EAEAEA",
          strong:  "#D4D4D4",
        },
        text: {
          primary:     "#111111",
          secondary:   "#666666",
          muted:       "#999999",
          placeholder: "#BBBBBB",
        },
      },

      keyframes: {
        "slide-up": {
          "0%":   { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.35" },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        "slide-up":   "slide-up 0.18s ease-out",
        "pulse-soft": "pulse-soft 1.6s ease-in-out infinite",
        "fade-in":    "fade-in 0.24s ease-out",
      },

      width: {
        "nav":     "220px",
        "sidebar": "288px",
      },

      boxShadow: {
        "card":    "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "card-md": "0 4px 16px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.04)",
        "input":   "0 0 0 3px rgba(0,0,0,0.06)",
      },

      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
    },
  },

  plugins: [],
};
