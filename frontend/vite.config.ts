import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    root: __dirname, // Explicitly set root to handle WSL paths
    publicDir: "public",
    plugins: [react()],
    resolve: {
        alias: {
            "~": path.resolve(__dirname, "./app"),
        },
    },
    server: {
        host: "0.0.0.0",
        port: 5173,
        strictPort: false,
        proxy: {
            "/api": {
                target: process.env.VITE_API_URL || "http://localhost:8000",
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ""),
            },
        },
    },
    build: {
        outDir: "dist",
        emptyOutDir: true,
        rollupOptions: {
            input: path.resolve(__dirname, "index.html"),
        },
    },
    // Expose env variables to the client
    envPrefix: "VITE_",
});
