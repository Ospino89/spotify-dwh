import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { isTokenExpired } from "@/lib/auth";

export default function CallbackPage() {
  const navigate = useNavigate();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get("token");

    if (tokenFromUrl) {
      localStorage.setItem("app_token", tokenFromUrl);
      window.history.replaceState({}, "", "/callback");
      navigate("/dashboard", { replace: true });
      return;
    }

    // React StrictMode ejecuta el effect 2 veces: la URL ya no tiene token,
    // pero puede estar guardado en localStorage tras la primera pasada.
    const stored = localStorage.getItem("app_token");
    if (stored && !isTokenExpired(stored)) {
      navigate("/dashboard", { replace: true });
      return;
    }

    navigate("/login", { replace: true });
  }, [navigate]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-[#0D0D0D] px-6">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#1DB954]" />
      <div className="text-center">
        <p className="text-base font-medium text-white">Connecting your Spotify account...</p>
        <p className="mt-2 text-sm text-[#888888]">You&apos;ll be redirected automatically.</p>
      </div>
    </div>
  );
}
