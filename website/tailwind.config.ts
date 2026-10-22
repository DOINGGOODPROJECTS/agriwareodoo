import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f1f7ed",
          100: "#dfedd4",
          200: "#c0dcac",
          300: "#98c67b",
          400: "#73ae55",
          500: "#4f8f36",
          600: "#3b7128",
          700: "#2f5a22",
          800: "#27481f",
          900: "#213d1c",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
