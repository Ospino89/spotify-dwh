# Mi Spotify Wrapped

Proyecto integrador full stack: construye un **Data Warehouse personal** con tu historial de Spotify, lo expone mediante una **API REST** (FastAPI) y lo visualizas en un **dashboard** (React).

Extrae top artistas, top tracks y reproducciones recientes desde la [Spotify Web API](https://developer.spotify.com/documentation/web-api), los carga en un **star schema** en PostgreSQL (Neon) y genera métricas tipo *Wrapped* (hora pico, géneros dominantes, rankings).

---

## Estructura del proyecto

```
mi-spotify-wrapped/
├── .env                    # Variables de entorno (raíz, no versionado)
├── .gitignore
├── requirements.txt        # Dependencias Python del backend
├── README.md
│
├── backend/
│   ├── main.py             # Entrada FastAPI
│   ├── alembic/            # Migraciones del DWH
│   ├── tests/              # Tests con pytest
│   └── app/
│       ├── core/           # config, DB, JWT, cliente Spotify
│       └── v1/
│           ├── routers/    # auth, profile, artists, tracks, history, etl
│           ├── schemas/    # Pydantic
│           └── services/   # ETL y lógica de negocio
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # Login, Dashboard, Profile, ETL
│   │   ├── lib/            # Cliente API y agregaciones
│   │   └── context/        # Sesión del usuario
│   └── package.json
│
└── docs/
    └── analytical_queries.sql   # 5 preguntas analíticas del DWH
```

Documentación detallada del API: [backend/README.md](backend/README.md)  
Frontend: [frontend/README.md](frontend/README.md)

---

## Arquitectura

### Star schema (PostgreSQL / Neon)

| Tabla | Tipo | Origen Spotify |
|-------|------|----------------|
| `dwh.dim_users` | Dimensión | `GET /v1/me` |
| `dwh.dim_artists` | Dimensión | `GET /v1/me/top/artists` |
| `dwh.dim_tracks` | Dimensión | `GET /v1/me/top/tracks` |
| `dwh.fact_listening_history` | Hechos | `GET /v1/me/player/recently-played` |
| `dwh.etl_audit` | Auditoría | Generado por el ETL |
| `public.pkce_sessions` | Operacional | OAuth PKCE (temporal) |

### Flujo de datos

```
Spotify API  →  ETL (extract / transform / load)  →  PostgreSQL (Neon)
                                                      ↓
                                              FastAPI /v1/*
                                                      ↓
                                              React Dashboard
```

---

## Requisitos

| Componente | Versión |
|------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | Neon (recomendado) o local |
| Cuenta Spotify | App en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) |

---

## Instalación rápida

### 1. Clonar e instalar

```bash
git clone https://github.com/tu-usuario/mi-spotify-wrapped.git
cd mi-spotify-wrapped

# Backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
pip install psycopg2-binary    # conexión PostgreSQL

# Frontend
cd frontend
npm install
cd ..
```

### 2. Variables de entorno

Crea un archivo `.env` en la **raíz del proyecto** (el backend lo lee desde ahí):

```env
# Spotify
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/v1/auth/callback

# Base de datos (Neon)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# App
APP_NAME=Spotify DWH API
APP_VERSION=1.0.0
SECRET_KEY=clave_secreta_minimo_32_caracteres
FRONTEND_URL=http://localhost:3000
```

En `frontend/.env` (opcional, valores por defecto en código):

```env
VITE_API_URL=http://127.0.0.1:8000
```

> El archivo `.env` de la raíz **no** debe subirse a git.

### 3. Spotify Developer Dashboard

1. Crear o abrir una app en [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard).
2. En **Redirect URIs** agregar: `http://127.0.0.1:8000/v1/auth/callback`
3. Copiar **Client ID** y **Client Secret** al `.env`.
4. Scopes usados: `user-read-private`, `user-read-email`, `user-top-read`, `user-read-recently-played`.

### 4. Migraciones (tablas del DWH)

```bash
cd backend
alembic upgrade head
```

