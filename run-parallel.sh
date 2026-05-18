#!/bin/bash
# =============================================================================
# run-parallel.sh — Executa a mesma feature em iOS e Android simultaneamente
#
# Uso:
#   ./run-parallel.sh                                    # todas as features
#   ./run-parallel.sh features/pesquisar_batata.feature  # feature específica
#   ./run-parallel.sh features/ --tags @smoke            # com filtro de tag
#   ./run-parallel.sh features/ --platform ios           # só iOS
#   ./run-parallel.sh features/ --platform android       # só Android
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Argumentos ───────────────────────────────────────────────────────────────
FEATURE_PATH="${1:-features/}"
shift || true

PLATFORM_FILTER="both"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      PLATFORM_FILTER="$2"
      shift 2
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

# ─── Verifica Appium ──────────────────────────────────────────────────────────
if ! curl -s http://localhost:4723/status &>/dev/null; then
  echo -e "${YELLOW}[INFO]${NC} Iniciando Appium..."
  nohup appium --log /tmp/appium.log > /tmp/appium.log 2>&1 &
  sleep 3
  if ! curl -s http://localhost:4723/status &>/dev/null; then
    echo -e "${RED}[ERRO]${NC} Appium não iniciou. Veja /tmp/appium.log"
    exit 1
  fi
fi

# ─── Logs por plataforma ──────────────────────────────────────────────────────
IOS_LOG="/tmp/bdd_ios_run.log"
ANDROID_LOG="/tmp/bdd_android_run.log"
: > "$IOS_LOG"
: > "$ANDROID_LOG"

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  automation-bdd | Execução Paralela${NC}"
echo -e "${CYAN}${BOLD}  Feature: $FEATURE_PATH${NC}"
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

IOS_PID=""
ANDROID_PID=""

# ─── Lança iOS ────────────────────────────────────────────────────────────────
if [[ "$PLATFORM_FILTER" == "both" || "$PLATFORM_FILTER" == "ios" ]]; then
  echo -e "${BLUE}[iOS]${NC}     Iniciando..."
  PLATFORM=ios behave "$FEATURE_PATH" "${EXTRA_ARGS[@]}" > "$IOS_LOG" 2>&1 &
  IOS_PID=$!
fi

# ─── Lança Android ────────────────────────────────────────────────────────────
if [[ "$PLATFORM_FILTER" == "both" || "$PLATFORM_FILTER" == "android" ]]; then
  echo -e "${GREEN}[Android]${NC} Iniciando..."
  PLATFORM=android behave "$FEATURE_PATH" "${EXTRA_ARGS[@]}" > "$ANDROID_LOG" 2>&1 &
  ANDROID_PID=$!
fi

echo ""

# ─── Stream de logs em tempo real com prefixos ────────────────────────────────
stream_logs() {
  local ios_done=false
  local android_done=false
  local ios_line=0
  local android_line=0

  while true; do
    # Lê novas linhas do log iOS
    if [ -n "$IOS_PID" ] && ! $ios_done; then
      new_lines=$(tail -n +"$((ios_line + 1))" "$IOS_LOG" 2>/dev/null || true)
      if [ -n "$new_lines" ]; then
        count=$(echo "$new_lines" | wc -l | tr -d ' ')
        ios_line=$((ios_line + count))
        while IFS= read -r line; do
          echo -e "${BLUE}[iOS]${NC}     $line"
        done <<< "$new_lines"
      fi
      kill -0 "$IOS_PID" 2>/dev/null || ios_done=true
    fi

    # Lê novas linhas do log Android
    if [ -n "$ANDROID_PID" ] && ! $android_done; then
      new_lines=$(tail -n +"$((android_line + 1))" "$ANDROID_LOG" 2>/dev/null || true)
      if [ -n "$new_lines" ]; then
        count=$(echo "$new_lines" | wc -l | tr -d ' ')
        android_line=$((android_line + count))
        while IFS= read -r line; do
          echo -e "${GREEN}[Android]${NC} $line"
        done <<< "$new_lines"
      fi
      kill -0 "$ANDROID_PID" 2>/dev/null || android_done=true
    fi

    # Ambos terminaram?
    local all_done=true
    [ -n "$IOS_PID" ] && ! $ios_done && all_done=false
    [ -n "$ANDROID_PID" ] && ! $android_done && all_done=false
    $all_done && break

    sleep 0.5
  done

  # Drena qualquer linha final
  if [ -n "$IOS_PID" ]; then
    tail -n +"$((ios_line + 1))" "$IOS_LOG" 2>/dev/null | while IFS= read -r line; do
      echo -e "${BLUE}[iOS]${NC}     $line"
    done
  fi
  if [ -n "$ANDROID_PID" ]; then
    tail -n +"$((android_line + 1))" "$ANDROID_LOG" 2>/dev/null | while IFS= read -r line; do
      echo -e "${GREEN}[Android]${NC} $line"
    done
  fi
}

stream_logs

# ─── Coleta resultados ────────────────────────────────────────────────────────
IOS_STATUS=0
ANDROID_STATUS=0

if [ -n "$IOS_PID" ]; then
  wait "$IOS_PID" 2>/dev/null || IOS_STATUS=$?
fi
if [ -n "$ANDROID_PID" ]; then
  wait "$ANDROID_PID" 2>/dev/null || ANDROID_STATUS=$?
fi

# ─── Resumo final ─────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  Resultado Final${NC}"
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -n "$IOS_PID" ]; then
  if [ "$IOS_STATUS" -eq 0 ]; then
    echo -e "  ${BLUE}[iOS]${NC}     ${GREEN}✓ Passou${NC}"
  else
    echo -e "  ${BLUE}[iOS]${NC}     ${RED}✗ Falhou (código $IOS_STATUS)${NC}"
  fi
fi

if [ -n "$ANDROID_PID" ]; then
  if [ "$ANDROID_STATUS" -eq 0 ]; then
    echo -e "  ${GREEN}[Android]${NC} ${GREEN}✓ Passou${NC}"
  else
    echo -e "  ${GREEN}[Android]${NC} ${RED}✗ Falhou (código $ANDROID_STATUS)${NC}"
  fi
fi

echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Notificação macOS
TOTAL_FAIL=$((IOS_STATUS + ANDROID_STATUS))
if [ "$TOTAL_FAIL" -eq 0 ]; then
  osascript -e 'display notification "Todos os testes passaram ✓" with title "automation-bdd"' 2>/dev/null || true
else
  osascript -e 'display notification "Houve falhas nos testes ✗" with title "automation-bdd"' 2>/dev/null || true
fi

[ "$TOTAL_FAIL" -eq 0 ]
