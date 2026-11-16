import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Set to /<repo>/ when building for GitHub Pages.
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
});
