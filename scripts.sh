#!/bin/bash

# 📦 Scripts para FastAPI - Versión simplificada y funcional

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}📢 $1${NC}"; }

# Verificar entorno virtual
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            return 0
        else
            print_error "No hay entorno virtual .venv"
            return 1
        fi
    fi
    return 0
}

# COMANDOS
case "$1" in
    start)
        print_header "INICIANDO PROYECTO"
        check_venv || exit 1
        
        # Iniciar servicios Docker si existen
        if [ -f "docker-compose.yml" ]; then
            print_info "Iniciando Docker services..."
            docker-compose up -d db redis
            sleep 2
        fi
        
        # Iniciar API
        print_info "Iniciando FastAPI..."
        pkill -f "uvicorn.*8000" 2>/dev/null
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        PID=$!
        
        print_success "API iniciada (PID: $PID)"
        echo ""
        print_info "🌐 http://localhost:8000"
        print_info "📚 http://localhost:8000/docs"
        print_info "🏥 http://localhost:8000/health"
        ;;
    
    stop)
        print_header "DETENIENDO PROYECTO"
        pkill -f "uvicorn.*8000" 2>/dev/null
        if [ -f "docker-compose.yml" ]; then
            docker-compose down
        fi
        print_success "Todo detenido"
        ;;
    
    restart)
        ./scripts.sh stop
        sleep 2
        ./scripts.sh start
        ;;
    
    status)
        print_header "ESTADO DEL PROYECTO"
        echo "📁 $(pwd)"
        echo "🐍 $(python --version 2>/dev/null || echo 'Python?')"
        
        if [[ -n "$VIRTUAL_ENV" ]]; then
            print_success "Entorno: $(basename $VIRTUAL_ENV)"
        else
            print_error "Sin entorno virtual"
        fi
        
        echo ""
        print_info "🌐 API:"
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Corriendo en :8000"
        else
            print_error "No responde"
        fi
        
        echo ""
        print_info "🐋 Docker:"
        if [ -f "docker-compose.yml" ]; then
            docker-compose ps 2>/dev/null || print_error "Docker no disponible"
        else
            print_info "Sin docker-compose.yml"
        fi
        ;;
    
    logs)
        print_header "LOGS"
        if pgrep -f "uvicorn" >/dev/null; then
            print_info "Proceso uvicorn encontrado"
            ps aux | grep uvicorn | grep -v grep
        else
            print_error "API no corriendo"
        fi
        
        if [ -f "docker-compose.yml" ]; then
            echo ""
            docker-compose logs --tail=10 2>/dev/null || true
        fi
        ;;
    
    install)
        print_header "INSTALANDO DEPENDENCIAS"
        check_venv || exit 1
        
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            pip install fastapi uvicorn sqlmodel pydantic-settings
            pip install python-jose[cryptography] passlib[bcrypt] asyncpg redis
        fi
        
        print_success "Dependencias instaladas"
        ;;
    
    check|verify)
        print_header "VERIFICANDO DEPENDENCIAS"
        check_venv || exit 1
        
        echo "📦 Paquetes esenciales:"
        for pkg in fastapi uvicorn sqlmodel pydantic_settings; do
            if python -c "import $pkg" 2>/dev/null; then
                print_success "  $pkg"
            else
                print_error "  $pkg"
            fi
        done
        
        echo ""
        echo "🔐 Autenticación:"
        for pkg in jose passlib; do
            if python -c "import $pkg" 2>/dev/null; then
                print_success "  $pkg"
            else
                print_error "  $pkg"
            fi
        done
        
        echo ""
        echo "🗄️  Base de datos:"
        for pkg in asyncpg redis; do
            if python -c "import $pkg" 2>/dev/null; then
                print_success "  $pkg"
            else
                print_error "  $pkg"
            fi
        done
        
        echo ""
        echo "📁 Estructura:"
        for file in "app/main.py" ".env" "docker-compose.yml"; do
            if [ -f "$file" ]; then
                print_success "  $file"
            else
                print_info "  $file (no encontrado)"
            fi
        done
        
        echo ""
        print_success "Verificación completada"
        ;;
    
    format)
        print_header "FORMATEANDO CÓDIGO"
        check_venv || exit 1
        
        if command -v black &>/dev/null; then
            black app/
            print_success "Black aplicado"
        else
            print_error "Black no instalado"
        fi
        
        if command -v isort &>/dev/null; then
            isort app/
            print_success "Isort aplicado"
        fi
        ;;
    
    test)
        print_header "EJECUTANDO TESTS"
        check_venv || exit 1
        pytest -v 2>/dev/null || print_error "pytest no disponible"
        ;;
    
    shell)
        print_header "SHELL INTERACTIVA"
        check_venv || exit 1
        python -i -c "from app.main import app; print('App disponible como: app')"
        ;;
    
    clean)
        print_header "LIMPIANDO CACHÉ"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find . -type f -name "*.pyc" -delete 2>/dev/null
        print_success "Cache limpiado"
        ;;
    
    help|"")
        print_header "AYUDA - COMANDOS DISPONIBLES"
        echo ""
        echo "  start    - Iniciar API y servicios"
        echo "  stop     - Detener todo"
        echo "  restart  - Reiniciar"
        echo "  status   - Ver estado"
        echo "  logs     - Ver logs"
        echo "  check    - Verificar dependencias"
        echo "  install  - Instalar dependencias"
        echo "  format   - Formatear código"
        echo "  test     - Ejecutar tests"
        echo "  shell    - Python interactivo"
        echo "  clean    - Limpiar cache"
        echo "  help     - Esta ayuda"
        echo ""
        echo "📁 Ubicación: $(pwd)"
        ;;
    
    *)
        print_error "Comando no válido: $1"
        echo "Usa: ./scripts.sh help"
        exit 1
        ;;
esac
