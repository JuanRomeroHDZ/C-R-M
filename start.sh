#!/usr/bin/env bash
# ==============================================================================
# Sistema de Captacion, Prospeccion y CRM Local
# Script de automatizacion, deteccion de puertos y arranque de servicios
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
ALLOCATED_PORTS=()

PORT_RANGE_MIN=20000
PORT_RANGE_MAX=45000

log_info() {
    echo "[INFO] $1"
}

log_warn() {
    echo "[WARN] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# ------------------------------------------------------------------------------
# 1. Verificacion de dependencias del host
# ------------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker no esta instalado en este sistema."
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    log_error "Docker Compose v2 no esta disponible."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Inicializacion de archivo .env si no existe
# ------------------------------------------------------------------------------
generate_secret() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 24
    else
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
    fi
}

set_env_var() {
    local key="$1"
    local value="$2"
    if grep -qE "^${key}=" "${ENV_FILE}" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
    else
        echo "${key}=${value}" >> "${ENV_FILE}"
    fi
}

get_env_var() {
    local key="$1"
    grep -E "^${key}=" "${ENV_FILE}" 2>/dev/null | cut -d'=' -f2- | tr -d '[:space:]' || true
}

if [ ! -f "${ENV_FILE}" ]; then
    log_info "Archivo .env no encontrado. Creando a partir de .env.example..."
    if [ ! -f "${ENV_EXAMPLE}" ]; then
        log_error "Archivo .env.example no existe en la raiz."
        exit 1
    fi
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"

    # Generar secretos criptograficos seguros
    set_env_var "POSTGRES_PASSWORD" "$(generate_secret)"
    set_env_var "APP_SECRET_KEY" "$(generate_secret)"
    set_env_var "JWT_SECRET" "$(generate_secret)"
    log_info "Secretos iniciales generados aleatoriamente en .env."
fi

# ------------------------------------------------------------------------------
# 3. Logica de deteccion y asignacion dinamica de puertos
# ------------------------------------------------------------------------------
is_port_in_use() {
    local port="$1"

    # Verificacion con ss
    if command -v ss >/dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -qE "[: ]${port}[ \t\n]"; then
            return 0
        fi
    fi

    # Verificacion con lsof
    if command -v lsof >/dev/null 2>&1; then
        if lsof -iTCP:"${port}" -sTCP:LISTEN -P -n >/dev/null 2>&1; then
            return 0
        fi
    fi

    # Verificacion con Docker container port mappings
    if docker ps --format '{{.Ports}}' 2>/dev/null | grep -qE "[: ]${port}->"; then
        return 0
    fi

    # Verificacion con socket bind en Python
    if command -v python3 >/dev/null 2>&1; then
        if ! python3 -c "import socket, sys; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1);
try:
    s.bind(('0.0.0.0', int(sys.argv[1])))
    sys.exit(0)
except Exception:
    sys.exit(1)" "$port" 2>/dev/null; then
            return 0
        fi
    fi

    return 1
}

get_random_free_port() {
    local attempts=0
    local max_attempts=500
    local port

    while [ "$attempts" -lt "$max_attempts" ]; do
        port=$(( PORT_RANGE_MIN + RANDOM % (PORT_RANGE_MAX - PORT_RANGE_MIN + 1) ))

        local already_allocated=0
        for allocated in "${ALLOCATED_PORTS[@]}"; do
            if [ "$allocated" -eq "$port" ]; then
                already_allocated=1
                break
            fi
        done

        if [ "$already_allocated" -eq 0 ] && ! is_port_in_use "$port"; then
            ALLOCATED_PORTS+=("$port")
            echo "$port"
            return 0
        fi
        attempts=$((attempts + 1))
    done

    log_error "No se encontraron puertos libres en el rango ${PORT_RANGE_MIN}-${PORT_RANGE_MAX}"
    exit 1
}

assign_port() {
    local service_key="$1"
    local service_name="$2"
    local current_val
    current_val="$(get_env_var "$service_key")"

    local assigned_port=""

    if [ -n "$current_val" ]; then
        if is_port_in_use "$current_val"; then
            log_warn "Puerto configurado ${current_val} para ${service_name} esta ocupado. Asignando puerto dinamico..."
            assigned_port="$(get_random_free_port)"
        else
            assigned_port="$current_val"
            ALLOCATED_PORTS+=("$assigned_port")
        fi
    else
        log_info "Asignando puerto dinamico aleatorio para ${service_name}..."
        assigned_port="$(get_random_free_port)"
    fi

    set_env_var "$service_key" "$assigned_port"
    export "${service_key}=${assigned_port}"
}

log_info "Comprobando disponibilidad de puertos en host..."
assign_port "HOST_PORT_PROXY"    "Proxy Inverso"
assign_port "HOST_PORT_FRONTEND" "Frontend Web"
assign_port "HOST_PORT_BACKEND"  "Backend API"
assign_port "HOST_PORT_DB"       "PostgreSQL DB"
assign_port "HOST_PORT_REDIS"    "Redis Cache"

# ------------------------------------------------------------------------------
# 4. Carga y exportacion de variables activas
# ------------------------------------------------------------------------------
while IFS='=' read -r key val || [ -n "$key" ]; do
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    export "${key}=${val}"
done < "${ENV_FILE}"

# Obtener direccion IP local en red LAN
get_lan_ip() {
    local ip
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -z "$ip" ]; then
        ip="127.0.0.1"
    fi
    echo "$ip"
}

LAN_IP="$(get_lan_ip)"

# ------------------------------------------------------------------------------
# 5. Resumen de asignacion de infraestructura
# ------------------------------------------------------------------------------
echo "===================================================================="
echo "CRM LOCAL - ORQUESTACION DE INFRAESTRUCTURA (FASE 1)"
echo "===================================================================="
printf "%-18s | %-12s | %-14s | %-10s\n" "SERVICIO" "PUERTO HOST" "PUERTO INTERNO" "ESTADO"
echo "--------------------------------------------------------------------"
printf "%-18s | %-12s | %-14s | %-10s\n" "Proxy Perimetral" "${HOST_PORT_PROXY}"    "80/tcp"    "ASIGNADO"
printf "%-18s | %-12s | %-14s | %-10s\n" "Frontend Web"     "${HOST_PORT_FRONTEND}" "80/tcp"    "ASIGNADO"
printf "%-18s | %-12s | %-14s | %-10s\n" "Backend API"      "${HOST_PORT_BACKEND}"  "8000/tcp"  "ASIGNADO"
printf "%-18s | %-12s | %-14s | %-10s\n" "PostgreSQL"       "${HOST_PORT_DB}"       "5432/tcp"  "ASIGNADO"
printf "%-18s | %-12s | %-14s | %-10s\n" "Redis Cache"      "${HOST_PORT_REDIS}"    "6379/tcp"  "ASIGNADO"
echo "===================================================================="
echo "Puntos de enlace:"
echo "  Acceso Local:    http://localhost:${HOST_PORT_PROXY}"
echo "  Acceso LAN:      http://${LAN_IP}:${HOST_PORT_PROXY}"
echo "  Documentacion:   http://localhost:${HOST_PORT_PROXY}/docs"
echo "  Salud Sistema:   http://localhost:${HOST_PORT_PROXY}/health"
echo "===================================================================="

# ------------------------------------------------------------------------------
# 6. Ejecucion de Docker Compose
# ------------------------------------------------------------------------------
log_info "Iniciando contenedores con Docker Compose..."
docker compose up -d --build "$@"

log_info "Despliegue completado con exito."
