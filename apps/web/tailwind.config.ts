import type { Config } from "tailwindcss";

/**
 * Tailwind CSS v4
 * - 主题变量与 design tokens：见 app/globals.css（@theme inline）
 * - PostCSS 插件：postcss.config.mjs（@tailwindcss/postcss）
 */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
};

export default config;
