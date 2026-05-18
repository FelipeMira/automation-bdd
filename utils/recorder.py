"""
recorder.py — Gravação de automações em linguagem natural → arquivo .feature (Gherkin).

Uso via CLI:
    python -m utils.recorder start "pesquisar_batata"
    python -m utils.recorder step "When" "abra o safari"
    python -m utils.recorder step "When" "pesquize batata da terra no navegador"
    python -m utils.recorder stop

O arquivo gerado em automation_scripts/ pode ser executado com:
    behave features/automation_scripts/<nome>.feature
"""

import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
AUTOMATION_DIR = PROJECT_ROOT / "automation_scripts"
FEATURES_DIR = PROJECT_ROOT / "features"

STATE_FILE = Path("/tmp/bdd_recording_state")
STEPS_FILE = Path("/tmp/bdd_recording_steps")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cmd_start(name: str) -> None:
    if STATE_FILE.exists():
        current = STATE_FILE.read_text().strip()
        print(f"[WARN] Já existe gravação ativa: \"{current}\"")
        print("       Use 'stop' para finalizar ou apague /tmp/bdd_recording_state")
        sys.exit(1)

    name = re.sub(r"[^\w\-]", "_", name.lower())
    STATE_FILE.write_text(name)
    STEPS_FILE.write_text("")
    print(f"\n● Gravação iniciada: \"{name}\"")
    print("  Use: python -m utils.recorder step <When|Given|Then> \"descrição\"")
    print("  Use: python -m utils.recorder stop\n")


def cmd_step(keyword: str, description: str) -> None:
    if not STATE_FILE.exists():
        print("[ERRO] Nenhuma gravação ativa. Use 'start' primeiro.")
        sys.exit(1)

    keyword = keyword.capitalize()
    if keyword not in ("Given", "When", "Then", "And"):
        keyword = "When"

    with open(STEPS_FILE, "a") as f:
        f.write(f"{keyword}|{description}\n")

    count = len(STEPS_FILE.read_text().strip().splitlines())
    print(f"[REC]  Passo {count}: {description}")


def cmd_stop() -> None:
    if not STATE_FILE.exists():
        print("[WARN] Nenhuma gravação ativa.")
        sys.exit(0)

    name = STATE_FILE.read_text().strip()
    steps_raw = STEPS_FILE.read_text().strip().splitlines() if STEPS_FILE.exists() else []

    # Gera .feature
    lines = [
        f"# Gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}",
        f"Feature: {name.replace('_', ' ').title()}",
        "",
        f"  Scenario: {name.replace('_', ' ').title()}",
    ]

    for i, raw in enumerate(steps_raw):
        if "|" not in raw:
            continue
        keyword, description = raw.split("|", 1)
        # Primeiro passo sempre é Given, independente do keyword informado
        if i == 0:
            keyword = "Given"
        lines.append(f"    {keyword} {description}")

    feature_content = "\n".join(lines) + "\n"

    # Salva em features/automation_scripts/
    feature_dir = FEATURES_DIR / "automation_scripts"
    feature_dir.mkdir(parents=True, exist_ok=True)
    dest = feature_dir / f"{name}.feature"
    dest.write_text(feature_content)

    # Limpa estado
    STATE_FILE.unlink(missing_ok=True)
    STEPS_FILE.unlink(missing_ok=True)

    print(f"\n● Gravação salva: {dest}")
    print(f"  Para executar: behave {dest}\n")
    print("─── Feature gerada ─────────────────────────────────")
    print(feature_content)
    print("────────────────────────────────────────────────────")


def cmd_status() -> None:
    if not STATE_FILE.exists():
        print("Nenhuma gravação ativa.")
        return
    name = STATE_FILE.read_text().strip()
    steps = STEPS_FILE.read_text().strip().splitlines() if STEPS_FILE.exists() else []
    print(f"● Gravando: \"{name}\" — {len(steps)} passo(s)")
    for i, s in enumerate(steps, 1):
        if "|" in s:
            kw, desc = s.split("|", 1)
            print(f"  {i:02d}. {kw} {desc}")


# ─── Classe para uso programático ─────────────────────────────────────────────

class Recorder:
    """Gravador de sessão para uso dentro do Behave (environment.py)."""

    def __init__(self):
        self.name: str | None = None
        self.steps: list[tuple[str, str]] = []
        self.active = False

    def start(self, name: str) -> None:
        self.name = re.sub(r"[^\w\-]", "_", name.lower())
        self.steps = []
        self.active = True
        print(f"\n● Gravação iniciada: \"{self.name}\"")

    def add_step(self, description: str, keyword: str = "When") -> None:
        if not self.active:
            return
        self.steps.append((keyword, description))

    def stop(self) -> str | None:
        if not self.active or not self.name:
            return None

        lines = [
            f"# Gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Feature: {self.name.replace('_', ' ').title()}",
            "",
            f"  Scenario: {self.name.replace('_', ' ').title()}",
        ]

        for i, (keyword, description) in enumerate(self.steps):
            kw = "Given" if i == 0 else keyword
            lines.append(f"    {kw} {description}")

        feature_content = "\n".join(lines) + "\n"

        feature_dir = FEATURES_DIR / "automation_scripts"
        feature_dir.mkdir(parents=True, exist_ok=True)
        dest = feature_dir / f"{self.name}.feature"
        dest.write_text(feature_content)

        self.active = False
        print(f"\n● Gravação salva: {dest}")
        print("─── Feature gerada ─────────────────────────────────")
        print(feature_content)
        print("────────────────────────────────────────────────────")
        return str(dest)


# ─── Entrypoint CLI ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso: python -m utils.recorder <start|step|stop|status> [args]")
        sys.exit(1)

    subcmd = args[0]
    if subcmd == "start":
        cmd_start(args[1] if len(args) > 1 else f"automacao_{int(time.time())}")
    elif subcmd == "step":
        if len(args) < 3:
            print("Uso: python -m utils.recorder step <Given|When|Then> \"descrição\"")
            sys.exit(1)
        cmd_step(args[1], args[2])
    elif subcmd == "stop":
        cmd_stop()
    elif subcmd == "status":
        cmd_status()
    else:
        print(f"Subcomando desconhecido: {subcmd}")
        sys.exit(1)
