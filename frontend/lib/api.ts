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
    let message: string;
    try {
      const body = await res.json();
      message = typeof body?.detail === "string"
        ? body.detail
        : `Upload failed (${res.status})`;
    } catch {
      message = `Upload failed (${res.status})`;
    }
    throw new Error(message);
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
