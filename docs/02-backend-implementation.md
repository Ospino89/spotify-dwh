## Documentación de Implementación — Backend API

---

## 1. Qué se implementó

Se construyó el backend completo del proyecto Mi Spotify Wrapped: una API REST versionada que integra la Spotify Web API, persiste los datos en un Data Warehouse en PostgreSQL (Neon) y los expone mediante endpoints protegidos con JWT.

El desarrollo abarcó:

- Autenticación OAuth 2.0 con PKCE — sin registro propio, todo a través de Spotify
- Pipeline ETL completo: extracción desde Spotify, transformación y carga en star schema
- API REST bajo prefijo `/v1` con 8 endpoints documentados en Swagger
- Arquitectura en capas: `routers → services → database`
- Modelos Pydantic con sufijos Base / Request / Response
- Docstrings con `Args` y `Returns` en todas las funciones y archivos

---

## 2. Arquitectura

### 2.1 Estructura de archivos

```
backend/
├── main.py                  ← FastAPI app, CORS, routers
└── app/
    ├── core/
    │   ├── config.py         ← Variables de entorno (Pydantic Settings)
    │   ├── database.py       ← Conexión psycopg2 a Neon
    │   ├── security.py       ← Dependency get_current_user (JWT)
    │   └── spotify_client.py ← Cliente HTTP reutilizable para Spotify
    └── v1/
        ├── api.py            ← Agrupa todos los routers
        ├── routers/          ← Endpoints HTTP
        ├── services/         ← Lógica de negocio y ETL
        └── schemas/          ← Modelos Pydantic (Base/Request/Response)
```

### 2.2 Star Schema (Data Warehouse)

| Tabla | Tipo | Descripción |
|---|---|---|
| `dwh.dim_users` | Dimensión | Perfil del usuario y tokens de Spotify |
| `dwh.dim_artists` | Dimensión | Top artistas del usuario |
| `dwh.dim_tracks` | Dimensión | Top tracks del usuario |
| `dwh.fact_listening_history` | Hechos | Historial (grain: user + played_at) |
| `dwh.etl_audit` | Auditoría | Registro de cada ejecución del ETL |
| `public.pkce_sessions` | Operacional | Estado temporal del flujo OAuth PKCE |

---

## 3. Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/v1/auth/login` | Inicia flujo PKCE con Spotify |
| GET | `/v1/auth/callback` | Recibe code, emite JWT |
| GET | `/v1/profile/me` | Perfil del usuario autenticado |
| GET | `/v1/artists/top` | Top artistas filtrados por usuario |
| GET | `/v1/tracks/top` | Top tracks filtrados por usuario |
| GET | `/v1/history/recently-played` | Historial de reproducciones |
| POST | `/v1/etl/run` | Ejecuta el pipeline ETL completo |
| GET | `/v1/etl/status` | Estado del DWH y últimas ejecuciones |

---

## 4. Flujo de autenticación PKCE

El proyecto usa OAuth 2.0 con PKCE — no hay registro propio, la identidad viene exclusivamente de Spotify.

**Paso 1 — Inicio de sesión**
- `GET /v1/auth/login` genera `code_verifier`, `code_challenge` y `state`
- Guarda `{state: verifier}` en `public.pkce_sessions`
- Redirige a `accounts.spotify.com/authorize`

**Paso 2 — Callback de Spotify**
- `GET /v1/auth/callback?code=...&state=...` valida `state` en `pkce_sessions`
- Intercambia el `code` por `access_token` y `refresh_token`
- Hace UPSERT en `dwh.dim_users` con el perfil del usuario
- Emite JWT `{sub: spotify_id, exp: now+8h}`
- Redirige a `FRONTEND_URL/callback?token=JWT`

**Paso 3 — Requests protegidas**
- Header: `Authorization: Bearer <JWT>`
- Dependency `get_current_user` decodifica el JWT y extrae `spotify_id`
- Todos los endpoints de datos validan este header

---

## 5. Pipeline ETL

El ETL se ejecuta con `POST /v1/etl/run` y opera en tres fases secuenciales:

| Fase | Operación | Detalle |
|---|---|---|
| EXTRACT | Llama a la Spotify API | Top artists, top tracks, recently played |
| TRANSFORM | Normaliza y enriquece | Fechas, `hour_of_day`, `day_of_week`, `context_type` |
| LOAD | Inserta en el DWH | `ON CONFLICT DO NOTHING` — operación idempotente |

---

## Prompt utilizado

Crea schemas Pydantic: auth.py, profile.py (Base/Request/Response) , Implementa GET /v1/auth/login — generacion PKCE y redirect a Spotify , Crea app/core/spotify_client.py — cliente HTTP reutilizable , revisar que la estructura de carpetas sea consistente  

## Técnica de prompting aplicada

No se aplicó ninguna técnica de prompting estructurada. 

---
