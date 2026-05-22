export interface HistoryItem {
  id: number;
  user_id: number;
  track_id: number;
  artist_id: number;
  played_at: string;
  hour_of_day: number | null;
  day_of_week: string | null;
  context_type: string | null;
  track_spotify_id?: string;
  artist_spotify_id?: string;
}
