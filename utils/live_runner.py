"""
live_runner.py — Daemon de execução ao vivo durante gravação BDD.

Mantém uma sessão Appium ativa e executa steps à medida que são gravados.
Comunicação via arquivos /tmp:

  /tmp/bdd_live_cmd    ← escreva o texto do step para executar
  /tmp/bdd_live_result ← leia o resultado (ok / erro: ...)
  /tmp/bdd_live_ready  ← existe quando a sessão está pronta
  /tmp/bdd_live_pid    ← PID do daemon

Uso:
    python -m utils.live_runner          # inicia o daemon
    python -m utils.live_runner stop     # encerra o daemon
"""

import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CMD_FILE    = Path("/tmp/bdd_live_cmd")
RESULT_FILE = Path("/tmp/bdd_live_result")
PID_FILE    = Path("/tmp/bdd_live_pid")
READY_FILE  = Path("/tmp/bdd_live_ready")


# ─── Mapeamento de steps ──────────────────────────────────────────────────────

def execute(session, step_text: str) -> str:
    """Mapeia texto de step para ação Appium e executa."""
    t = step_text.lower().strip()

    # ── Ajustes / Settings ───────────────────────────────────────────────────
    if any(x in t for x in ["ajustes", "configurações", "settings", "preferences"]):
        if any(x in t for x in ["abro", "abrir", "acesso", "acessar", "abre", "inicio"]):
            session.launch_app("com.apple.Preferences")
            time.sleep(2)
            return "ok"
        if any(x in t for x in ["fecho", "fechar", "encerro"]):
            session.terminate_app("com.apple.Preferences")
            return "ok"

    # ── Safari / Navegador ────────────────────────────────────────────────────
    if "safari" in t or "navegador" in t or "browser" in t:
        if any(x in t for x in ["abro", "abrir", "inicio", "iniciar", "abre"]):
            session.launch_app("com.apple.mobilesafari")
            time.sleep(1.5)
            return "ok"
        if any(x in t for x in ["fecho", "fechar", "encerro"]):
            session.terminate_app("com.apple.mobilesafari")
            return "ok"

    # ── Pesquisa ─────────────────────────────────────────────────────────────
    for prefix in ["pesquiso ", "pesquisar ", "pesquize ", "busco ", "buscar ", "procuro ", "search "]:
        if t.startswith(prefix):
            q = step_text[len(prefix):].strip()
            for suffix in [" no navegador", " no browser", " no safari", " no chrome"]:
                if q.lower().endswith(suffix):
                    q = q[:-len(suffix)].strip()
            session.search(q)
            return "ok"

    # ── URL ───────────────────────────────────────────────────────────────────
    for prefix in ["abro a url ", "navego para a url ", "abro url ", "navego para "]:
        if t.startswith(prefix):
            url = step_text[len(prefix):].strip()
            if not url.startswith("http"):
                url = "https://" + url
            session.open_url(url)
            return "ok"

    # ── Home ──────────────────────────────────────────────────────────────────
    if t in ["home", "tela inicial", "ir para home", "página inicial",
             "acesse home", "acesso home", "volto para home", "voltar para home"]:
        session.home()
        return "ok"

    # ── Voltar ────────────────────────────────────────────────────────────────
    if t in ["volto", "volta", "voltar", "clico em voltar", "boto voltar", "ir para trás"]:
        session.back()
        return "ok"

    # ── Scroll ────────────────────────────────────────────────────────────────
    if any(x in t for x in ["scroll para baixo", "rolo para baixo", "deslizo para baixo"]):
        session.scroll_down()
        return "ok"
    if any(x in t for x in ["scroll para cima", "rolo para cima", "deslizo para cima"]):
        session.scroll_up()
        return "ok"
    if any(x in t for x in ["scroll para esquerda", "deslizo para esquerda"]):
        session.scroll_left()
        return "ok"
    if any(x in t for x in ["scroll para direita", "deslizo para direita"]):
        session.scroll_right()
        return "ok"

    # ── Toggle Switch ─────────────────────────────────────────────────────────
    for prefix in ["clicar no seletor de ", "clico no seletor de ", "ativo o seletor de "]:
        if t.startswith(prefix):
            from appium.webdriver.common.appiumby import AppiumBy
            from selenium.webdriver.common.by import By
            label = step_text[len(prefix):].strip()

            # Estratégia 1: acha o label (XCUIElementTypeButton) e pega o
            # XCUIElementTypeSwitch irmão (mesma camada / mesmo pai).
            # Hierarquia no iOS:
            #   XCUIElementTypeSwitch [outer, accessible=true]
            #     ├─ XCUIElementTypeButton [label=Grade, accessible=false]
            #     └─ XCUIElementTypeSwitch [knob, accessible=false]  ← queremos este
            try:
                knob = session.driver.find_element(
                    By.XPATH,
                    f'//XCUIElementTypeButton[@label="{label}"]'
                    f'/following-sibling::XCUIElementTypeSwitch'
                )
                knob.click()
                time.sleep(0.5)
                return "ok"
            except Exception:
                pass

            # Estratégia 2: via child do outer switch (mesmo resultado diferente XPath)
            try:
                knob = session.driver.find_element(
                    By.XPATH,
                    f'//XCUIElementTypeSwitch[@label="{label}"]/XCUIElementTypeSwitch'
                )
                knob.click()
                time.sleep(0.5)
                return "ok"
            except Exception:
                pass

            # Estratégia 3 (fallback): localiza o outer switch acessível e toca
            # 32px antes da borda direita — onde o knob físico sempre está no iOS.
            outer = session.driver.find_element(
                AppiumBy.IOS_CLASS_CHAIN,
                f'**/XCUIElementTypeSwitch[`label CONTAINS[c] "{label}"'
                f' OR name CONTAINS[c] "{label}"`]'
            )
            rect = outer.rect
            knob_x = rect["x"] + rect["width"] - 32
            knob_y = rect["y"] + rect["height"] / 2
            session.driver.execute_script("mobile: tap", {"x": knob_x, "y": knob_y})
            time.sleep(0.5)
            return "ok"

    # ── Tap genérico ──────────────────────────────────────────────────────────
    for prefix in ["clico em ", "toco em ", "toco no ", "toco na ",
                   "pressiono ", "tap em ", "clicar em ", "toco "]:
        if t.startswith(prefix):
            label = step_text[len(prefix):].strip()
            session.tap_by_label(label)
            return "ok"

    # ── Digitar ───────────────────────────────────────────────────────────────
    for prefix in ["digito ", "escrevo ", "insiro ", "tipo "]:
        if t.startswith(prefix):
            text = step_text[len(prefix):].strip()
            session.type_text(text)
            return "ok"

    # ── Apps genéricos ────────────────────────────────────────────────────────
    for prefix in ["abro o app ", "inicio o app "]:
        if t.startswith(prefix):
            bundle = step_text[len(prefix):].strip()
            session.launch_app(bundle)
            time.sleep(1.5)
            return "ok"
    for prefix in ["fecho o app ", "encerro o app "]:
        if t.startswith(prefix):
            bundle = step_text[len(prefix):].strip()
            session.terminate_app(bundle)
            return "ok"

    # ── Screenshot ────────────────────────────────────────────────────────────
    if any(x in t for x in ["screenshot", "capturo a tela", "salvo a tela", "tiro screenshot"]):
        from utils.screenshot import take_screenshot
        take_screenshot(session, "live")
        return "ok"

    # ── Aguardar N segundos ───────────────────────────────────────────────────
    m = re.match(r"(?:aguardo|espero|wait)\s+(\d+)\s+segundos?", t)
    if m:
        time.sleep(int(m.group(1)))
        return "ok"
    if t in ["aguardo", "espero"]:
        time.sleep(2)
        return "ok"

    return f"⚠️  Step não mapeado para execução: '{step_text}' (gravado, mas não executado)"


