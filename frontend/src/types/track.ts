export interface Track {
  track_id: number;
  spotify_id: string;
  name: string;
  artist_id: number | null;
  album_name: string | null;
  duration_ms: number | null;
  popularity: number | null;
  explicit: boolean;
  loaded_at: string;
}
