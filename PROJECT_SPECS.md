# Especificaciones del Proyecto: CRM Local y Motor de Prospeccion

## 1. Alcance General y Requerimientos del Sistema

### 1.1 Proposito y Filosofia
Plataforma local y autonoma disenada para extraer, auditar, calificar y gestionar contactos comerciales a partir de Google Maps y OpenStreetMap sin costos asociados a licencias o APIs de pago.

El sistema prioriza la soberania de datos, ejecutandose integramente dentro del hardware del usuario bajo un esquema Zero-Config que permite operatividad funcional desde el primer despliegue sin configuraciones iniciales complejas.

### 1.2 Cobertura Geografica y Segmentacion Territorial
- Region operativa inicial: Tijuana, Baja California, Mexico.
- Estrategia de particion: Division cartografica por cuadriculas adaptativas basadas en densidad demografica y comercial.
- Fuentes cartograficas: Integracion nativa con nodos de OpenStreetMap (Overpass API / Nominatim) y scraping perimetral optimizado sobre Google Maps.

### 1.3 Gestion de Categorias y Sinonimia
- Arquitectura multisectorial para catalogar rubros comerciales.
- Bancos de sinonimos y palabras clave configurables para desambiguar busquedas.
- Casos piloto de validacion: "dentistas" y "despachos contables".

### 1.4 Auditoria Tecnica Web y Lead Scoring
- Evaluacion automatizada en segundo plano de dominios detectados:
  - Validez y vigencia de certificados SSL/TLS.
  - Tiempos de respuesta y rendimiento base.
  - Compatibilidad de viewport movil (meta viewport y responsividad).
  - Deteccion de pixeles de rastreo y plataformas analiticas (Meta Pixel, Google Tag Manager).
- Algoritmo de Lead Scoring: Calculo determinista del porcentaje de exito de cierre (0 a 100%) ponderando madurez digital y canales de atencion.

### 1.5 Acciones de Contacto Directo
- Generador de enlaces universales para WhatsApp (`wa.me`) con texto inicial parametrizado y editable por el usuario, sin disparo automatico de envios.
- Deteccion y enlace directo a perfiles en redes sociales (Facebook, Instagram, LinkedIn).
- Generador de enlaces `tel:` para marcacion telefonica tradicional en dispositivos moviles.

### 1.6 Pipeline de Ventas Extendido (12 Etapas)
1. Extraido: Contacto recopilado en base de datos sin procesamiento adicional.
2. Auditado: Auditoria tecnica del sitio web completada.
3. Calificado: Puntuacion de Lead Scoring asignada.
4. Primer Contacto: Mensaje o llamada inicial emitida.
5. Respuesta Recibida: Interaccion bidireccional confirmada por el prospecto.
6. En Conversacion: Dialogo activo para identificacion de requerimientos.
7. Demostracion / Propuesta: Presentacion tecnica o comercial enviada.
8. En Negociacion: Discusion de terminos, presupuesto o acuerdos.
9. En Espera / Postergado: Proceso pausado a peticion del prospecto con fecha de reanudacion.
10. Arrepentimiento / Retractado: Cancelacion posterior al interes inicial (motivo obligatorio).
11. Cerrado - Ganado: Venta o contratacion concretada.
12. Cerrado - Descartado: Prospecto inviable o no interesado (motivo obligatorio).

### 1.7 Integridad, Deduplicacion y Persistencia
- Normalizacion telefonica estricta bajo formato internacional E.164.
- Normalizacion de dominios raiz eliminando protocolos, subdominios redundantes y rutas.
- Evaluacion de similitud léxica mediante distancia de Levenshtein y proximidad geoespacial.
- Deteccion visual de duplicados sospechosos (similitud entre 65% y 84%) con modal de comparacion lado a lado y lista blanca de exclusion.

