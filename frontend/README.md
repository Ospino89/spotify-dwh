# Frontend — Mi Spotify Wrapped

Cliente web del proyecto integrador de Bases de Datos II. SPA construida con React + Vite + TanStack Router que consume el backend FastAPI y presenta los datos del DWH personal de Spotify del usuario autenticado.

> El frontend **nunca llama directamente a la Spotify API**. Todos los datos pasan por el backend, que los obtiene de Spotify o los sirve desde el DWH en Neon.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework | React 18 + Vite (TanStack Start) |
| Lenguaje | TypeScript |
| Enrutamiento | TanStack Router (file-based) |
| Estilos | Tailwind CSS + shadcn/ui |
| HTTP client | `fetch` nativo con wrapper personalizado |
| Autenticación | JWT en `localStorage` (emitido por el backend tras OAuth PKCE) |
| Linting / Formato | ESLint + Prettier |
| Generación inicial | Lovable AI |

---

## Estructura de carpetas

```
frontend/
├── public/
│   └── favicon.svg                     ← ícono de la app
├── src/
│   ├── components/
│   │   └── ui/                         ← componentes shadcn/ui (Button, Card, Badge…)
│   ├── hooks/                          ← custom hooks reutilizables (useProfile, useEtlStatus…)
│   ├── lib/
│   │   ├── api.ts                      ← wrapper fetch con Bearer token automático
│   │   └── auth.ts                     ← helpers: getToken, isTokenExpired, logout
│   └── routes/                         ← enrutamiento file-based con TanStack Router
│       ├── __root.tsx                  ← layout raíz: Outlet + configuración global
│       ├── index.tsx                   ← redirige a /dashboard o /login según sesión
│       ├── login.tsx                   ← página de acceso con botón "Connect with Spotify"
│       ├── callback.tsx                ← recibe JWT de la URL y redirige al dashboard
│       ├── _authenticated.tsx          ← layout protegido: Navbar + guard de sesión
│       ├── _authenticated.dashboard.tsx ← KPIs analíticos con 4 widgets
│       ├── _authenticated.profile.tsx  ← perfil del usuario autenticado
│       └── _authenticated.etl.tsx     ← monitoreo del DWH y ejecución del pipeline
├── .prettierrc                         ← configuración Prettier
├── components.json                     ← configuración shadcn/ui
├── eslint.config.js
├── package.json
├── tsconfig.json
├── vite.config.ts
└── wrangler.jsonc                      ← configuración Cloudflare Workers (deploy opcional)
```

---

## Requisitos previos

- **Node.js** 18 o superior
- **npm** 9 o superior (o **bun** si prefieren el lockfile incluido)
- **Backend corriendo** en `http://localhost:8000` — ver `backend/README.md`
- El backend debe tener las migraciones aplicadas (`alembic upgrade head`) y las variables de entorno configuradas

---

## Instalación

```bash
# 1. Entrar a la carpeta del frontend
cd frontend

# 2. Instalar dependencias
npm install
```

---

## Variables de entorno

Crear un archivo `.env` en la raíz de `frontend/` (nunca versionar este archivo):

```env
VITE_API_URL=http://localhost:8000
```

> El prefijo `VITE_` es obligatorio para que Vite exponga la variable al navegador. Sin esta variable, todos los llamados al backend fallarán.

---

## Correr localmente

```bash
npm run dev
```

La app queda disponible en `http://localhost:8080`.

El backend debe estar corriendo en paralelo en `http://localhost:8000` para que el flujo de autenticación y los datos funcionen.

---

## Páginas

### `/login`

Punto de entrada para usuarios sin sesión activa. Si ya existe un JWT válido en `localStorage`, redirige automáticamente a `/dashboard` sin mostrar esta página.

Contiene únicamente el logo de la app y el botón **"Connect with Spotify"**, que redirige al endpoint `GET /v1/auth/login` del backend — sin formularios ni contraseñas.

---

### `/callback`

Ruta técnica, invisible al usuario. El backend redirige aquí con el JWT como parámetro de URL tras completar el flujo OAuth PKCE.

Acciones que realiza:
1. Lee `?token=<jwt>` de los query params
2. Guarda el JWT en `localStorage` bajo la clave `app_token`
3. Limpia el token de la URL con `history.replaceState`
4. Redirige a `/dashboard`

Muestra solo un spinner mientras procesa. Si no llega token, redirige a `/login`.

---

### `/dashboard`

Vista principal de análisis. Consume cuatro endpoints del backend y los presenta en widgets:

| Widget | Endpoint | Contenido |
|---|---|---|
| **Top 5 Artistas** | `GET /v1/artists/top` | Nombre + barra de popularidad (0–100) |
| **Top 5 Canciones** | `GET /v1/tracks/top` | Nombre + artista + duración en mm:ss |
| **Hora pico** | `GET /v1/history/peak-hour` | Gráfico de barras por hora del día |
| **Géneros dominantes** | `GET /v1/history/genres` | Top géneros con conteo de artistas |

