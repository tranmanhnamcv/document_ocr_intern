"use client";

import { authHeaders, getToken, logout } from "./lib/auth";
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL;

interface Document {
  id: number;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  created_at: string;
  extracted_text?: string;
  total_pages?: number;
  average_confidence?: number;
  error_message?: string;
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // SSR-safe auth check
  useEffect(() => {
  const token = getToken();
  setIsLoggedIn(!!token);
  if (token) {
    axios
      .get<Document[]>(`${API}/api/v1/documents/`, { headers: authHeaders() })
      .then(({ data }) => setDocuments(data))
      .catch(() => {});
  }
}, []);

  // Poll while any document is pending/processing
  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );

    if (hasPending) {
      pollingRef.current = setInterval(async () => {
        try {
          const { data } = await axios.get<Document[]>(
            `${API}/api/v1/documents/`,
            { headers: authHeaders() }
          );
          setDocuments(data);
        } catch {
          // silently ignore poll errors
        }
      }, 3000);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [documents]);

  const uploadFile = async (file: File) => {
    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await axios.post<{ message: string; document: Document }>(
        `${API}/api/v1/documents/upload`,
        form,
        { headers: authHeaders() }
      );
      setDocuments((prev) => [data.document, ...prev]);
      setExpandedId(data.document.id);
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const fmt = (bytes: number) =>
    bytes < 1024 * 1024
      ? `${(bytes / 1024).toFixed(1)} KB`
      : `${(bytes / 1024 / 1024).toFixed(1)} MB`;

  const statusStyle = (status: string) => {
    switch (status) {
      case "completed":  return "bg-green-900 text-green-300";
      case "failed":     return "bg-red-900 text-red-300";
      case "processing": return "bg-blue-900 text-blue-300";
      default:           return "bg-yellow-900 text-yellow-300";
    }
  };

  const statusLabel = (status: string) => {
    if (status === "pending" || status === "processing") return "Extracting...";
    return status;
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">OCR Document Search</h1>
            <p className="text-gray-400 mt-1">Upload images or PDFs to extract and search text</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isLoggedIn ? (
              <button
                onClick={async () => {
                  await logout();
                  window.location.href = "/login";
                }}
                className="px-4 py-2 text-sm font-medium text-gray-300 border border-gray-700 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
              >
                Log out
              </button>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-300 border border-gray-700 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors"
                >
                  Register
                </Link>
              </>
            )}
            <Link
              href="/search"
              className="px-4 py-2 text-sm font-medium text-gray-300 border border-gray-700 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
            >
              Search →
            </Link>
          </div>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => !uploading && fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors
            ${uploading ? "cursor-default" : "cursor-pointer"}
            ${dragOver
              ? "border-blue-400 bg-blue-950/30"
              : "border-gray-700 hover:border-gray-500 bg-gray-900"
            }`}
        >
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            accept=".jpg,.jpeg,.png,.tiff,.bmp,.webp,.pdf"
            onChange={onFileChange}
          />
          <div className="text-5xl mb-4">📄</div>
          {uploading ? (
            <p className="text-blue-400 font-medium animate-pulse">Uploading…</p>
          ) : (
            <>
              <p className="text-gray-300 font-medium">Drop a file here or click to browse</p>
              <p className="text-gray-500 text-sm mt-1">
                Supports JPG, PNG, TIFF, BMP, WEBP, PDF — up to 50 MB
              </p>
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-950 border border-red-700 text-red-300 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Uploaded documents */}
        {documents.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-300">Your Documents</h2>
            {documents.map((doc) => (
              <div key={doc.id} className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">

                {/* Doc row */}
                <div
                  className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-800/50 transition-colors"
                  onClick={() => setExpandedId(expandedId === doc.id ? null : doc.id)}
                >
                  <div>
                    <p className="font-medium text-white">{doc.original_filename}</p>
                    <p className="text-sm text-gray-500">
                      {doc.mime_type} · {fmt(doc.file_size)}
                      {doc.total_pages && doc.total_pages > 1 && ` · ${doc.total_pages} pages`}
                      {doc.average_confidence != null && ` · ${doc.average_confidence.toFixed(0)}% confidence`}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${statusStyle(doc.status)}`}>
                      {statusLabel(doc.status)}
                      {(doc.status === "pending" || doc.status === "processing") && (
                        <span className="ml-1 animate-pulse">●</span>
                      )}
                    </span>
                    {doc.status === "completed" && (
                      <span className="text-gray-500 text-xs">
                        {expandedId === doc.id ? "▲" : "▼"}
                      </span>
                    )}
                  </div>
                </div>

                {/* Extracted text */}
                {expandedId === doc.id && doc.status === "completed" && doc.extracted_text && (
                  <div className="border-t border-gray-800 px-4 py-4">
                    <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Extracted Text</p>
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-950 rounded-lg p-4 max-h-72 overflow-y-auto leading-relaxed">
                      {doc.extracted_text}
                    </pre>
                  </div>
                )}

                {/* Failed message */}
                {doc.status === "failed" && doc.error_message && (
                  <div className="border-t border-gray-800 px-4 py-3">
                    <p className="text-sm text-red-400">{doc.error_message}</p>
                  </div>
                )}

              </div>
            ))}
          </div>
        )}

      </div>
    </main>
  );
}
