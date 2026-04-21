import type { OrderResponse, ActivityLog } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function uploadPDF(file: File): Promise<OrderResponse> {
  const formData = new FormData();
  formData.append("file", file);
  // Do NOT set Content-Type manually — browser sets multipart boundary
  const res = await fetch(`${BASE_URL}/orders/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchActivityLogs(
  skip: number,
  limit: number
): Promise<ActivityLog[]> {
  const res = await fetch(
    `${BASE_URL}/activity-logs?skip=${skip}&limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch activity logs: ${res.status}`);
  }
  return res.json();
}
