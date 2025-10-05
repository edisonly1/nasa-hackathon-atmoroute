import { defineConfig, loadEnv } from "vite";
import dyadComponentTagger from "@dyad-sh/react-vite-component-tagger";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), ""); // loads .env, .env.local, etc.
  const API = env.VITE_BACKEND_PROXY;

  if (!API) {
    console.warn("⚠️  VITE_BACKEND_PROXY is not set. /api requests will NOT be proxied.");
  }

  return {
    server: {
      // Bind to all interfaces so Codespaces can expose it
      host: "0.0.0.0",
      port: 8080,
      proxy: API
        ? {
            // Anything starting with /api will be forwarded to your backend
            "/api": {
              target: API,
              changeOrigin: true,
              secure: false, // Codespaces uses a cert the dev proxy terminates; this is fine for dev
              // Optional: rewrite if your backend isn't rooted at /
              // rewrite: (p) => p,
            },
          }
        : undefined,
      // Optional (helps HMR behind https tunnels)
      hmr: { clientPort: 443 },
    },
    plugins: [dyadComponentTagger(), react()],
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
  };
});
