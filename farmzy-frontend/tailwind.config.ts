import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./providers/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        farm: {
          bg: "#0A0F0D",
          surface: "#0F1A14",
          primary: "#16A34A",
          accent: "#4ADE80",
          warning: "#F59E0B",
          danger: "#EF4444",
          muted: "#6B7280",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(74, 222, 128, 0.2), 0 8px 24px rgba(22, 163, 74, 0.15)",
      },
    },
  },
  plugins: [],
};

export default config;
