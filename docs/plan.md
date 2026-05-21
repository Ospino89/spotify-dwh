# MI SPOTIFY WRAPPED
## Plan de Implementación — 2 Semanas / 2 Personas

Adaptado para 2 desarrolladores con conocimiento básico de backend.

---

## 1. Perfil del Equipo y Premisas

| Desarrollador | Conocimiento Backend | Fortaleza Asignada | Apoyo Necesario |
|---|---|---|---|
| Dev 1 | Básico | Autenticación y configuración inicial (Auth, Setup, DB) | Guía paso a paso para PKCE y Alembic |
| Dev 2 | Básico | ETL pipeline y endpoints de datos (ETL, Routers de datos) | Ejemplos claros de extract/transform/load |

**Premisas del plan:**

- Ambos desarrolladores trabajan en el mismo repositorio git con ramas por feature
- Se reservan 4-5 horas diarias de trabajo efectivo por persona
- Los primeros 2 días son de trabajo conjunto (pair programming) para unificar criterios
- Se usa FastAPI, PostgreSQL Neon, Python 3.11+ y las dependencias del requirements.txt
- La primera ejecución del ETL debe hacerse el Día 3 para acumular datos durante las 2 semanas

---

## 2. Visión General del Plan

| Fase | Días | Foco | Entregable |
|---|---|---|---|
| Fase 0: Setup | Días 1-2 | Configuración compartida del proyecto | Repositorio, .env, DB, estructura de carpetas |
| Fase 1: Fundación | Días 3-5 | Auth, DB schema, migraciones, ETL inicial | Flujo PKCE funcional + primera carga de datos |
| Fase 2: API de Datos | Días 6-9 | Endpoints de datos + ETL completo | Los 8 endpoints funcionando en Postman |
| Fase 3: Tests y Docs | Días 10-12 | Tests unitarios + documentación | pytest sin errores + colección Postman |
| Fase 4: Cierre | Días 13-14 | SQL analítico + reflexión DWH + polish | 5 queries respondidas + entregables completos |

---

## 3. Semana 1 — Fundación y Pipeline

### Día 1 — Setup del Proyecto (Ambos juntos)

**Objetivo:** Tener el repositorio configurado, la DB creada y el servidor corriendo con un endpoint de prueba.

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear proyecto en Neon (spotify-dwh, PostgreSQL 17, US East 1) | Dev 1 | 30 min | Connection String disponible |
| Inicializar repositorio git con estructura de carpetas completa (backend/app/...) | Dev 1 | 45 min | git push con estructura base |
| Crear .env con todas las variables (Spotify, Neon, JWT secret) | Dev 1 | 30 min | .env creado y en .gitignore |
| Registrar app en Spotify Developer Dashboard y obtener client_id/secret | Dev 2 | 30 min | Redirect URI configurada |
| Instalar dependencias del requirements.txt en virtualenv | Dev 2 | 20 min | pip install sin errores |
| Crear main.py con FastAPI + CORS + router /v1 (placeholder) | Dev 2 | 45 min | uvicorn main:app arranca sin errores |
| Crear app/core/config.py con pydantic Settings | Ambos | 45 min | Settings carga .env correctamente |
| Inicializar Alembic y configurar env.py para leer DATABASE_URL | Ambos | 60 min | alembic history funciona |

### Día 2 — Schema de DB y Autenticación Base (Ambos juntos)

**Objetivo:** DDL completo aplicado en Neon via Alembic. Inicio del router de autenticación.

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear migración Alembic con todo el DDL (dwh schema + 5 tablas) | Dev 1 | 90 min | alembic upgrade head sin errores |
| Verificar tablas en Neon (\d dwh.* en psql o dashboard) | Dev 1 | 20 min | 6 tablas visibles en Neon |
| Crear schemas Pydantic: auth.py, profile.py (Base/Request/Response) | Dev 1 | 60 min | Schemas importan sin errores |
| Implementar GET /v1/auth/login — generación PKCE y redirect a Spotify | Dev 2 | 120 min | Redirect a Spotify al llamar el endpoint |
| Crear app/core/spotify_client.py — cliente HTTP reutilizable | Dev 2 | 60 min | Función get con headers Authorization |
| Reunión de sincronización: revisar que la estructura de carpetas sea consistente | Ambos | 30 min | Ambos entienden la estructura completa |