Comprueba en Neon: `dim_users`, `dim_artists`, `dim_tracks`, `fact_listening_history`, `etl_audit`, `pkce_sessions`.

---

## Ejecutar el proyecto

Abre **dos terminales**:

**Terminal 1 — API**

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

- App: http://localhost:3000  

`FRONTEND_URL` en el `.env` debe coincidir con el puerto de Vite (`3000` por defecto en `vite.config.ts`).

---

## Autenticación

OAuth 2.0 con **PKCE** (solo Spotify, sin usuario/contraseña propio).

1. En el frontend: **Connect with Spotify** → redirige a `GET /v1/auth/login`.
2. Autorizas en Spotify.
3. El backend recibe el callback, guarda tokens en `dim_users` y redirige a:  
   `{FRONTEND_URL}/callback?token=<jwt>`
4. El frontend guarda el JWT en `localStorage` (`app_token`).
5. Las peticiones llevan: `Authorization: Bearer <token>` (válido ~8 h).

---

## API pública (`/v1`)

Endpoints visibles en Swagger (alineados con el README del workshop):

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/v1/auth/login` | No | Inicia OAuth PKCE |
| GET | `/v1/auth/callback` | No | Callback Spotify → JWT |
| GET | `/v1/profile/me` | Sí | Perfil en `dim_users` |
| GET | `/v1/artists/top` | Sí | Top artistas del DWH |
| GET | `/v1/tracks/top` | Sí | Top tracks del DWH |
| GET | `/v1/history/recently-played` | Sí | Últimas reproducciones |
| POST | `/v1/etl/run` | Sí | Pipeline ETL completo |
| GET | `/v1/etl/status` | Sí | Historial de ejecuciones |

El dashboard también consume rutas internas (`plays-by-hour`, `dominant-genres`, `repair-artists`) que no aparecen en Swagger pero siguen disponibles para la app.

---

## Pipeline ETL

```
EXTRACT   →  Spotify: top artists, top tracks, recently played (cursor incremental)
TRANSFORM →  Normaliza fechas, hour_of_day, day_of_week, genres, popularity
LOAD      →  Upsert en dimensiones + hechos (idempotente por user + played_at)
```

**Ejecutar:** botón en la página **ETL** del frontend o `POST /v1/etl/run` con JWT.

**Recomendación:** ejecutar el ETL **al menos una vez al día**. Spotify solo expone las últimas ~50 reproducciones; sin cargas frecuentes se pierde historial.

Tras cada corrida se registra métricas en `dwh.etl_audit` (`artists_inserted`, `history_inserted`, cursores, etc.).

---

## Frontend — Páginas

| Ruta | Contenido |
|------|-----------|
| `/login` | Conectar con Spotify |
| `/callback` | Recibe y guarda el JWT |
| `/dashboard` | Top artistas/tracks, hora pico, géneros |
| `/profile` | Datos de `dim_users` |
| `/etl` | Sincronizar y ver estado del pipeline |

---

## Consultas analíticas (SQL)

Las 5 preguntas del proyecto están en [docs/analytical_queries.sql](docs/analytical_queries.sql):

1. Hora del día con más reproducciones  
2. Top 5 artistas por plays  
3. Popularidad promedio de tracks  
4. Géneros dominantes (`UNNEST(genres)`)  
5. Ranking de tracks por día de la semana (`RANK()`)

Ejecútalas en el SQL Editor de Neon sobre tu base cargada.

---

## Tests

```bash
cd backend
pytest tests/ -v
```

Con cobertura:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Notas técnicas

- **Géneros:** la API de Spotify suele devolver `genres: []` en modo Development; el ETL puede completar tags vía MusicBrainz.
- **Hora pico:** `hour_of_day` se deriva de `played_at` en UTC (mismo criterio en SQL y dashboard).
- **Carga incremental:** el ETL usa el cursor `after` de `recently-played` y lo persiste en `etl_audit`.

---

## Licencia y autoría

Proyecto académico / integrador. Ajusta autor y licencia según tu entrega.
