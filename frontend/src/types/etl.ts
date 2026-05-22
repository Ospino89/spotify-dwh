export interface EtlRun {
  audit_id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  artists_inserted: number;
  artists_skipped: number;
  tracks_inserted: number;
  tracks_skipped: number;
  history_inserted: number;
  history_skipped: number;
  cursor_after_ms: number | null;
  cursor_next_ms: number | null;
  error_msg: string | null;
}

export interface EtlRunResult {
  status: string;
  cursor_after_ms: number | null;
  cursor_next_ms: number | null;
  duration_ms: number;
  artists_inserted: number;
  artists_skipped: number;
  tracks_inserted: number;
  tracks_skipped: number;
  tracks_backfilled?: number;
  history_inserted: number;
  history_skipped: number;
}