### 1.8 Visor Web Integrado y Arquitectura Ultra-Compacta (Fase 9)
- Visor web enmarcado sin abandono de aplicacion mediante proxy inverso en segundo plano (`GET /api/v1/preview/proxy`).
- Sanitizacion de cabeceras bloqueadoras de embebido (`X-Frame-Options`, `Content-Security-Policy`), neutralizacion de framebusting scripts (`top.location`) e inyeccion de `<base href="...">`.
- Aislamiento en iframe sandbox estricto (`sandbox="allow-scripts allow-same-origin allow-forms"`).
- Conmutador de dispositivo movil (375px) vs escritorio completo (100%).
- Bloc de notas rapido integrado para captura comercial sin salir del visor web.
- Botonera ultra-compacta de solo iconos con areas tactiles optimizadas (>=36px escritorio, >=42px movil) y tooltips flotantes.
- Popovers informativos `(i)` para eliminar parrafos densos de explicacion.
- Barra flotante inferior de acciones en lote (cambio de fase, etiquetas, exportacion CSV y papelera).
- Historial persistente de busquedas recientes con re-ejecucion en 1 clic.
- 3 Herramientas de Productividad Creativa:
  1. Pastilla flotante con diagnostico visual de fallas tecnicas en tiempo real dentro del visor.
  2. Selector rapido de angulo de contacto para WhatsApp por falla detectada (SSL, movil, Google Maps, general).
  3. Barra de filtros rapidos solo-iconos (WhatsApp, telefono, sitio web, duplicados).
- Borrado logico (soft delete) mediante columnas de marcado temporal (`deleted_at`).
- Dialogos de doble confirmacion para toda accion irreversible.

### 1.8 Red Local, Aislamiento y Calendario
- Operacion en red local (LAN / Wi-Fi) compatible con entornos bajo doble NAT.
- Calendario interno con soporte de eventos y tareas.
- Modulo opcional de sincronizacion con Google Calendar mediante integracion OAuth local.

### 1.9 Directrices de Diseno Visual
- Estetica minimalista neutra inspirada en Notion y Obsidian.
- Paleta en escala de grises con fondos oscuros neutros (`#191919`, `#202020`), bordes sutiles y tipografia legible.
- Color reservado exclusivamente para indicadores de estado funcionales (verde, ambar, rojo).
- Empleo estricto de iconos vectoriales SVG estandar. Prohibicion absoluta de emojis en toda la interfaz, codigo y documentacion.
- Diseno completamente adaptativo para dispositivos moviles, tabletas y monitores de escritorio.

---

## 2. Fases de Desarrollo del Proyecto

### Fase 1: Infraestructura Base, Orquestacion y Gestion de Puertos
- Despliegue con Docker Compose de los cinco servicios estructurales:
  - Base de datos relacional (PostgreSQL 16).
  - Capa de colas y cache en memoria (Redis 7).
  - Backend asincrono para alta concurrencia (FastAPI / Python 3.12).
  - Frontend responsivo (Nginx / Web).
  - Proxy perimetral y enrutamiento interno (Nginx).
- Script de automatizacion (`start.sh`) con comprobacion de puertos en host y asignacion dinamica para prevenir colisiones.
- Centralizacion segura de credenciales en `.env`, plantilla limpia `.env.example` y exclusion en `.gitignore`.
- Documentacion tecnica del repositorio (`README.md`, `PROJECT_SPECS.md`, `memory.md`).

### Fase 2: Motor de Extraccion Geolocalizado en Tijuana
- Extraccion perimetral con OpenStreetMap mediante consultas Overpass y geocodificacion con Nominatim.
- Motor de scraping asincrono sobre Google Maps optimizado para entornos residenciales (respeto de retardos humanos, emulacion de navegadores reales y mitigacion de bloqueos).
- Division de la mancha urbana de Tijuana en cuadriculas adaptativas.
- Motor de sinónimos y taxonomias sectoriales.

### Fase 3: Auditoria Tecnica Web, Scoring y Deduplicacion
- Modulo de auditoria tecnica de sitios web (certificados SSL, latencia, metadatos moviles, pixeles).
- Motor de evaluacion algoritmica de probabilidad de cierre (0 a 100%).
- Mecanismo de deduplicacion multicapa (telefono E.164, dominio base y similitud fonetica/geografica).

### Fase 4: Enriquecimiento de Perfiles, Redirecciones y Calendario
- Generador de plantillas personalizadas de redireccion a WhatsApp (`wa.me`).
- Deteccion de redes sociales y enlaces telefonicos.
- Modulo de agenda y calendario local con soporte para sincronizacion con Google Calendar.