### Día 3 — Auth Callback + ETL Primera Carga

**Objetivo:** Flujo PKCE completo funcional. PRIMERA EJECUCIÓN DEL ETL (crítica para acumular datos).

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Implementar GET /v1/auth/callback — validar state, intercambiar code, emitir JWT | Dev 1 | 150 min | Token JWT recibido en frontend callback URL |
| Implementar dependency get_current_user para protección de rutas | Dev 1 | 60 min | 401 al llamar endpoint sin token |
| Implementar extract_top_artists y extract_top_tracks (Spotify API) | Dev 2 | 90 min | Funciones retornan JSON crudo de Spotify |
| Implementar extract_recently_played con lógica de cursor | Dev 2 | 90 min | Retorna lista de reproducciones |
| **⭐ PRIMERA EJECUCIÓN DEL ETL (sin cursor)** | Ambos | 30 min | 50 filas en fact_listening_history |

> **NOTA CRÍTICA:** La primera ejecución del ETL debe hacerse HOY (Día 3). Cada día sin ETL es historial de reproducciones perdido permanentemente. A partir de hoy, ejecutar el ETL al menos 1 vez al día.

### Día 4 — Transform, Load y Audit del ETL

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Implementar transform_top_artists y transform_top_tracks | Dev 2 | 90 min | Datos normalizados (spotify_id, name, genres, etc.) |
| Implementar load_dim_artists y load_dim_tracks con ON CONFLICT DO NOTHING | Dev 2 | 90 min | INSERT idempotente verificado |
| Implementar transform_recently_played (parsed played_at, hour_of_day, day_of_week, context_type) | Dev 2 | 90 min | played_at como TIMESTAMP, hour y day derivados |
| Implementar load_fact_listening_history con ON CONFLICT (user_id, played_at) DO NOTHING | Dev 2 | 60 min | Segunda ejecución no duplica registros |
| Implementar audit trail (insert_audit_start, update_audit_success, update_audit_error) | Dev 1 | 90 min | etl_audit tiene fila por cada ejecución |
| Implementar run_etl orquestador en etl_service.py | Dev 1 | 90 min | POST /v1/etl/run ejecuta pipeline completo |

### Día 5 — Endpoints de Datos y Schemas Restantes

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Implementar GET /v1/profile/me — perfil del usuario desde dim_users | Dev 1 | 90 min | 200 con datos del usuario + 401 sin token |
| Crear schemas: artists.py, tracks.py, history.py (Base/Request/Response) | Dev 1 | 60 min | Schemas importan sin errores |
| Implementar GET /v1/artists/top — consulta dim_artists | Dev 2 | 90 min | 200 con lista de artistas + 401 sin token |
| Implementar GET /v1/tracks/top — consulta dim_tracks | Dev 2 | 90 min | 200 con lista de tracks + 401 sin token |
| Implementar GET /v1/history/recently-played — consulta fact_listening_history | Dev 2 | 90 min | 200 con historial + 401 sin token |
| Implementar GET /v1/etl/status — últimas 20 ejecuciones de etl_audit | Dev 1 | 60 min | 200 con lista de ejecuciones |
| Prueba end-to-end en Postman: flujo completo login→callback→endpoints | Ambos | 60 min | Los 8 endpoints responden correctamente |

---

## 4. Semana 2 — Tests, Documentación y Entregables

### Día 6 — Tests: conftest, auth y profile

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear backend/tests/ con __init__.py y conftest.py (fixtures: app, client, mock token) | Dev 1 | 90 min | conftest.py importa sin errores |
| Crear test_auth.py: test_login_redirects, test_callback_returns_jwt, test_callback_invalid_state_401 | Dev 1 | 120 min | pytest test_auth.py -v: 3 PASSED |
| Crear test_profile.py: test_get_profile_200, test_get_profile_no_token_401, test_get_profile_invalid_token_401 | Dev 2 | 120 min | pytest test_profile.py -v: 3 PASSED |
| Agregar docstrings completos a auth.py y profile.py (routers y services) | Dev 2 | 90 min | Revisión manual: todos los métodos documentados |

