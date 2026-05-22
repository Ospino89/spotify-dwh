import { Link, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { AppLogo } from "./AppLogo";
import { profileInitials, useUser } from "@/context/UserContext";
import { logout } from "@/lib/auth";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/profile", label: "Profile" },
  { to: "/etl", label: "ETL" },
] as const;

export function Navbar() {
  const navigate = useNavigate();
  const { profile } = useUser();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const initials = profileInitials(profile?.display_name);
  const displayName = profile?.display_name ?? "Usuario";
  const email = profile?.email ?? profile?.spotify_id ?? "";

  return (
    <header className="sticky top-0 z-40 border-b border-[#2A2A2A] bg-[#0D0D0D]/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/dashboard" className="flex items-center">
          <AppLogo size="md" />
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="rounded-md px-3 py-1.5 text-sm text-[#888888] transition-colors hover:text-white"
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <div className="text-sm font-medium text-white">{displayName}</div>
            <div className="text-xs text-[#888888]">{email}</div>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1DB954] text-sm font-semibold text-black">
            {initials}
          </div>
          <button
            onClick={handleLogout}
            className="inline-flex items-center gap-1.5 rounded-md border border-[#2A2A2A] px-3 py-1.5 text-sm text-[#888888] transition-colors hover:border-[#1DB954] hover:text-[#1DB954]"
            aria-label="Log out"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0D0D0D]">
      <Navbar />
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
