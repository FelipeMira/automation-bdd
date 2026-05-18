"""
environment.py — Hooks do Behave: setup e teardown da sessão Appium.

Executado automaticamente antes/depois de cada feature e cenário.
"""

import os
import time
from pathlib import Path

from driver.appium_driver import AppiumSession
from utils.screenshot import take_screenshot

SCREENSHOTS_DIR = Path(__file__).parent.parent / "automation_scripts" / "screenshots"


# ─── Suite completa ───────────────────────────────────────────────────────────

def before_all(context):
    """Inicia sessão Appium uma única vez para toda a suite."""
    platform = os.environ.get("PLATFORM", None)
    context.session = AppiumSession(platform=platform)
    context.session.start()
    context.platform = context.session.platform

    # Contadores globais
    context.total_steps = 0
    context.failed_steps = 0


def after_all(context):
    """Encerra sessão Appium."""
    if hasattr(context, "session") and context.session:
        context.session.stop()


# ─── Feature ──────────────────────────────────────────────────────────────────

def before_feature(context, feature):
    print(f"\n▶ Feature: {feature.name}")


def after_feature(context, feature):
    passed = sum(1 for s in feature.scenarios if s.status == "passed")
    failed = sum(1 for s in feature.scenarios if s.status == "failed")
    total = len(feature.scenarios)
    print(f"\n{'✓' if failed == 0 else '✗'} Feature '{feature.name}': "
          f"{passed}/{total} cenários ok")


# ─── Cenário ──────────────────────────────────────────────────────────────────

def before_scenario(context, scenario):
    context.step_count = 0
    context.step_failures = 0
    print(f"\n  Cenário: {scenario.name}")


def after_scenario(context, scenario):
    if scenario.status == "failed":
        # Screenshot automático em falha
        try:
            take_screenshot(context.session, f"FALHA_{scenario.name.replace(' ', '_')}")
        except Exception:
            pass
        print(f"\n  ✗ Cenário FALHOU: {scenario.name}")
    else:
        # Evidência do último passo (cenário passou)
        try:
            take_screenshot(context.session, f"evidencia_{scenario.name.replace(' ', '_')}")
        except Exception:
            pass
        print(f"\n  ✓ Cenário ok: {scenario.name}")


# ─── Step ─────────────────────────────────────────────────────────────────────

def before_step(context, step):
    context.step_count = getattr(context, "step_count", 0) + 1
    print(f"\n  Passo {context.step_count}: {step.name}")


def after_step(context, step):
    if step.status == "failed":
        context.step_failures = getattr(context, "step_failures", 0) + 1
        print(f"    ✗ Falhou: {step.name}")
    else:
        print(f"    ✓ Ok")
