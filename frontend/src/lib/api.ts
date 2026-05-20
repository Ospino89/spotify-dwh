const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("app_token");
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem("app_token");
    window.location.href = "/login";
    throw new Error("Sesión expirada");
  }
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}