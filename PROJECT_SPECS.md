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

### Fase 6: Interfaz de Usuario, Panel Modular y Onboarding
- Maquetacion responsiva y accesible bajo escala de grises estilo Notion/Obsidian.
- Panel de configuracion modular avanzado (parametros de scraping, pesos de scoring, red).
- Flujo interactivo guiado para el arranque inicial (onboarding).

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
