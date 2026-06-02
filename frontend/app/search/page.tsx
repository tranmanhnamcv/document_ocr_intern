// frontend/app/search/page.tsx
"use client";

import { authHeaders } from "../lib/auth";
import { useState, useCallback } from "react";
import axios from "axios";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL;

interface DocumentItem {
  id: number;
  original_filename: string;
  status: string;
  total_pages: number | null;
  average_confidence: number | null;
  file_size: number;
  created_at: string;
}

interface SearchResult {
  document: DocumentItem;
  rank: number;
  headline: string | null;
}

interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  page: number;
  limit: number;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const doSearch = useCallback(async (q: string, p = 1) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.get<SearchResponse>(`${API}/api/v1/search/`, {
        params: { q, page: p, limit: 20 },
        headers: authHeaders(),
      });
      setResponse(data);
      setPage(p);
    } catch (e: unknown) {
      const msg = axios.isAxiosError(e) ? e.response?.data?.detail ?? e.message : "Search failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    doSearch(query, 1);
  };

  const totalPages = response ? Math.ceil(response.total / 20) : 0;

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 px-4 py-10">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Search Documents</h1>
            <p className="text-gray-400 mt-1 text-sm">Full-text search across extracted OCR text</p>
          </div>
          <Link href="/" className="text-sm text-indigo-400 hover:text-indigo-300 transition">
            ← Upload
          </Link>
        </div>

        {/* Search bar */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search extracted text…"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-lg text-sm font-medium transition"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Results summary */}
        {response && !loading && (
          <p className="text-gray-400 text-sm">
            {response.total === 0
              ? `No results for "${response.query}"`
              : `${response.total} result${response.total !== 1 ? "s" : ""} for "${response.query}"`}
          </p>
        )}

        {/* Result cards */}
        <div className="space-y-4">
          {response?.results.map(({ document: doc, rank, headline }) => (
            <div
              key={doc.id}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 hover:border-gray-600 transition"
            >
              {/* Top row */}
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium text-gray-100 truncate">{doc.original_filename}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {doc.total_pages != null ? `${doc.total_pages} page${doc.total_pages !== 1 ? "s" : ""}` : "—"}
                    {doc.average_confidence != null && (
                      <> · <span className="text-green-400">{doc.average_confidence.toFixed(1)}% confidence</span></>
                    )}
                    {" "}· {(doc.file_size / 1024).toFixed(1)} KB
                    · {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className="shrink-0 text-xs bg-gray-800 text-gray-400 rounded px-2 py-1">
                  score {rank.toFixed(3)}
                </span>
              </div>

              {/* Headline snippet */}
              {headline && (
                <div
                  className="text-sm text-gray-300 leading-relaxed bg-gray-800/50 rounded-lg px-3 py-2
                             [&_mark]:bg-yellow-400/30 [&_mark]:text-yellow-200 [&_mark]:rounded [&_mark]:px-0.5"
                  dangerouslySetInnerHTML={{ __html: headline }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 pt-2">
            <button
              onClick={() => doSearch(query, page - 1)}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded bg-gray-800 text-sm disabled:opacity-40 hover:bg-gray-700 transition"
            >
              ← Prev
            </button>
            <span className="px-3 py-1.5 text-sm text-gray-400">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => doSearch(query, page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded bg-gray-800 text-sm disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Next →
            </button>
          </div>
        )}

      </div>
    </main>
  );
}