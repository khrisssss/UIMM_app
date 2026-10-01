import { translateErrorDetail } from "../utils/french";
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  });
  //this is for the local and above is for deployment online
  //baseURL: "http://127.0.0.1:8000",
//});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error?.response?.status;
    const detail = error?.response?.data?.detail;

    const isAuthError =
      statusCode === 401 ||
      detail === "Invalid or expired token" ||
      detail === "Not authenticated";

    if (isAuthError) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      window.dispatchEvent(
        new CustomEvent("auth-expired", {
          detail: {
            message: "Votre session a expiré. Veuillez vous reconnecter.",
          },
        })
      );
    }

    if (error?.response?.data?.detail !== undefined) {
      error.response.data.detail = translateErrorDetail(detail);
    }

    return Promise.reject(error);
  }
);

export default api;