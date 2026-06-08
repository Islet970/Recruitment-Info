import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = "http://localhost:8000/api";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    if (error.response?.status !== 401) throw error;
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) { clearAuth(); throw error; }
    try {
      const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken });
      const { access_token, refresh_token } = res.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      return api.request(error.config!);
    } catch {
      clearAuth();
      window.location.href = "/";
      throw error;
    }
  }
);

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("auth_user");
}

export function storeAuth(token: string, refresh: string, user: any) {
  localStorage.setItem("access_token", token);
  localStorage.setItem("refresh_token", refresh);
  localStorage.setItem("auth_user", JSON.stringify(user));
}

export function getStoredUser() {
  if (typeof window === "undefined") return null;
  try { return JSON.parse(localStorage.getItem("auth_user") || "null"); }
  catch { return null; }
}

export default api;
