import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#09090b", // Zinc-950
        surface: {
          DEFAULT: "#18181b", // Zinc-900
          hover: "#27272a", // Zinc-800
        },
        border: {
          subtle: "#27272a", // 1px Zinc-800
        },
        accent: {
          DEFAULT: "#f59e0b", // Sharp Amber CTA
          hover: "#d97706",
          subtle: "rgba(245, 158, 11, 0.12)",
        },
        ink: {
          primary: "#f4f4f5", // Zinc-100
          secondary: "#a1a1aa", // Zinc-400
          muted: "#71717a", // Zinc-500
        },
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;