### Fase 5: Pipeline Comercial de 12 Etapas y Persistencia
- Maquina de estados formal para la gestion del embudo de ventas.
- Reglas de transicion y captura obligatoria de motivos en etapas de arrepentimiento y descarte.
- Persistencia integral con borrado logico y auditoria de cambios.

### Fase 6: Seguridad AppSec, Mapa Interactivo, Ajustes Modulares y Metricas (Completada)
- Endurecimiento estricto de seguridad: Argon2id para PIN de operador en red local y AES-256-GCM derivado con HKDF-SHA256 para tokens OAuth en reposo.
- Blindaje contra inyecciones XSS y HTML mediante sanitizacion estricta y limitacion de tasa de peticiones con cabeceras de seguridad perimetrales.
- Mapa interactivo de Tijuana autoalojado con Leaflet 1.9.4 offline, capas de poligonos por delegaciones, marcadores de prospectos por calificacion y monitor de barrido en tiempo real.
- Panel de Ajustes Modular Avanzado con 8 modulos independientes: Operador, Categorias y Palabras Negativas, Motor Scraper, Calibracion de Scoring con Recalculo Masivo, Plantillas WhatsApp con Toggles de Canales, Reglas de Pipeline, Calendario/Gmail y Respaldos/Mantenimiento.
- Panel de Metricas Comerciales con embudo visual de 12 fases, porcentaje de retencion, post-mortem de objeciones y distribucion por rubro y delegacion.
- Recorrido guiado nativo Spotlight Onboarding de 6 pasos con persistencia local y en base de datos.

### Fase 7: Erradicacion de Mock Data, Integracion Reactiva y Chromium Headless (Completada)
- Politica estricta de Cero Datos Falsos (Zero Mock Policy): purga absoluta de semillas artificiales o ficticias; la interfaz opera exclusivamente con prospectos comerciales reales extraidos de internet.
- Automatizacion de Chromium Headless en contenedor Docker con memoria compartida shm_size 2GB y aislamiento en memoria para ejecucion sin fallos de Playwright.
- Geocodificador dinamico acoplado a Nominatim de OpenStreetMap con cache de persistencia en Redis de 30 dias para resolucion de coordenadas y poligonos de cualquier ciudad o delegacion.
- Motor de busqueda libre y flexible para cualquier giro o categoria comercial con auto-aprovisionamiento y registro dinamico en base de datos.
- Encadenamiento continuo de extremo a extremo: Extraccion -> Deduplicacion -> Auditoria tecnica de sitios web -> Enriquecimiento multicanal -> Calculo predictivo de aceptacion -> Calificacion automatica en etapa QUALIFIED.
- Transmision reactiva en tiempo real mediante Server-Sent Events (SSE) a traves de endpoint /api/v1/stream/events conectado al frontend para insercion en vivo de prospectos y telemetria sin sondeo.
- Panel de autodiagnostico integral (/api/v1/diagnostics/health-check) que verifica en tiempo real la salud y latencia de PostgreSQL, Redis, Chromium Headless, Nominatim, Overpass API y Google Maps.

### Fase 8: Humanizacion Comercial Total, Herramientas de Velocidad y Productividad (Completada)
- Erradicacion total de jerga tecnica en pantallas, etiquetas, modales y notificaciones (sustitucion por lenguaje comercial claro y natural).
- Herramienta de Velocidad 1 (Modo Enfoque / Rafaga de Contacto): Vista de prospeccion secuencial un prospecto a la vez ordenado por calificacion con avance inmediato en menos de un segundo en acciones rapidas.
- Herramienta de Velocidad 2 (Generador de Diagnostico Comercial Copiable en 1 Clic): Resumenes comerciales listos para ventas sin tecnicismos generados a partir de fallas reales detectadas.
- Herramienta de Velocidad 3 (Indicador de Abierto Ahora y Filtro por Horario): Evaluacion en vivo del estado de apertura comercial en horario local de Tijuana con filtro dedicado.
- Herramienta de Velocidad 4 (Buscador Global Rapido Ctrl+K y Etiquetas): Modal de busqueda instantanea multicampo y gestion de etiquetas comerciales personalizadas.
- Herramienta Creativa 1 (Cotizador Express y Calculadora de Propuesta): Seleccion de paquetes de servicios en pesos mexicanos, guardado en base de datos y copia de propuesta formateada.
- Herramienta Creativa 2 (Radar de Competencia Local): Comparativa contextual con negocios del mismo rubro en la zona para argumento de negociacion comercial.
- Herramienta Creativa 3 (Atajos de Teclado Comerciales con una Sola Mano): Navegacion rapida con teclas J/K, WhatsApp con W, copia con C, notas con N y busqueda con Ctrl+K.
- Paleta visual Notion/Obsidian en tonos pastel mate apagados (salvia, pizarra, arena y terracota) con bordes de 6 a 10 pixeles y cero destellos o neones.

