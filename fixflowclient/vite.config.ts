import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // В режиме разработки запросы /api/... перенаправляются на Django.
    // Для браузера это один адрес — как и в проде, где Django раздаёт собранный фронтенд.
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