# ─── Stop helper (chamado externamente) ───────────────────────────────────────

def cmd_stop_daemon():
    if not PID_FILE.exists():
        print("[LiveRunner] Nenhum daemon ativo.")
        return
    CMD_FILE.write_text("STOP")
    print("[LiveRunner] Sinal de parada enviado.")


# ─── Daemon principal ─────────────────────────────────────────────────────────

def main():
    from driver.appium_driver import AppiumSession

    # Limpa estado anterior
    for f in [CMD_FILE, RESULT_FILE, READY_FILE]:
        f.unlink(missing_ok=True)

    PID_FILE.write_text(str(os.getpid()))
    print(f"[LiveRunner] PID {os.getpid()} — iniciando sessão Appium...")

    session = AppiumSession()
    try:
        session.start()
    except Exception as e:
        print(f"[LiveRunner] Erro ao iniciar sessão: {e}")
        PID_FILE.unlink(missing_ok=True)
        sys.exit(1)

    READY_FILE.write_text("ready")
    print("[LiveRunner] ✓ Sessão pronta. Aguardando steps...")

    try:
        while True:
            if CMD_FILE.exists():
                cmd = CMD_FILE.read_text().strip()
                CMD_FILE.unlink(missing_ok=True)

                if cmd == "STOP":
                    RESULT_FILE.write_text("stopped")
                    break

                print(f"[LiveRunner] ▶ Executando: {cmd}")
                try:
                    result = execute(session, cmd)
                    RESULT_FILE.write_text(result)
                    print(f"[LiveRunner] {'✓' if result == 'ok' else result}")
                except Exception as e:
                    err = f"erro: {e}"
                    RESULT_FILE.write_text(err)
                    print(f"[LiveRunner] ✗ {err}")
            time.sleep(0.2)
    finally:
        session.stop()
        for f in [PID_FILE, READY_FILE, CMD_FILE]:
            f.unlink(missing_ok=True)
        print("[LiveRunner] Sessão encerrada.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        cmd_stop_daemon()
    else:
        main()
