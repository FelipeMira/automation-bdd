#!/bin/bash
# =============================================================================
# run.sh — Executa automações BDD com Appium + Behave
#
# Uso:
#   ./run.sh                          # Roda todas as features
#   ./run.sh features/pesquisar.feature  # Roda uma feature específica
#   ./run.sh --platform android       # Força plataforma Android
#   ./run.sh --tags @smoke            # Filtra por tag
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Verifica dependências ────────────────────────────────────────────────────
check_deps() {
  if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERRO]${NC} Python3 não encontrado."
    exit 1
  fi

  if ! python3 -c "import behave" &>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} Instalando dependências..."
    pip3 install -r requirements.txt
  fi
}

# ─── Verifica Appium ──────────────────────────────────────────────────────────
check_appium() {
  if curl -s http://localhost:4723/status &>/dev/null; then
    echo -e "${GREEN}[OK]${NC}   Appium rodando em localhost:4723"
    return 0
  fi

  echo -e "${YELLOW}[INFO]${NC} Appium não está rodando. Iniciando..."
  if ! command -v appium &>/dev/null; then
    echo -e "${RED}[ERRO]${NC} Appium não instalado. Execute:"
    echo "  npm install -g appium"
    echo "  appium driver install xcuitest"
    echo "  appium driver install uiautomator2"
    exit 1
  fi

  nohup appium --log /tmp/appium.log > /tmp/appium.log 2>&1 &
  echo -e "${CYAN}[INFO]${NC} Aguardando Appium iniciar..."
  local waited=0
  while [ $waited -lt 15 ]; do
    if curl -s http://localhost:4723/status &>/dev/null; then
      echo -e "${GREEN}[OK]${NC}   Appium iniciado (PID $!)"
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done

  echo -e "${RED}[ERRO]${NC} Timeout aguardando Appium. Veja /tmp/appium.log"
  exit 1
}

# ─── Entrypoint ───────────────────────────────────────────────────────────────
check_deps
check_appium

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  automation-bdd | Appium + Python + Behave${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

behave "$@"
