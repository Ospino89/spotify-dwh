import { apiFetch } from "./api";
import type { Artist } from "@/types/artist";
import type { EtlRun, EtlRunResult } from "@/types/etl";
import type { HistoryItem } from "@/types/history";
import type { Profile } from "@/types/user";
import type { Track } from "@/types/track";

export function getProfile() {
  return apiFetch<Profile>("/v1/profile/me");
}

export function getTopArtists(limit = 10) {
  return apiFetch<Artist[]>(`/v1/artists/top?limit=${limit}`);
}

export function getTopTracks(limit = 10) {
  return apiFetch<Track[]>(`/v1/tracks/top?limit=${limit}`);
}

export function getListeningHistory(limit = 50) {
  return apiFetch<HistoryItem[]>(`/v1/history/recently-played?limit=${limit}`);
}

/** 24 conteos por hora (0-23) desde todo el DWH — alineado con la query SQL analitica. */
export function getPlaysByHour() {
  return apiFetch<number[]>("/v1/history/plays-by-hour");
}

export type GenrePlays = { name: string; plays: number };

/** Generos por reproducciones (fact + UNNEST genres), no solo ultimas 50 filas. */
export function getDominantGenres(limit = 10) {
  return apiFetch<GenrePlays[]>(`/v1/history/dominant-genres?limit=${limit}`);
}

export function runEtl() {
  return apiFetch<EtlRunResult>("/v1/etl/run", { method: "POST" });
}

export function getEtlStatus() {
  return apiFetch<EtlRun[]>("/v1/etl/status");
}

export function formatDurationMs(ms: number | null | undefined): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatTrackDuration(durationMs: number | null): string {
  if (durationMs == null) return "—";
  const totalSec = Math.floor(durationMs / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}:${String(sec).padStart(2, "0")}`;
}

export function aggregatePlaysByHour(history: HistoryItem[]): number[] {
  const hours = Array.from({ length: 24 }, () => 0);
  for (const row of history) {
    if (row.hour_of_day != null && row.hour_of_day >= 0 && row.hour_of_day < 24) {
      hours[row.hour_of_day] += 1;
    }
  }
  return hours;
}

export function aggregateGenres(
  history: HistoryItem[],
  artists: Artist[]
): { name: string; plays: number }[] {
  const genresByArtist = new Map(
    artists.map((a) => [a.spotify_id, a.genres?.length ? a.genres : []])
  );
  const counts = new Map<string, number>();

  for (const row of history) {
    const artistId = row.artist_spotify_id;
    if (!artistId) continue;
    const genres = genresByArtist.get(artistId) ?? [];
    for (const genre of genres) {
      counts.set(genre, (counts.get(genre) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .map(([name, plays]) => ({ name, plays }))
    .sort((a, b) => b.plays - a.plays)
    .slice(0, 5);
}
