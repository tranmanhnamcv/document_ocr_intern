import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL;

export const TOKEN_KEY = "ocr_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Auto-redirect to /login whenever an authenticated request comes back 401
// (expired or blacklisted token). Only fires for requests that actually
// carried an Authorization header, so a bad-password 401 on the login form
// itself is left alone.
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined" && error.response?.status === 401) {
      const hadAuthHeader = Boolean(error.config?.headers?.Authorization);
      const onAuthPage =
        window.location.pathname === "/login" ||
        window.location.pathname === "/register";

      if (hadAuthHeader && !onAuthPage) {
        removeToken();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function register(email: string, password: string, fullName: string) {
  const { data } = await axios.post(`${API}/api/v1/auth/register`, {
    email,
    password,
    full_name: fullName,
  });
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await axios.post(`${API}/api/v1/auth/login`, {
    email,
    password,
  });
  return data;
}

export async function logout() {
  const token = getToken();
  if (token) {
    try {
      await axios.post(
        `${API}/api/v1/auth/logout`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch {
      // Token may already be expired/blacklisted — fine, we're logging
      // out locally either way. The interceptor above will also catch
      // this 401 and redirect.
    }
  }
  removeToken();
}