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
    await axios.post(
      `${API}/api/v1/auth/logout`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
  }
  removeToken();
}