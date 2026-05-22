import { ExternalLink, Loader2 } from "lucide-react";
import { PageShell } from "@/components/Navbar";
import { profileInitials, useUser } from "@/context/UserContext";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
      <div className="text-xs font-semibold uppercase tracking-wider text-[#888888]">{label}</div>
      <div className="mt-2 text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { profile, loading } = useUser();

  if (loading) {
    return (
      <PageShell>
        <div className="flex min-h-[40vh] items-center justify-center gap-3 text-[#888888]">
          <Loader2 className="h-6 w-6 animate-spin text-[#1DB954]" />
          Cargando perfil...
        </div>
      </PageShell>
    );
  }

  if (!profile) {
    return (
      <PageShell>
        <p className="text-[#888888]">No se pudo cargar el perfil.</p>
      </PageShell>
    );
  }

  const initials = profileInitials(profile.display_name);
  const memberSince = new Date(profile.loaded_at).toLocaleDateString("es-CO", {
    month: "short",
    year: "numeric",
  });

  return (
    <PageShell>
      <div className="grid gap-8 md:grid-cols-[320px_1fr]">
        <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-8 text-center">
          <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-[#1DB954] text-4xl font-bold text-black">
            {initials}
          </div>
          <h1 className="mt-6 text-[28px] font-bold leading-tight text-white">
            {profile.display_name ?? "Sin nombre"}
          </h1>
          <p className="mt-1 text-sm text-[#888888]">{profile.email ?? "—"}</p>
          <div className="mt-4 text-sm text-[#888888]">{profile.country ?? "—"}</div>
          {profile.product && (
            <span className="mt-4 inline-block rounded-full bg-[#1DB954] px-3 py-1 text-xs font-semibold capitalize text-black">
              {profile.product}
            </span>
          )}
        </div>
        <div className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-3">
            <StatCard label="Seguidores" value={String(profile.followers ?? 0)} />
            <StatCard label="Cuenta" value={profile.product ?? "—"} />
            <StatCard label="En DWH desde" value={memberSince} />
          </div>
          <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">Spotify ID</h3>
            <p className="mt-3 font-mono text-sm text-white">{profile.spotify_id}</p>
          </div>
          <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">About</h3>
            <p className="mt-3 text-sm text-white">
              Perfil sincronizado desde Spotify vía OAuth PKCE. Los datos analíticos viven en tu
              data warehouse personal.
            </p>
          </div>
          <a
            href={`https://open.spotify.com/user/${profile.spotify_id}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-[#1DB954] px-5 py-2.5 text-sm font-semibold text-[#1DB954] transition-colors hover:bg-[#1DB954] hover:text-black"
          >
            Ver en Spotify
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </PageShell>
  );
}
