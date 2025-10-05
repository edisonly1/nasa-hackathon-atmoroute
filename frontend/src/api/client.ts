// src/api/client.ts
import axios from "axios";

export const API_BASE = "";
export const api = axios.create({ baseURL: API_BASE, timeout: 30000 });

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.detail || err?.response?.data?.error?.message || err.message;
    return Promise.reject(new Error(msg));
  }
);
