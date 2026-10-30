# Indice de Rutas y Memoria de Arquitectura

Documento de referencia para navegacion e indexacion por agentes de inteligencia artificial.

## Rutas y Componentes del Repositorio

- `CRM/`: Directorio raiz del repositorio que alberga la infraestructura en contenedores, automatizaciones de despliegue, codigo de aplicacion y especificaciones del sistema.
- `.env.example`: Plantilla de variables de entorno con nombres obligatorios y valores ficticios para puertos dinamicos, credenciales de PostgreSQL y claves criptograficas.
- `.gitignore`: Reglas de exclusion de Git para proteger credenciales locales en .env, artefactos temporales, registros de depuracion y datos de ejecucion.
- `docker-compose.yml`: Orquestacion multicontenedor con PostgreSQL, Redis, Backend, Frontend y Proxy sobre red puente aislada con volumenes de datos persistentes.
- `start.sh`: Script en Bash que escanea puertos ocupados en host, asigna dinamicamente puertos libres y despliega los contenedores sin colisiones.
- `PROJECT_SPECS.md`: Especificacion tecnica global con alcance en Tijuana, pipeline de 12 etapas, motor de scoring y resumen de las seis fases.
- `README.md`: Documentacion tecnica para GitHub con requisitos del sistema, guia de arranque con start.sh, arbol de directorios y reglas de contribucion.
- `memory.md`: Indice conciso de rutas y responsabilidades para agentes de inteligencia artificial, limitado a menos de treinta palabras por entrada.
- `backend/`: Directorio del servicio backend orientado a alta concurrencia, APIs asincronas con FastAPI y futuros motores de scraping geolocalizado.
- `backend/Dockerfile`: Definicion de contenedor Docker basado en Python 3.12 Debian Bookworm para ejecutar la aplicacion backend de forma aislada.
- `backend/requirements.txt`: Lista de dependencias de Python para FastAPI, servidor Uvicorn, controladores asincronos de PostgreSQL, Redis y cliente HTTP.
- `backend/src/`: Codigo fuente del backend que encapsula la logica de negocio, controladores de API y modulos de integracion.
- `backend/src/main.py`: Punto de entrada FastAPI con ciclo de vida lifespan, routers de categorias, trabajos y prospectos, y endpoints de salud.
- `backend/src/config.py`: Gestor central de configuraciones y variables de entorno para conexiones a PostgreSQL, Redis, limites de concurrencia y parametros del scraper.
- `backend/src/db/connection.py`: Proveedor de conexiones seguras y transaccionales hacia PostgreSQL mediante cursores basados en diccionarios para consultas parametrizadas.
- `backend/src/db/schema.py`: Migraciones DDL para tablas de categorias, palabras clave, etiquetas OSM, trabajos de extraccion, cuadriculas y prospectos, incluyendo semillas iniciales.
- `backend/src/models/schemas.py`: Esquemas Pydantic para validacion y serializacion de categorias, trabajos de extraccion, telemetria en tiempo real y prospectos capturados.
- `backend/src/geo/bounds.py`: Delimitacion perimetral de Tijuana y definicion de coordenadas limite para macro-zonas estrategicas como Zona Rio, Centro y Otay.
- `backend/src/geo/quadtree.py`: Algoritmo de subdivision adaptativa de cuadriculas espaciales en cuatro sub-cuadrantes al detectar saturacion comercial en celdas.
- `backend/src/extractors/osm_engine.py`: Sub-motor de extraccion para OpenStreetMap con generador Overpass QL, rotacion de servidores espejo y analisis de etiquetas comerciales.
- `backend/src/extractors/gmaps_engine.py`: Sub-motor de extraccion profunda para Google Maps con Playwright headless, intercepcion de recursos pesados y cortacircuitos de seguridad.
- `backend/src/queue/redis_queue.py`: Gestor de colas en Redis que controla la maquina de estados de trabajos, encolamiento de celdas y pausas en caliente.
- `backend/src/queue/worker.py`: Trabajador en segundo plano que procesa celdas geograficas, ejecuta extraccion hibrida, particion adaptativa y persistencia con manejo de conflictos.
- `backend/src/api/categories.py`: Endpoints REST para operaciones CRUD sobre categorias comerciales, bancos de sinonimos y mapeos de etiquetas OpenStreetMap.
- `backend/src/api/jobs.py`: Endpoints para crear barridos geograficos, pausar, reanudar o cancelar trabajos de extraccion y consultar telemetria en tiempo real.
- `backend/src/api/leads.py`: Endpoints para consultar y filtrar prospectos capturados con soporte de paginacion, filtros por categoria y exclusion de borrado logico.
- `backend/src/verify_extraction.py`: Rutina de verificacion ejecutable para comprobar la extraccion real de prospectos en Zona Rio sin emplear datos simulados.
- `frontend/`: Directorio del servicio web cliente con interfaz responsiva, ligera y estetica minimalista en escala de grises.
- `frontend/Dockerfile`: Imagen ligera Nginx Alpine encargada de servir los archivos estaticos del frontend con comprobacion de salud integrada.
- `frontend/nginx.conf`: Configuracion del servidor Nginx local para entregar la aplicacion web estatica con politicas basicas de cache.
- `frontend/src/`: Codigo fuente del frontend compuesto por estructura HTML, estilos monocromaticos y logica JavaScript del cliente.
- `frontend/src/index.html`: Estructura HTML responsiva con diseno minimalista neutro en escala de grises para el panel de estado.
- `frontend/src/styles.css`: Hojas de estilo CSS inspiradas en Notion y Obsidian con paleta monocromatica y componentes visuales adaptativos.
- `frontend/src/app.js`: Script del cliente para consultar periodicamente la API y mostrar el estado de conexion de los servicios.
- `proxy/`: Directorio del proxy perimetral de enrutamiento inverso y aislamiento de seguridad de la red interna de contenedores.
- `proxy/Dockerfile`: Contenedor Nginx Alpine optimizado para gestionar el trafico perimetral y transferir solicitudes entre el host y servicios.
- `proxy/nginx.conf`: Reglas de enrutamiento que redirigen /api y /health al backend y el trafico raiz al frontend.
