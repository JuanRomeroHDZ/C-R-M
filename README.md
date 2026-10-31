# CRM Local y Sistema de Prospeccion Autonomo

Plataforma local y modular de extraccion de contactos comerciales, auditoria tecnica web, calificacion predictiva (lead scoring) y gestion de embudo de ventas en 12 etapas, disenada para operar en Tijuana, Baja California sobre Debian Linux.

## Requisitos Minimos del Sistema

- Sistema Operativo: Debian Linux 12 (Bookworm) o derivados oficiales.
- Docker Engine: Version 24.0 o superior.
- Docker Compose: Version 2.20 o superior (plugin compose v2).
- Shell: Bash 5.0 o superior.
- Utilidades del host: `iproute2` (`ss`), `lsof`, `curl`.
- Recursos recomendados: 2 CPU cores, 4 GB de memoria RAM, 10 GB de almacenamiento disponible.

## Inicio Rapido

El script de inicio verifica la disponibilidad de puertos en la maquina host, previene colisiones con servicios existentes (como PostgreSQL o Redis locales), genera secretos criptograficos si no existen y despliega los contenedores.

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio> crm
cd crm

# 2. Conceder permisos de ejecucion al script de inicio
chmod +x start.sh

# 3. Iniciar la infraestructura con deteccion dinamica de puertos
./start.sh
```

Al finalizar la ejecucion, el script mostrara la tabla de asignacion de puertos y los enlaces directos de acceso:

- Acceso Local: `http://localhost:<HOST_PORT_PROXY>`
- Acceso LAN (misma red Wi-Fi/Ethernet): `http://<IP_LAN>:<HOST_PORT_PROXY>`
- Documentacion OpenAPI / Swagger: `http://localhost:<HOST_PORT_PROXY>/docs`
- Verificacion de Salud del Sistema: `http://localhost:<HOST_PORT_PROXY>/health`

## Asignacion Dinamica de Puertos

Para evitar conflictos con puertos estandar ya ocupados en el host (como 5432, 6379, 80 o 3000), `start.sh` ejecuta la siguiente logica:

1. Lee los valores definidos en `.env`.
2. Si un puerto no esta definido o si ya se encuentra ocupado por otro proceso del host, asigna aleatoriamente un puerto libre en el rango seguro 20000-45000.
3. Actualiza automaticamente el archivo `.env` con las asignaciones resultantes.
4. Exporta las variables al contexto de ejecucion antes de invocar `docker compose up -d`.

## Estructura del Proyecto

```
CRM/
|-- .env.example              # Plantilla de variables de entorno y puertos
|-- .gitignore                # Reglas de exclusion para Git
|-- docker-compose.yml        # Orquestacion de servicios locales
|-- start.sh                  # Automatizacion de arranque y escaneo de puertos
|-- PROJECT_SPECS.md          # Especificacion tecnica de requerimientos y fases
|-- README.md                 # Documentacion principal del repositorio
|-- memory.md                 # Indice sintetico de rutas para agentes IA
|-- backend/
|   |-- Dockerfile            # Imagen base Python 3.12 Debian para FastAPI
|   |-- requirements.txt      # Dependencias de Python (FastAPI, psycopg, redis, argon2, cryptography)
|   `-- src/
|       |-- main.py           # API principal y endpoints de salud
|       |-- security/         # Blindaje AppSec (Argon2id, AES-256-GCM HKDF, sanitizacion)
|       |-- geo/              # Limites perimetrales, geocodificador dinamico Nominatim y division quadtree
|       |-- extractors/       # Motores de extraccion hibrida OSM Overpass y Google Maps Chromium Headless
|       |-- analysis/         # Deduplicacion, auditoria web, scoring predictivo, evaluador de horarios y generador de pitch
|       |-- pipeline/         # Maquina de estados del pipeline comercial de 12 etapas
|       `-- api/              # Endpoints REST (jobs, leads, pipeline, calendar, geo, metrics, settings, stream, diagnostics)
|-- frontend/
|   |-- Dockerfile            # Servidor Nginx para interfaz estatica responsiva
|   |-- nginx.conf            # Configuracion de entrega de activos web y politicas sin cache
|   `-- src/
|       |-- leaflet/          # Activos locales de Leaflet 1.9.4 autoalojados 100% offline
|       |-- app.js            # Logica de Kanban, modo enfoque, buscador global Ctrl+K, cotizador y atajos
|       |-- index.html        # Vista minimalista Notion/Obsidian con modo enfoque, cotizador y radar local
|       `-- styles.css        # Paleta pastel mate, modo enfoque, tarjetas comerciales y buscador global
`-- proxy/
    |-- Dockerfile            # Servidor perimetral Nginx
    `-- nginx.conf            # Reglas perimetrales, cabeceras de seguridad y limitacion de peticiones
```

## Servicios Orquestados

| Servicio | Contenedor | Imagen Base | Proposito |
| :--- | :--- | :--- | :--- |
| Proxy | `crm_proxy` | `nginx:1.27-alpine` | Enrutamiento perimetral y aislamiento |
| Frontend | `crm_frontend` | `nginx:1.27-alpine` | Interfaz web neutra y responsiva |
| Backend | `crm_backend` | `python:3.12-slim` | API asincrona y tareas concurrentes |
| Base de Datos | `crm_postgres` | `postgres:16-alpine` | Almacenamiento relacional principal |
| Cache / Colas | `crm_redis` | `redis:7-alpine` | Gestion de colas y cache en memoria |

## Variables de Entorno

Copie `.env.example` a `.env` o permita que `./start.sh` lo inicialice de forma automatica:

- `ENVIRONMENT`: Modo de ejecucion (`development` o `production`).
- `HOST_PORT_PROXY`: Puerto en el host asignado al proxy web.
- `HOST_PORT_FRONTEND`: Puerto local en el host para depuracion directa del frontend.
- `HOST_PORT_BACKEND`: Puerto local en el host para el backend FastAPI.
- `HOST_PORT_DB`: Puerto local en el host para PostgreSQL.
- `HOST_PORT_REDIS`: Puerto local en el host para Redis.
- `POSTGRES_DB`: Nombre de la base de datos relacional.
- `POSTGRES_USER`: Usuario administrador de PostgreSQL.
- `POSTGRES_PASSWORD`: Credencial generada para PostgreSQL.
- `APP_SECRET_KEY`: Clave de firma interna de la aplicacion.
- `JWT_SECRET`: Clave de generacion de tokens.

## Verificacion Automatizada E2E (Fase 10)

El proyecto incluye una suite completa de pruebas E2E con Playwright que comprueba multi-resolucion, ciclo de vida del prospecto, prevencion de duplicados y transiciones:

```bash
docker cp test_e2e_fase10.py crm_backend:/test_e2e_fase10.py
docker exec crm_backend python /test_e2e_fase10.py
```

## Reglas de Contribucion

1. Ausencia total de emojis: Queda estrictamente prohibido incluir emojis en codigo fuente, nombres de ramas, mensajes de commit o documentacion Markdown.
2. Formato conciso: Toda documentacion debe ser tecnica, estructurada y sin introducciones redundantes.
3. Compatibilidad de puertos: Ningun servicio debe asumir puertos fijos del host; todos los mapeos deben respetar las variables dinamicas.
4. Revision de dependencias: No versionar directorios `node_modules`, entornos virtuales `.venv`, archivos `.env` o datos locales persistentes.
