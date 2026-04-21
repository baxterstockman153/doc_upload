export interface OrderResponse {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string; // "YYYY-MM-DD"
  source_file_name: string | null;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface ActivityLog {
  id: number;
  method: string;
  path: string;
  status_code: number;
  request_id: string;
  error_message: string | null;
  created_at: string; // ISO 8601
}
