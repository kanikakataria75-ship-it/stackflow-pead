import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// /api/* is proxied to the FastAPI scanner (uvicorn, default :8765; override with DRIFT_API).
const API = process.env.DRIFT_API ?? "http://127.0.0.1:8765";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: API, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") } },
  },
  preview: {
    port: 4173,
    proxy: { "/api": { target: API, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") } },
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: { output: { manualChunks: (id) => (id.includes("three") || id.includes("@react-three") ? "three" : undefined) } },
  },
});
