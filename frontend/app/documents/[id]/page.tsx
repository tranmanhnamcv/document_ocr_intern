"use client";

import { authHeaders } from "../../lib/auth";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import axios from "axios";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL;

interface PageResult {
  page_number: number;
  text: string;
  confidence: number | null;
  pipeline_used: string | null;
}

interface DocumentDetail {
  id: number;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  created_at: string;
  extracted_text: string | null;
  total_pages: number | null;
  average_confidence: number | null;
  error_message: string | null;
  pages: PageResult[];
}

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activePage, setActivePage] = useState<number | null>(null);

  useEffect(() => {
    axios
      .get<DocumentDetail>(`${API}/api/v1/documents/${id}`, {
        headers: authHeaders(),
      })
      .then(({ data }) => {
        setDoc(data);
        if (data.pages?.length > 0) setActivePage(data.pages[0].page_number);
      })
      .catch((e) => {
        setError(
          axios.isAxiosError(e)
            ? e.response?.data?.detail ?? e.message
            : "Failed to load document"
        );
      })
      .finally(() => setLoading(false));
  }, [id]);

  const fmt = (bytes: number) =>
    bytes < 1024 * 1024
      ? `${(bytes / 1024).toFixed(1)} KB`
      : `${(bytes / 1024 / 1024).toFixed(1)} MB`;

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-gray-400 animate-pulse">Loading document…</p>
      </main>
    );
  }

  if (error || !doc) {
    return (
      <main className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-red-400">{error ?? "Document not found"}</p>
          <Link href="/" className="text-indigo-400 hover:text-indigo-300 text-sm">← Back</Link>
        </div>
      </main>
    );
  }

  const activePg = doc.pages?.find((p) => p.page_number === activePage);

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 px-4 py-10">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold truncate">{doc.original_filename}</h1>
            <p className="text-gray-400 text-sm mt-1">
              {doc.mime_type} · {fmt(doc.file_size)}
              {doc.total_pages != null && ` · ${doc.total_pages} page${doc.total_pages !== 1 ? "s" : ""}`}
              {doc.average_confidence != null && ` · ${doc.average_confidence.toFixed(1)}% avg confidence`}
              · {new Date(doc.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Link href="/search" className="text-sm text-indigo-400 hover:text-indigo-300 transition">
              ← Search
            </Link>
            <Link href="/" className="text-sm text-gray-400 hover:text-gray-300 transition ml-3">
              Home
            </Link>
          </div>
        </div>

        {/* Status / error banner */}
        {doc.status === "failed" && doc.error_message && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
            OCR failed: {doc.error_message}
          </div>
        )}

        {/* Single-page or no per-page breakdown */}
        {(!doc.pages || doc.pages.length === 0) && doc.extracted_text && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Extracted Text</p>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto">
              {doc.extracted_text}
            </pre>
          </div>
        )}

        {/* Multi-page viewer */}
        {doc.pages && doc.pages.length > 0 && (
          <div className="flex gap-4">

            {/* Page tabs (sidebar for many pages) */}
            {doc.pages.length > 1 && (
              <div className="w-24 shrink-0 space-y-1">
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Pages</p>
                {doc.pages.map((p) => (
                  <button
                    key={p.page_number}
                    onClick={() => setActivePage(p.page_number)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition ${
                      activePage === p.page_number
                        ? "bg-indigo-700 text-white"
                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                  >
                    Page {p.page_number}
                  </button>
                ))}
              </div>
            )}

            {/* Page content */}
            <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
              {activePg ? (
                <>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500 uppercase tracking-widest">
                      Page {activePg.page_number}
                    </p>
                    <div className="flex gap-3 text-xs text-gray-500">
                      {activePg.confidence != null && (
                        <span className="text-green-400">{activePg.confidence.toFixed(1)}% confidence</span>
                      )}
                      {activePg.pipeline_used && (
                        <span className="bg-gray-800 px-2 py-0.5 rounded">
                          {activePg.pipeline_used} pipeline
                        </span>
                      )}
                    </div>
                  </div>
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto">
                    {activePg.text || <span className="text-gray-600 italic">No text extracted for this page.</span>}
                  </pre>
                </>
              ) : (
                <p className="text-gray-500 text-sm">Select a page.</p>
              )}
            </div>
          </div>
        )}

      </div>
    </main>
  );
}