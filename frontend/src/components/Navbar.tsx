import { Link, Outlet, useNavigate } from "@tanstack/react-router";
import { LogOut } from "lucide-react";
import { AppLogo } from "./AppLogo";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/profile", label: "Profile" },
  { to: "/etl", label: "ETL" },
] as const;

export function Navbar() {
  const navigate = useNavigate();
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/dashboard" className="flex items-center">
          <AppLogo size="md" />
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
              activeProps={{ className: "rounded-md px-3 py-1.5 text-sm text-foreground bg-secondary" }}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <div className="text-sm font-medium text-foreground">Alex Morgan</div>
            <div className="text-xs text-muted-foreground">alex@wrapped.app</div>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
            AM
          </div>
          <button
            onClick={() => navigate({ to: "/login" })}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-primary"
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
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}

export function AuthenticatedLayout() {
  return (
    <PageShell>
      <Outlet />
    </PageShell>
  );
}