---

## 3. Arquitectura Tecnica de Infraestructura (Fase 1)

```
[ Dispositivos en LAN / Wi-Fi ]  -->  [ HOST: HOST_PORT_PROXY ]
                                                |
                                      +--------------------+
                                      | crm_proxy (Nginx)  |
                                      +--------------------+
                                                |  (crm_network)
                   +----------------------------+----------------------------+
                   |                                                         |
         +--------------------+                                    +--------------------+
         | crm_frontend       |                                    | crm_backend        |
         | (Nginx Static)     |                                    | (FastAPI Core)     |
         +--------------------+                                    +--------------------+
                                                                             |
                                                 +---------------------------+---------------------------+
                                                 |                                                       |
                                       +--------------------+                                  +--------------------+
                                       | crm_postgres       |                                  | crm_redis          |
                                       | (PostgreSQL 16)    |                                  | (Redis 7)          |
                                       +--------------------+                                  +--------------------+
                                                 |                                                       |
                                       [ crm_postgres_data ]                                   [ crm_redis_data ]
```

### 3.1 Aislamiento de Red
- Red interna: `crm_network` (bridge privado).
- Acceso externo: Unicamente el proxy expone puerto en `0.0.0.0` para recibir conexiones de la red local.
- Los puertos de base de datos, colas, backend y frontend se vinculan a la interfaz local `127.0.0.1` del host para labores de desarrollo y diagnostico, impidiendo exposicion directa no autenticada en la red local.

### 3.2 Persistencia de Datos
- `crm_postgres_data`: Almacena tablas de contactos, transiciones de estados, auditorias y configuraciones.
- `crm_redis_data`: Almacena colas de scraping, cache de auditorias web y estados efimeros.

---

## 4. Fase 10 Extendida: Auditoria, Reparacion Quirurgica y Suite de Productividad

### 4.1 Ciclo de Vida y Edicion Permanente
- Creacion manual con validacion inteligente (Nombre + Telefono o Sitio Web) y resolucion de colisiones mediante banner interactivo con boton "Abrir Ficha Existente".
- Edicion en vivo dentro del Drawer para los 7 campos criticos y canales de redes sociales persistida en PostgreSQL sin recarga.
- Re-evaluacion tecnica web en vivo mediante boton solo-icono con actualizacion reactiva de puntajes y argumentos comerciales.

### 4.2 Suite de Velocidad Comercial y Bandeja "Para Hoy"
- Bandeja diaria que consolida citas de agenda, reactivaciones vencidas de prospectos pospuestos y prospectos estancados (>48 horas).
- Despacho en rafaga con Modo Enfoque integrado y reactivacion inteligente automatizada.
- Modulo de Propuestas y Cierre Economico con clasificacion de montos ganados y perdidos por objecion en Metricas.
- Ficha Comercial de Propuesta imprimible en 1 clic lista para PDF con `window.print()`.

### 4.3 Arquitectura de Interfaz Libre de Desbordamientos
- Montaje de popovers y tooltips explicativos en portal global fijado al `body` con clamp a bordes de pantalla para evitar recortes por `overflow: hidden`.
- Estandarizacion de botones de accion rápida a solo-icono (36x36 px escritorio, 42x42 px movil).
- Verificacion de diseno responsivo libre de desbordamientos en 5 resoluciones (360x800, 390x844, 768x1024, 1366x768, 1920x1080) mediante suite E2E con Playwright.