### Día 7 — Tests: artists y tracks

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear test_artists.py: test_get_top_artists_200, test_no_token_401, test_invalid_token_401, test_empty_returns_200 | Dev 1 | 120 min | pytest test_artists.py -v: 4 PASSED |
| Crear test_tracks.py: test_get_top_tracks_200, test_no_token_401, test_invalid_token_401, test_empty_returns_200 | Dev 1 | 120 min | pytest test_tracks.py -v: 4 PASSED |
| Agregar docstrings a artists.py y tracks.py (routers y services) | Dev 2 | 60 min | Revisión manual OK |
| Agregar docstrings de archivo (Regla 4) a todos los .py aún sin ellos | Dev 2 | 120 min | Todos los .py tienen docstring de archivo |

### Día 8 — Tests: history y ETL + cobertura

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear test_history.py: test_recently_played_200, test_no_token_401, test_invalid_token_401, test_empty_history_200 | Dev 1 | 120 min | pytest test_history.py -v: 4 PASSED |
| pytest backend/tests/ -v — verificar que TODOS los tests pasan sin errores | Dev 1 | 30 min | 0 failed, 0 errors |
| pytest backend/tests/ --cov=backend/app --cov-report=term-missing | Dev 2 | 30 min | Cobertura visible por módulo |
| Identificar y corregir gaps de cobertura críticos (< 70%) | Dev 2 | 90 min | Cobertura mínima 70% en módulos críticos |
| Agregar tests adicionales según gaps identificados | Ambos | 120 min | pytest final: 0 errores |

### Día 9 — Colección Postman y Diagrama Excalidraw

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear colección Postman 'Spotify DWH API' con 4 carpetas y 8 requests | Dev 1 | 120 min | Todos los endpoints responden en Postman |
| Agregar variables de entorno Postman (base_url, token) y script auto-token | Dev 1 | 45 min | Token se llena automáticamente en POST /token |
| Exportar colección como backend/docs/spotify-dwh.postman_collection.json | Dev 1 | 15 min | Archivo JSON versionado en git |
| Generar diagrama Excalidraw del star schema con Claude Code + MCP | Dev 2 | 90 min | backend/docs/dwh-diagram.excalidraw creado |
| Verificar diagrama muestra: dim_users, dim_artists, dim_tracks, fact_listening_history con PKs y FKs | Dev 2 | 30 min | Diagrama abierto en excalidraw.com correctamente |

### Día 10 — SQL Analítico (Preguntas 1 a 3)

> Para este día deben existir al menos 7 días de datos en fact_listening_history (ejecutando ETL desde el Día 3).

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Ejecutar ETL diario matutino (hábito desde Día 3) | Ambos | 10 min | Nueva fila en etl_audit con status='success' |
| Responder Pregunta 1: hora del día con más reproducciones (GROUP BY hour_of_day) | Dev 1 | 45 min | Query ejecuta y retorna resultados con datos reales |
| Responder Pregunta 2: artista más escuchado (JOIN fact+dim_artists, LIMIT 5) | Dev 1 | 45 min | Query ejecuta y retorna top 5 artistas |
| Responder Pregunta 3: popularidad promedio de top tracks (AVG/MIN/MAX) | Dev 2 | 45 min | Query retorna 3 valores numéricos |
| Documentar resultados de preguntas 1-3 en backend/docs/dwh-reflection.md | Ambos | 60 min | Resultados + capturas de pantalla en Markdown |
| Iniciar respuestas de reflexión DWH (Pregunta 1: star vs snowflake) | Dev 1 | 60 min | Borrador redactado |

