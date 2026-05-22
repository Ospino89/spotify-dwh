export interface Artist {
  artist_id: number;
  spotify_id: string;
  name: string;
  popularity: number | null;
  followers_count: number | null;
  genres: string[];
  loaded_at: string;
}
