import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Proxy API calls to the FastAPI backend during development.
  // The React dev server runs on :5173, FastAPI runs on :8000.
  // Without this proxy, the browser would get CORS errors on every API call.
  // With it, /api/... requests are transparently forwarded — no CORS issues in dev.
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:9000",
        changeOrigin: true,
      },
    },
  },

  // Path alias so imports read `@/components/...` not `../../components/...`
  resolve: {
    alias: {
      "@": "/src",
    },
  },
});