### Día 11 — SQL Analítico (Preguntas 4 y 5) + Reflexión DWH

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Responder Pregunta 4: géneros dominantes (UNNEST + GROUP BY) | Dev 2 | 60 min | Query usa UNNEST(genres) correctamente |
| Responder Pregunta 5: ranking por día de semana (RANK() OVER PARTITION BY) | Dev 2 | 90 min | Query usa window function RANK() OVER correctamente |
| Documentar resultados de preguntas 4-5 en dwh-reflection.md | Dev 2 | 60 min | Las 5 preguntas con resultados en el documento |
| Responder reflexión DWH Pregunta 2: genres TEXT[] vs tabla dim_genres | Dev 1 | 60 min | Respuesta justifica decisión y menciona snowflake |
| Responder reflexión DWH Pregunta 3: granularidad de fact_listening_history | Dev 1 | 60 min | Respuesta explica grain y por qué played_at no puede ser PK sola |

### Día 12 — README y Revisión Final de Código

| Tarea | Quién | Duración est. | Criterio de completitud |
|---|---|---|---|
| Crear README.md con: setup, configuración .env, migraciones Alembic, cómo correr la API, cómo ejecutar tests | Dev 1 | 120 min | Otro desarrollador puede seguir el README desde cero |
| Revisión de código: verificar que TODOS los archivos .py tienen docstring de archivo (Regla 4) | Dev 2 | 90 min | 100% de archivos .py con docstring de archivo |
| Revisión de código: verificar que TODAS las funciones tienen docstring con Args/Returns (Regla 3) | Dev 2 | 90 min | 0 funciones sin docstring en services/ y routers/ |
| Verificar .gitignore incluye .env y carpeta __pycache__ | Dev 1 | 15 min | git status no muestra .env |
| pytest backend/tests/ -v — última corrida completa | Ambos | 20 min | 0 failed, 0 errors |

### Día 13 — Buffer y Ajustes

Día de buffer para resolver deuda técnica, bugs encontrados en la revisión o tareas que tomaron más tiempo del estimado.

| Actividad | Prioridad | Notas |
|---|---|---|
| Corregir tests que fallen o estuvieran incompletos | Alta | Ejecutar pytest -v y revisar cada falla |
| Completar docstrings faltantes | Alta | Revisión manual archivo por archivo |
| Mejorar cobertura de tests si está por debajo del 70% | Media | Agregar tests para servicios sin cobertura |
| Optimizar queries SQL si alguna es lenta | Baja | Agregar índices si fact_listening_history > 500 filas |
| Revisar y mejorar README | Media | Pedir a alguien externo que intente seguirlo |

### Día 14 — Entrega Final

| Checklist de entrega | Responsable | Estado |
|---|---|---|
| DDL + migraciones Alembic aplicadas en Neon | Dev 1 | [ ] Pendiente |
| ETL funcional: POST /v1/etl/run ejecuta las 3 fases | Dev 2 | [ ] Pendiente |
| 8 endpoints respondiendo en Postman (200 con token, 401 sin token) | Ambos | [ ] Pendiente |
| pytest backend/tests/ -v: 0 failed | Ambos | [ ] Pendiente |
| Colección Postman exportada en backend/docs/ | Dev 1 | [ ] Pendiente |
| Diagrama Excalidraw en backend/docs/dwh-diagram.excalidraw | Dev 2 | [ ] Pendiente |
| 5 preguntas SQL respondidas con datos reales en dwh-reflection.md | Ambos | [ ] Pendiente |
| 3 preguntas de reflexión DWH respondidas en dwh-reflection.md | Ambos | [ ] Pendiente |
| README.md completo en la raíz del proyecto | Dev 1 | [ ] Pendiente |
| .env en .gitignore (no versionado) | Ambos | [ ] Pendiente |
| Todos los .py con docstring de archivo y funciones documentadas | Ambos | [ ] Pendiente |
| ETL diario ejecutado durante al menos 10 días consecutivos | Ambos | [ ] Pendiente |

---

## 5. Tabla Resumen: Distribución de Carga por Desarrollador

