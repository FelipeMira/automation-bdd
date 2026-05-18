"""
screenshot.py — Captura e salva screenshots com timestamp.
"""

import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "automation_scripts" / "screenshots"


def take_screenshot(driver_session, label: str = "screenshot") -> str:
    """
    Captura screenshot e salva em automation_scripts/screenshots/.

    Args:
        driver_session: instância de AppiumSession
        label: prefixo do nome do arquivo

    Returns:
        Caminho completo do arquivo salvo.
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    label_clean = label.replace(" ", "_").replace("/", "-")
    platform = getattr(driver_session, "platform", "unknown")
    path = str(SCREENSHOTS_DIR / f"{label_clean}_{platform}_{ts}.png")
    driver_session.screenshot(path)
    try:
        rel = str(Path(path).relative_to(PROJECT_ROOT))
    except ValueError:
        rel = path
    print(f"    📸 Screenshot salvo: {rel}")
    return path
