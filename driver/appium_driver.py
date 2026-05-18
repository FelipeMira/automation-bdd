"""
appium_driver.py — Sessão Appium unificada para iOS e Android.

Encapsula todas as interações com o device: tap, type, swipe, scroll,
screenshot, lançamento de apps, URLs e árvore de acessibilidade.
"""

import time
import urllib.parse
from pathlib import Path

from appium import webdriver
from appium.webdriver.webdriver import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from driver.device_manager import (
    detect_platform,
    ensure_ios_ready,
    ensure_android_ready,
    get_ios_capabilities,
    get_android_capabilities,
    resolve_package,
)

APPIUM_URL = "http://localhost:4723"
MAX_RETRIES = 3
CMD_TIMEOUT = 15
RECOVER_WAIT = 2


class AppiumSession:
    """
    Sessão Appium com suporte a iOS (XCUITest) e Android (UiAutomator2).

    Uso:
        session = AppiumSession()
        session.start()
        session.launch_app("com.apple.mobilesafari")
        session.open_url("https://google.com")
        session.screenshot("/tmp/tela.png")
        session.stop()
    """

    def __init__(self, platform: str | None = None):
        self.platform = platform or detect_platform()
        self.driver: webdriver.Remote | None = None
        self._device_id: str | None = None

    # ─── Ciclo de vida da sessão ──────────────────────────────────────────────

    def start(self) -> None:
        """Inicia sessão Appium (boot device se necessário)."""
        print(f"[Runner] Plataforma: {self.platform.upper()}")

        if self.platform == "ios":
            udid = ensure_ios_ready()
            caps = get_ios_capabilities(udid)
            self._device_id = udid
        else:
            device_id = ensure_android_ready()
            caps = get_android_capabilities(device_id)
            self._device_id = device_id

        options = AppiumOptions()
        options.load_capabilities(caps)
        self.driver = webdriver.Remote(APPIUM_URL, options=options)
        self.driver.implicitly_wait(5)
        print("[Runner] Sessão Appium iniciada.\n")

    def stop(self) -> None:
        """Encerra sessão Appium."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    # ─── Apps ─────────────────────────────────────────────────────────────────

    def launch_app(self, bundle_or_package: str) -> None:
        """Lança app pelo bundle ID (iOS) ou package name (Android)."""
        pkg = resolve_package(bundle_or_package, self.platform)
        if self.platform == "ios":
            self.driver.execute_script("mobile: launchApp", {"bundleId": pkg})
        else:
            self.driver.execute_script(
                "mobile: activateApp", {"appId": pkg}
            )
        time.sleep(1.5)

    def terminate_app(self, bundle_or_package: str) -> None:
        """Encerra app pelo bundle ID (iOS) ou package name (Android)."""
        pkg = resolve_package(bundle_or_package, self.platform)
        if self.platform == "ios":
            self.driver.execute_script("mobile: terminateApp", {"bundleId": pkg})
        else:
            self.driver.execute_script(
                "mobile: terminateApp", {"appId": pkg}
            )

    def open_url(self, url: str) -> None:
        """Abre URL no navegador padrão."""
        if self.platform == "ios":
            self.driver.execute_script("mobile: launchApp", {
                "bundleId": "com.apple.mobilesafari"
            })
            time.sleep(1)
            self.driver.get(url)
        else:
            self.driver.get(url)
        time.sleep(1.5)

    # ─── Navegação ────────────────────────────────────────────────────────────

    def home(self) -> None:
        """Pressiona botão Home."""
        if self.platform == "ios":
            self.driver.execute_script("mobile: pressButton", {"name": "home"})
        else:
            self.driver.press_keycode(3)  # KEYCODE_HOME
        time.sleep(0.5)

    def back(self) -> None:
        """Pressiona botão Voltar (Android) ou tenta BackButton (iOS)."""
        if self.platform == "android":
            self.driver.press_keycode(4)  # KEYCODE_BACK
        else:
            try:
                el = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Back")
                el.click()
            except NoSuchElementException:
                pass
        time.sleep(0.5)

    # ─── Interações ───────────────────────────────────────────────────────────

    def tap_by_label(self, label: str, timeout: int = CMD_TIMEOUT) -> None:
        """Toca em elemento pelo accessibility label (AXLabel / content-desc)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                el = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, label)
                el.click()
                return
            except NoSuchElementException:
                pass
            try:
                if self.platform == "android":
                    el = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{label}")')
                else:
                    # CONTAINS[c] = case-insensitive no NSPredicate do iOS
                    el = self.driver.find_element(AppiumBy.IOS_PREDICATE,
                        f'label CONTAINS[c] "{label}" OR name CONTAINS[c] "{label}"')
                el.click()
                return
            except NoSuchElementException:
                time.sleep(1)

        raise NoSuchElementException(f'Elemento não encontrado: "{label}"')

    def tap_switch(self, label: str, timeout: int = CMD_TIMEOUT) -> None:
        """
        Ativa/desativa um toggle switch pelo label ou name.

        Hierarquia no iOS (descoberta via page_source):
          XCUIElementTypeSwitch [outer, accessible=true, width=full-row]
            ├─ XCUIElementTypeButton [label=<texto>, accessible=false]
            └─ XCUIElementTypeSwitch [knob, accessible=false, width=63]

        Estratégias em ordem de preferência:
          1. XPath: XCUIElementTypeButton[@label] → following-sibling Switch (o knob)
          2. XPath: XCUIElementTypeSwitch[@label] → child Switch (mesmo knob)
          3. Fallback: localiza o outer switch e toca 32px antes da borda direita
        """
        from selenium.webdriver.common.by import By

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.platform == "ios":
                # Estratégia 1: button irmão do knob
                try:
                    knob = self.driver.find_element(
                        By.XPATH,
                        f'//XCUIElementTypeButton[@label="{label}"]'
                        f'/following-sibling::XCUIElementTypeSwitch',
                    )
                    knob.click()
                    return
                except NoSuchElementException:
                    pass

                # Estratégia 2: outer switch → child switch
                try:
                    knob = self.driver.find_element(
                        By.XPATH,
                        f'//XCUIElementTypeSwitch[@label="{label}"]/XCUIElementTypeSwitch',
                    )
                    knob.click()
                    return
                except NoSuchElementException:
                    pass

                # Estratégia 3 (fallback): toca 32px antes da borda direita do outer switch
                try:
                    try:
                        outer = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, label)
                    except NoSuchElementException:
                        outer = self.driver.find_element(
                            AppiumBy.IOS_PREDICATE,
                            f'type == "XCUIElementTypeSwitch" AND label CONTAINS[c] "{label}"',
                        )
                    rect = outer.rect
                    cx = rect["x"] + rect["width"] - 32
                    cy = rect["y"] + rect["height"] / 2
                    self.driver.execute_script("mobile: tap", {"x": cx, "y": cy})
                    return
                except NoSuchElementException:
                    pass

            else:
                try:
                    el = self.driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().className("android.widget.Switch")'
                        f'.textContains("{label}")',
                    )
                    el.click()
                    return
                except NoSuchElementException:
                    pass

            time.sleep(1)

        raise NoSuchElementException(f'Switch não encontrado: "{label}"')

    def tap_by_coords(self, x: float, y: float) -> None:
        """Toca em coordenadas absolutas."""
        self.driver.execute_script("mobile: tap", {"x": x, "y": y})

    def type_text(self, text: str) -> None:
        """Digita texto no elemento focado."""
        try:
            active = self.driver.switch_to.active_element
            active.send_keys(text)
        except Exception:
            self.driver.execute_script("mobile: type", {"text": text})

    def swipe(self, x1: float, y1: float, x2: float, y2: float,
              duration_ms: int = 300) -> None:
        """Swipe de (x1,y1) para (x2,y2)."""
        self.driver.swipe(int(x1), int(y1), int(x2), int(y2), duration_ms)

    def scroll_down(self) -> None:
        self.swipe(200, 600, 200, 200)

    def scroll_up(self) -> None:
        self.swipe(200, 200, 200, 600)

    def scroll_left(self) -> None:
        self.swipe(350, 400, 50, 400)

    def scroll_right(self) -> None:
        self.swipe(50, 400, 350, 400)

    # ─── Screenshot ───────────────────────────────────────────────────────────

    def screenshot(self, path: str) -> str:
        """Salva screenshot no caminho indicado. Retorna o caminho."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.driver.save_screenshot(path)
        return path

    # ─── Acessibilidade ───────────────────────────────────────────────────────

    def get_page_source(self) -> str:
        """Retorna o XML da árvore de acessibilidade atual."""
        return self.driver.page_source

    def wait_for_element(self, label: str, timeout: int = 15) -> bool:
        """Aguarda até que elemento com o label apareça na tela."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, label)
                return True
            except NoSuchElementException:
                time.sleep(1)
        return False

    # ─── Pesquisa ─────────────────────────────────────────────────────────────

    def search(self, query: str) -> None:
        """Pesquisa query no Google via navegador."""
        encoded = urllib.parse.quote(query)
        self.open_url(f"https://www.google.com/search?q={encoded}")

    # ─── Auto-recovery ────────────────────────────────────────────────────────

    def recover(self) -> None:
        """Tenta voltar para estado conhecido: Voltar → Home."""
        print("    ↩ Recuperando: tentando voltar para estado conhecido...")
        try:
            self.back()
        except Exception:
            pass
        time.sleep(0.5)
        try:
            self.home()
        except Exception:
            pass
        time.sleep(RECOVER_WAIT)
        print("    ↺ Pronto para retry.")