| Componente | Dev 1 (horas est.) | Dev 2 (horas est.) | Total |
|---|---|---|---|
| Setup inicial (Neon, git, .env, Spotify) | 3h | 2h | 5h |
| Schema DB + Migraciones Alembic | 4h | 1h | 5h |
| Autenticación PKCE + JWT (auth.py) | 6h | 1h | 7h |
| spotify_client.py + config.py | 1h | 2h | 3h |
| ETL extract_* (3 funciones) | 1h | 5h | 6h |
| ETL transform_* (3 funciones) | 1h | 6h | 7h |
| ETL load_* + ON CONFLICT (3 funciones) | 2h | 5h | 7h |
| ETL audit trail + run_etl orquestador | 4h | 1h | 5h |
| Endpoints de datos (profile, artists, tracks, history, etl/status) | 3h | 6h | 9h |
| Schemas Pydantic (todos los módulos) | 4h | 2h | 6h |
| Tests unitarios (conftest + 5 archivos) | 6h | 4h | 10h |
| Documentación (README, docstrings, reflexión DWH) | 4h | 3h | 7h |
| Colección Postman | 3h | 0h | 3h |
| Diagrama Excalidraw | 0h | 2h | 2h |
| SQL analítico (5 preguntas) | 3h | 3h | 6h |
| Buffer y ajustes | 4h | 4h | 8h |
| **TOTAL ESTIMADO** | **49h** | **47h** | **96h** |

---

## 6. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| La configuración de Alembic (env.py + DATABASE_URL) bloquea el Día 1 | Alta | Alto | Usar el snippet de env.py documentado en el análisis de reglas. Reservar 2h extra el Día 1 para esto. |
| El flujo PKCE es complejo para nivel básico (code_verifier, state, redirect) | Alta | Alto | Pair programming en Día 2-3. Dev 1 lidera auth, Dev 2 hace preguntas. Usar la sección del flujo de 6 pasos como checklist. |
| La primera ejecución del ETL se retrasa más allá del Día 3 | Media | Alto | Ejecutar ETL parcial (solo extract_recently_played sin load completo) el Día 3 para asegurar que el historial no se pierda. |
| Los tests fallan porque mockean en el nivel equivocado | Media | Medio | Usar el ejemplo de test_artists.py del documento como plantilla. Mockear siempre en services/, no en routers/. |
| La API de Spotify retorna errores de rate limit durante el desarrollo | Baja | Medio | Usar los MOCK_ARTISTS y MOCK_TRACKS de los tests como datos de prueba. No llamar a Spotify en cada iteración de desarrollo. |
| El tiempo disponible se reduce por obligaciones externas | Media | Medio | El Día 13 es buffer. Priorizar: ETL funcional + tests > SQL analítico > documentación extra. |

---

## 7. Notas para Desarrolladores con Nivel Básico de Backend

### 7.1 Sobre Pydantic y los Schemas

- Pydantic valida automáticamente los tipos. Si el endpoint recibe un campo incorrecto, FastAPI retorna 422 automáticamente.
- `model_config = ConfigDict(from_attributes=True)` en Response le dice a Pydantic que puede leer desde un objeto ORM (no solo desde un dict).
- Si el Request no agrega campos nuevos al Base, simplemente hereda con `pass`. No hay problema en eso.

### 7.2 Sobre JWT y la Autenticación

- El JWT de la app es **INDEPENDIENTE** del access_token de Spotify. Son dos tokens distintos con propósitos distintos.
- El JWT de la app expira en 8 horas. El access_token de Spotify expira en 1 hora pero se renueva con refresh_token.
- Si se recibe 401, verificar primero: ¿existe el header Authorization? ¿El token empieza con `Bearer `? ¿El token no expiró?

### 7.3 Sobre el ETL y la Carga Incremental

- `ON CONFLICT DO NOTHING` es la clave de la idempotencia: ejecutar el ETL 2 veces no duplica datos.
- El cursor Unix ms en etl_audit es como un marcador de página: dice "la próxima vez empieza desde aquí".
- Si algo falla en el ETL, la fila de etl_audit queda con `status='error'`. Esto es intencional para auditar fallos.

### 7.4 Sobre pytest y los Mocks

- `patch('app.v1.services.artists_service.extract_top_artists')` reemplaza la función real por una falsa durante el test. La ruta debe ser donde la función **SE USA**, no donde **SE DEFINE**.
- `TestClient(app)` simula hacer requests HTTP sin levantar un servidor real. Es más rápido y no necesita conexión de red.
- `conftest.py` con fixtures compartidos evita repetir el `client = TestClient(app)` en cada archivo de test.