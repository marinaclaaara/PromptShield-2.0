import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// A URL da API vem de VITE_API_URL (padrão http://localhost:8000). Nada é embutido no código.
export default defineConfig({ plugins: [react()], server: { port: 5173 } });
