import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0B1220",
          soft: "#141D2E",
          line: "#233047",
        },
        paper: {
          DEFAULT: "#F7F5F0",
          soft: "#EFEBE2",
          line: "#DDD6C7",
        },
        accent: {
          DEFAULT: "#2F6FEB",
          soft: "#5B8CF0",
        },
        gain: "#17A673",
        loss: "#E5484D",
        caution: "#E8A33D",
      },
      fontFamily: {
        sans: ["var(--font-plex-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
