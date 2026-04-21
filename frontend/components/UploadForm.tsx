"use client";

import { useState } from "react";
import { uploadPDF } from "@/lib/api";
import type { OrderResponse } from "@/types";

export default function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await uploadPDF(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            PDF File
          </label>
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !file}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
        >
          {loading ? "Uploading…" : "Upload PDF"}
        </button>
      </form>

      {error && (
        <div className="rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded border border-green-300 bg-green-50 px-4 py-4 space-y-1 text-sm">
          <p className="font-semibold text-green-800 mb-2">Upload successful</p>
          <p>
            <span className="font-medium">Name:</span> {result.first_name}{" "}
            {result.last_name}
          </p>
          <p>
            <span className="font-medium">Date of Birth:</span>{" "}
            {result.date_of_birth}
          </p>
          <p>
            <span className="font-medium">Source File:</span>{" "}
            {result.source_file_name ?? "—"}
          </p>
          <p>
            <span className="font-medium">Created:</span>{" "}
            {new Date(result.created_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
