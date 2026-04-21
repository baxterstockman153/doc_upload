"use client";

import { useState, useEffect } from "react";
import { fetchActivityLogs } from "@/lib/api";
import type { ActivityLog } from "@/types";

const LIMIT = 50;

function statusClass(code: number): string {
  if (code >= 500) return "text-red-700 font-semibold";
  if (code >= 400) return "text-yellow-700 font-semibold";
  if (code >= 300) return "text-blue-700 font-semibold";
  return "text-green-700 font-semibold";
}

export default function ActivityLogTable() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(newSkip: number) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActivityLogs(newSkip, LIMIT);
      setLogs(data);
      setSkip(newSkip);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(0);
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <button
          onClick={() => load(Math.max(0, skip - LIMIT))}
          disabled={skip === 0 || loading}
          className="px-3 py-1.5 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
        >
          Previous
        </button>
        <button
          onClick={() => load(skip + LIMIT)}
          disabled={logs.length < LIMIT || loading}
          className="px-3 py-1.5 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
        <button
          onClick={() => load(skip)}
          disabled={loading}
          className="px-3 py-1.5 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
        >
          Refresh
        </button>
        {loading && (
          <span className="text-sm text-gray-500">Loading…</span>
        )}
      </div>

      {error && (
        <div className="rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {["Timestamp", "Method", "Path", "Status Code", "Request ID", "Error"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {logs.length === 0 && !loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-4 text-center text-gray-400">
                  No logs found.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 whitespace-nowrap text-gray-600">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 font-mono font-medium">{log.method}</td>
                  <td className="px-4 py-2 font-mono text-gray-700">{log.path}</td>
                  <td className={`px-4 py-2 ${statusClass(log.status_code)}`}>
                    {log.status_code}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-gray-500">
                    {log.request_id}
                  </td>
                  <td className="px-4 py-2 text-red-600 text-xs">
                    {log.error_message ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
