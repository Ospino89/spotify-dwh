# Frontend — Mi Spotify Wrapped

React + Vite + Tailwind. Consume la API FastAPI en `/v1`.

## Requisitos

- Node.js 18+
- Backend corriendo en `http://127.0.0.1:8000`
- `FRONTEND_URL=http://localhost:5173` en el `.env` de la raíz del proyecto

## Instalación

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173).

## Flujo de autenticación

1. **Connect with Spotify** → `GET /v1/auth/login`
2. Spotify redirige al backend → `GET /v1/auth/callback`
3. Backend redirige a `/callback?token=<jwt>`
4. El frontend guarda el token en `localStorage` (`app_token`)

## Páginas

| Ruta | API |
|------|-----|
| `/dashboard` | artists, tracks, history |
| `/profile` | `GET /v1/profile/me` |
| `/etl` | `POST /v1/etl/run`, `GET /v1/etl/status` |
