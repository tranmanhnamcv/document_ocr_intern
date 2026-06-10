"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: "#f7f7f7",
      padding: "1.5rem",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "400px",
      }}>
        {/* Wordmark */}
        <p style={{
          fontSize: "11px",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          color: "#aaa",
          marginBottom: "8px",
          fontWeight: 500,
        }}>
          Document OCR
        </p>

        <h1 style={{
          fontSize: "22px",
          fontWeight: 500,
          color: "#111",
          marginBottom: "2rem",
          lineHeight: 1.2,
        }}>
          Sign in to your account
        </h1>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Email */}
          <div>
            <label style={{
              display: "block",
              fontSize: "13px",
              color: "#555",
              marginBottom: "6px",
              fontWeight: 500,
            }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={{
                width: "100%",
                padding: "10px 12px",
                fontSize: "14px",
                border: "1px solid #e0e0e0",
                borderRadius: "8px",
                outline: "none",
                backgroundColor: "#fff",
                color: "#111",
                boxSizing: "border-box",
                transition: "border-color 0.15s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "#111")}
              onBlur={(e) => (e.target.style.borderColor = "#e0e0e0")}
            />
          </div>

          {/* Password */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <label style={{ fontSize: "13px", color: "#555", fontWeight: 500 }}>
                Password
              </label>
              <Link href="/forgot-password" style={{ fontSize: "13px", color: "#555", textDecoration: "none" }}
                onMouseOver={(e) => ((e.target as HTMLElement).style.color = "#111")}
                onMouseOut={(e) => ((e.target as HTMLElement).style.color = "#555")}
              >
                Forgot password?
              </Link>
            </div>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: "100%",
                  padding: "10px 40px 10px 12px",
                  fontSize: "14px",
                  border: "1px solid #e0e0e0",
                  borderRadius: "8px",
                  outline: "none",
                  backgroundColor: "#fff",
                  color: "#111",
                  boxSizing: "border-box",
                  transition: "border-color 0.15s",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#111")}
                onBlur={(e) => (e.target.style.borderColor = "#e0e0e0")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                  color: "#aaa",
                  fontSize: "13px",
                  lineHeight: 1,
                }}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p style={{
              fontSize: "13px",
              color: "#c0392b",
              margin: 0,
              padding: "10px 12px",
              backgroundColor: "#fdf0ef",
              borderRadius: "6px",
              border: "1px solid #f5c6c2",
            }}>
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "11px",
              fontSize: "14px",
              fontWeight: 500,
              backgroundColor: loading ? "#888" : "#111",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              cursor: loading ? "not-allowed" : "pointer",
              marginTop: "4px",
              transition: "background-color 0.15s",
              letterSpacing: "0.01em",
            }}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {/* Footer */}
        <p style={{
          textAlign: "center",
          fontSize: "13px",
          color: "#888",
          marginTop: "1.5rem",
        }}>
          No account?{" "}
          <Link href="/register" style={{ color: "#111", textDecoration: "none", fontWeight: 500 }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
