"""
device_manager.py — Detecção de plataforma e gerenciamento de dispositivos.

Detecta automaticamente iOS (simulador ativo) ou Android (device/emulador),
devolve as capabilities Appium corretas e garante que o device está pronto.
"""

import json
import os
import subprocess
import time


# ─── Detecção de plataforma ───────────────────────────────────────────────────

def detect_platform() -> str:
    """Retorna 'ios' ou 'android' com base nos devices ativos."""
    forced = os.environ.get("PLATFORM", "").lower()
    if forced in ("ios", "android"):
        return forced

    if _get_booted_ios_udid():
        return "ios"
    if _get_connected_android_device():
        return "android"
    return "ios"  # padrão


def _get_booted_ios_udid() -> str | None:
    """Retorna o UDID do primeiro simulador iOS com estado Booted, ou None."""
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        for devices in data.get("devices", {}).values():
            for d in devices:
                if d.get("state") == "Booted":
                    return d["udid"]
    except Exception:
        pass
    return None


def _get_connected_android_device() -> str | None:
    """Retorna o ID do primeiro device Android conectado, ou None."""
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) == 2 and parts[1] in ("device", "emulator"):
                return parts[0]
    except Exception:
        pass
    return None


# ─── Boot automático ──────────────────────────────────────────────────────────

def ensure_ios_ready() -> str:
    """Garante simulador iOS ativo. Retorna o UDID."""
    udid = _get_booted_ios_udid()
    if udid:
        return udid

    print("[Device] Nenhum simulador ativo — inicializando...")
    udid = _find_preferred_ios_udid()
    if not udid:
        raise RuntimeError("Nenhum simulador iOS disponível. Crie um via Xcode.")

    subprocess.run(["xcrun", "simctl", "boot", udid], check=False)
    subprocess.run(["open", "-a", "Simulator"], check=False)

    for _ in range(30):
        if _get_booted_ios_udid():
            break
        time.sleep(2)
    else:
        raise RuntimeError("Timeout aguardando boot do simulador iOS.")

    print("[Device] Simulador pronto.")
    return udid


def ensure_android_ready() -> str:
    """Garante emulador Android ativo. Retorna o device ID."""
    device = _get_connected_android_device()
    if device:
        _wait_android_ui_ready(device)
        return device

    print("[Device] Nenhum device Android ativo — inicializando emulador...")
    avds = subprocess.run(
        ["emulator", "-list-avds"], capture_output=True, text=True, timeout=10,
    ).stdout.strip().splitlines()

    if not avds:
        raise RuntimeError("Nenhum AVD Android disponível. Crie via Android Studio.")

    subprocess.Popen(
        ["emulator", "-avd", avds[0]],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        device = _get_connected_android_device()
        if device:
            break
        time.sleep(2)
    else:
        raise RuntimeError("Timeout aguardando emulador Android.")

    _wait_android_ui_ready(device)
    print("[Device] Emulador pronto.")
    return device


def _find_preferred_ios_udid() -> str | None:
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "available", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        preferred, fallback = [], []
        for devices in data.get("devices", {}).values():
            for d in devices:
                if not d.get("isAvailable", True):
                    continue
                name = d["name"].lower()
                if "iphone 17 pro" in name:
                    preferred.append(d["udid"])
                elif "iphone" in name:
                    fallback.append(d["udid"])
        candidates = preferred or fallback
        return candidates[0] if candidates else None
    except Exception:
        return None


def _wait_android_ui_ready(device: str, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = subprocess.run(
                ["adb", "-s", device, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=5,
            )
            if r.stdout.strip() == "1":
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("Timeout aguardando UI Android.")


# ─── Capabilities Appium ──────────────────────────────────────────────────────

def get_ios_capabilities(udid: str) -> dict:
    """Retorna capabilities para Appium 2 + XCUITest."""
    return {
        "platformName": "iOS",
        "appium:automationName": "XCUITest",
        "appium:udid": udid,
        "appium:noReset": True,
        "appium:newCommandTimeout": 300,
        "appium:waitForQuiescence": False,
    }


def get_android_capabilities(device_id: str) -> dict:
    """Retorna capabilities para Appium 2 + UiAutomator2."""
    return {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": device_id,
        "appium:noReset": True,
        "appium:newCommandTimeout": 300,
    }


# ─── Bundle ID / Package mapping ─────────────────────────────────────────────

IOS_TO_ANDROID = {
    "com.apple.mobilesafari":    "com.android.chrome",
    "com.apple.Preferences":     "com.android.settings",
    "com.apple.camera":          "com.android.camera2",
    "com.apple.MobileSMS":       "com.google.android.apps.messaging",
    "com.apple.Maps":            "com.google.android.apps.maps",
    "com.apple.mobilenotes":     "com.google.android.keep",
    "com.apple.calculator":      "com.google.android.calculator",
    "com.apple.clock":           "com.google.android.deskclock",
    "com.apple.mobileslideshow": "com.google.android.apps.photos",
    "com.apple.AppStore":        "com.android.vending",
}


def resolve_package(bundle_or_package: str, platform: str) -> str:
    """Converte bundle ID iOS para package Android quando necessário."""
    if platform == "android":
        return IOS_TO_ANDROID.get(bundle_or_package, bundle_or_package)
    return bundle_or_package
