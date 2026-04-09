import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  globalCss: {
    body: {
      bg: "gray.50",
      color: "gray.800",
    },
  },
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#f0f0f8" },
          100: { value: "#d1d1e6" },
          200: { value: "#b2b2d4" },
          300: { value: "#8585b8" },
          400: { value: "#5a5a9e" },
          500: { value: "#1a1a2e" },
          600: { value: "#161628" },
          700: { value: "#121222" },
          800: { value: "#0e0e1c" },
          900: { value: "#0a0a16" },
        },
        accent: {
          50: { value: "#fef0f3" },
          100: { value: "#fcd1da" },
          200: { value: "#f9a3b5" },
          300: { value: "#f57590" },
          400: { value: "#e94560" },
          500: { value: "#d63251" },
          600: { value: "#b82844" },
          700: { value: "#991e37" },
          800: { value: "#7a142a" },
          900: { value: "#5c0a1d" },
        },
      },
      fonts: {
        heading: { value: "Inter, system-ui, sans-serif" },
        body: { value: "Inter, system-ui, sans-serif" },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
