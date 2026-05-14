# 🎵 Mi Spotify Wrapped
### Backend API — FastAPI + PostgreSQL DWH

Proyecto integrador de backend que construye un Data Warehouse personal con tu historial de Spotify.
Extrae tus top artistas, top tracks y reproducciones recientes via la Spotify Web API,
los carga en un star schema en PostgreSQL (Neon) y los expone a través de una API REST versionada.

---

## 🗂️ Estructura del Proyecto

```
mi-spotify-wrapped/
├── .env                          # Variables de entorno (no versionado)
├── .env.example                  # Plantilla del .env
├── .gitignore
├── requirements.txt
│
└── backend/
    ├── main.py                   # Punto de entrada de la aplicación
    ├── alembic.ini               # Configuración de Alembic
    ├── alembic/
    │   ├── env.py                # Configuración de migraciones
    │   └── versions/             # Historial de migraciones
    │
    └── app/
        ├── core/
        │   ├── config.py         # Variables de entorno con pydantic Settings
        │   ├── database.py       # Conexión a PostgreSQL
        │   ├── security.py       # JWT + dependency get_current_user
        │   └── spotify_client.py # Cliente HTTP para Spotify API
        │
        └── v1/
            ├── api.py            # Registro de todos los routers bajo /v1
            ├── routers/          # Endpoints (auth, profile, artists, tracks, history, etl)
            ├── schemas/          # Schemas Pydantic (Base / Request / Response)
            └── services/         # Lógica de negocio y ETL
```

---

## 🏗️ Arquitectura

El proyecto implementa un **star schema** en PostgreSQL con las siguientes tablas:

| Tabla | Tipo | Descripción |
|---|---|---|
| `dwh.dim_users` | Dimensión | Perfil del usuario y tokens de Spotify |
| `dwh.dim_artists` | Dimensión | Top artistas del usuario |
| `dwh.dim_tracks` | Dimensión | Top tracks del usuario |
| `dwh.fact_listening_history` | Hechos | Historial de reproducciones (grain: user + played_at) |
| `dwh.etl_audit` | Auditoría | Registro de cada ejecución del pipeline ETL |
| `public.pkce_sessions` | Operacional | Estado temporal del flujo OAuth PKCE |

---

## ⚙️ Requisitos

- Python 3.11+
- PostgreSQL (Neon recomendado)
- Cuenta de Spotify y app registrada en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/mi-spotify-wrapped.git
cd mi-spotify-wrapped
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```env
# Spotify
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRE=http://127.0.0.1:8000/v1/auth/callback

# Base de datos Neon
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# App
SECRET_KEY=clave_secreta_minimo_32_caracteres
FRONTEND_URL=http://localhost:3000
```

> ⚠️ El archivo `.env` nunca debe subirse al repositorio.

### 5. Configurar la app en Spotify Developer Dashboard

1. Ir a [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Crear una app o usar una existente
3. En **Redirect URIs** agregar: `http://127.0.0.1:8000/v1/auth/callback`
4. Copiar el `Client ID` y `Client Secret` al `.env`

### 6. Aplicar migraciones (crear tablas en la DB)

```bash
cd backend
alembic upgrade head
```

Verifica que se crearon las 6 tablas en Neon: `pkce_sessions`, `dim_users`, `dim_artists`, `dim_tracks`, `fact_listening_history`, `etl_audit`.

---

## ▶️ Correr la API

```bash
cd backend
uvicorn main:app --reload
```

La API queda disponible en:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health

---

## 🔐 Autenticación

El proyecto usa **OAuth 2.0 con PKCE** — no hay registro propio, todo pasa por Spotify.

### Flujo completo:

1. Abrir en el navegador: `http://127.0.0.1:8000/v1/auth/login`
2. Iniciar sesión con tu cuenta de Spotify
3. Spotify redirige a `http://localhost:3000?token=eyJ...`
4. Copiar el token JWT de la URL
5. Usar el token en el header de todas las peticiones: `Authorization: Bearer <token>`

> El token tiene una validez de **8 horas**.

---

## 📡 Endpoints

Todos los endpoints de datos requieren el header `Authorization: Bearer <token>`.

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `/v1/auth/login` | No | Inicia el flujo OAuth PKCE |
| GET | `/v1/auth/callback` | No | Callback de Spotify, emite JWT |
| GET | `/v1/profile/me` | ✅ | Perfil del usuario autenticado |
| GET | `/v1/artists/top` | ✅ | Top artistas desde dim_artists |
| GET | `/v1/tracks/top` | ✅ | Top tracks desde dim_tracks |
| GET | `/v1/history/recently-played` | ✅ | Historial de reproducciones |
| POST | `/v1/etl/run` | ✅ | Ejecuta el pipeline ETL completo |
| GET | `/v1/etl/status` | ✅ | Últimas 20 ejecuciones del ETL |

---

## 🔄 Pipeline ETL

El ETL extrae datos de Spotify en 3 fases:

```
EXTRACT  →  Llama a la Spotify API (top artists, top tracks, recently played)
TRANSFORM →  Normaliza fechas, deriva hour_of_day, day_of_week, context_type
LOAD     →  Inserta en el DWH con ON CONFLICT DO NOTHING (idempotente)
```

### Ejecutar el ETL

```bash
# Via Swagger: POST /v1/etl/run
# O via curl:
curl -X POST http://127.0.0.1:8000/v1/etl/run \
  -H "Authorization: Bearer <tu_token>"
```

> ⚠️ **Importante:** Ejecutar el ETL al menos **una vez al día**. Spotify solo expone las últimas 50 reproducciones — si no se corre diariamente se pierde historial permanentemente.

---

## 🧪 Correr tests

```bash
cd backend
pytest tests/ -v
```

Con reporte de cobertura:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