Si el DWH está vacío (primer uso antes de correr el ETL), todos los widgets muestran un **estado vacío** con el mensaje: *"Tu DWH está vacío. Ve a la pestaña ETL y sincroniza tus datos."*

---

### `/profile`

Muestra el perfil del usuario autenticado. Consume `GET /v1/profile/me`.

| Elemento | Dato |
|---|---|
| Avatar circular | Imagen de Spotify, placeholder si no existe |
| Nombre | `display_name` |
| Email | `email` |
| País | Código ISO (ej. `CO`) |
| Tipo de cuenta | Badge **Free** / **Premium** |
| Seguidores | Formateado con separador de miles |
| Enlace externo | "Ver en Spotify" → tab nueva |

---

### `/etl`

Panel de monitoreo del Data Warehouse y ejecución manual del pipeline.

**Bloque A — Estado del DWH** (`GET /v1/etl/status`):
- Tabla con las 4 tablas del DWH, conteo de registros y badge de estado (`empty` / `loaded` / `stale`)
- Historial con las últimas 10 ejecuciones del ETL desde `etl_audit`

**Bloque B — Ejecutar ETL** (`POST /v1/etl/run`):
- Botón **"Sync Now"** que se desactiva con spinner mientras el pipeline corre
- Log terminal paso a paso construido desde el campo `steps` de la respuesta:
  ```
  [ ✅ ] Extract: perfil de usuario obtenido
  [ ✅ ] Extract: 50 artistas obtenidos
  ...
  [ ✅ ] Auditoría registrada — duración: 1.23 s
  ```

---

## Cómo funciona la autenticación

El flujo completo es **OAuth Authorization Code con PKCE**, implementado en el backend. El frontend solo participa al inicio y al final:

```
/login
  └── Clic en "Connect with Spotify"
        └── window.location.href = `${VITE_API_URL}/v1/auth/login`
              └── Backend genera PKCE, redirige a Spotify
                    └── Usuario autoriza en Spotify
                          └── Backend intercambia code → tokens → emite JWT
                                └── 302 redirect a /callback?token=<jwt>

/callback
  └── Lee token de la URL
        └── localStorage.setItem("app_token", token)
              └── Redirige a /dashboard
```

A partir de ese momento, **todas las rutas protegidas** leen el JWT de `localStorage` y lo envían automáticamente en el header `Authorization: Bearer <token>` mediante el wrapper `apiFetch` en `src/lib/api.ts`.

Si el backend retorna `401`, el wrapper elimina el token de `localStorage` y redirige a `/login`.

Para cerrar sesión, el frontend ejecuta `localStorage.removeItem("app_token")` y redirige a `/login`. No hay llamada al backend — el JWT expira naturalmente a las 8 horas.

### Rutas protegidas

El layout `_authenticated.tsx` actúa como guard: verifica que exista un JWT válido antes de renderizar cualquier ruta hija. Si no hay token o está expirado, redirige a `/login`.

```
/dashboard  ┐
/profile    ├── protegidas por _authenticated.tsx
/etl        ┘
```

---

## Diseño y herramientas de IA

| Fase | Herramienta | Uso |
|---|---|---|
| Diseño inicial y generación de código base | **Lovable AI** | Generación de las 5 páginas desde prompt descriptivo |
| Ajustes, refactors y lógica de autenticación | **Claude (Anthropic)** | Revisión de código, correcciones de TypeScript, prompts de mejora |

**Prompt base usado en Lovable AI:**

> *"Design a personal Spotify analytics dashboard web app with dark theme (#0D0D0D background, #1DB954 green accent). 5 pages: Login with single 'Connect with Spotify' button centered; Callback that reads JWT from URL params; Dashboard with top 5 artists (popularity bar), top 5 tracks (mm:ss duration), peak listening hour bar chart, and top genres count; Profile with circular avatar, display name, email, country, Free/Premium badge, followers; ETL page with DWH status table, sync button with terminal step log, and execution history table. Use React + TypeScript + Tailwind CSS + shadcn/ui components. File-based routing with TanStack Router."*

El diseño resultante se ajustó manualmente en VS Code para conectar los endpoints reales del backend, agregar los estados vacíos y corregir los tipos TypeScript de las respuestas.

---

## Diseño visual

El sistema de colores sigue el tema oscuro de Spotify:

| Token | Valor | Uso |
|---|---|---|
| Fondo base | `#0D0D0D` | Background de la app |
| Superficies / Cards | `#1A1A1A` | Contenedores y paneles |
| Acento principal | `#1DB954` | Botones, badges, highlights |
| Texto primario | `#FFFFFF` | Títulos y valores |
| Texto secundario | `#A3A3A3` | Labels y metadatos |