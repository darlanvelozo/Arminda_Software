import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * Instância única do axios para chamar a API do Arminda.
 * Em dev, o Vite faz proxy de /api para localhost:8000.
 */
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  // 30s — endpoints de cálculo de folha podem demorar
  timeout: 30_000,
});

// Placeholder para interceptor de auth (Bloco 1)
api.interceptors.request.use((config) => {
  // const token = localStorage.getItem("arminda_token");
  // if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
