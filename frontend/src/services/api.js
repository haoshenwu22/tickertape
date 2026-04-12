import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("/auth/refresh/") &&
      !originalRequest.url.includes("/auth/login/") &&
      !originalRequest.url.includes("/auth/register/")
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");

      if (refreshToken) {
        try {
          const { data } = await axios.post("/api/auth/refresh/", {
            refresh: refreshToken,
          });
          localStorage.setItem("access_token", data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          // refresh failed
        }
      }

      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

export const login = (username, password) =>
  api.post("/auth/login/", { username, password }).then((r) => r.data);

export const register = (username, email, password) =>
  api.post("/auth/register/", { username, email, password }).then((r) => r.data);

export const getMe = () => api.get("/auth/me/").then((r) => r.data);

export const getSubscriptions = () =>
  api.get("/subscriptions/").then((r) => r.data.results || r.data);

export const createSubscription = (ticker, email) =>
  api.post("/subscriptions/", { ticker, email }).then((r) => r.data);

export const deleteSubscription = (id) =>
  api.delete(`/subscriptions/${id}/`).then((r) => r.data);

export const sendNow = (id) =>
  api.post(`/subscriptions/${id}/send-now/`).then((r) => r.data);

export const getStockPrices = (tickers) =>
  api.get("/stocks/prices/", { params: { tickers: tickers.join(",") } }).then((r) => r.data);

export const getStockHistory = (ticker, period) =>
  api.get("/stocks/history/", { params: { ticker, period } }).then((r) => r.data);

export const validateTicker = (ticker) =>
  api.get("/stocks/validate/", { params: { ticker } }).then((r) => r.data);

export const getAlerts = () => api.get("/alerts/").then((r) => r.data.results || r.data);

export const createAlert = (ticker, target_price, condition) =>
  api.post("/alerts/", { ticker, target_price, condition }).then((r) => r.data);

export const deleteAlert = (id) =>
  api.delete(`/alerts/${id}/`).then((r) => r.data);

export default api;
