"""
accessibility.py — Parse da árvore de acessibilidade (iOS XML / Android XML).

Permite buscar elementos por label, texto ou classe na árvore retornada
pelo Appium (driver.page_source).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class AccessibilityNode:
    label: str = ""
    text: str = ""
    class_name: str = ""
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    enabled: bool = True
    children: list["AccessibilityNode"] = field(default_factory=list)

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2


def parse_tree(page_source: str, platform: str) -> list[AccessibilityNode]:
    """Parseia o XML do Appium e retorna lista de nós raiz."""
    root = ET.fromstring(page_source)
    if platform == "ios":
        return _parse_ios_node(root)
    return _parse_android_node(root)


def _parse_ios_node(element: ET.Element) -> list[AccessibilityNode]:
    nodes = []
    for child in element:
        node = AccessibilityNode(
            label=child.get("label", "") or child.get("name", ""),
            text=child.get("value", ""),
            class_name=child.get("type", ""),
            x=float(child.get("x", 0)),
            y=float(child.get("y", 0)),
            width=float(child.get("width", 0)),
            height=float(child.get("height", 0)),
            enabled=child.get("enabled", "true").lower() == "true",
            children=_parse_ios_node(child),
        )
        nodes.append(node)
    return nodes


def _parse_android_node(element: ET.Element) -> list[AccessibilityNode]:
    nodes = []
    for child in element:
        bounds = child.get("bounds", "[0,0][0,0]")
        x, y, x2, y2 = _parse_android_bounds(bounds)
        node = AccessibilityNode(
            label=child.get("content-desc", ""),
            text=child.get("text", ""),
            class_name=child.get("class", ""),
            x=x, y=y,
            width=x2 - x,
            height=y2 - y,
            enabled=child.get("enabled", "true").lower() == "true",
            children=_parse_android_node(child),
        )
        nodes.append(node)
    return nodes


def _parse_android_bounds(bounds: str) -> tuple[float, float, float, float]:
    """[x1,y1][x2,y2] → (x1, y1, x2, y2)"""
    try:
        parts = bounds.replace("][", ",").strip("[]").split(",")
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except Exception:
        return 0, 0, 0, 0


def find_by_label(nodes: list[AccessibilityNode], label: str,
                  partial: bool = True) -> AccessibilityNode | None:
    """Busca nó por label (ou content-desc no Android). Retorna primeiro match."""
    label_lower = label.lower()
    for node in nodes:
        node_label = (node.label or node.text or "").lower()
        if (partial and label_lower in node_label) or node_label == label_lower:
            return node
        found = find_by_label(node.children, label, partial)
        if found:
            return found
    return None


def print_tree(nodes: list[AccessibilityNode], indent: int = 0) -> None:
    """Imprime árvore no terminal (debug)."""
    for node in nodes:
        prefix = "  " * indent
        label = node.label or node.text or ""
        print(f"{prefix}[{node.class_name}] \"{label}\"  "
              f"frame=({node.x:.0f},{node.y:.0f},{node.width:.0f},{node.height:.0f})")
        print_tree(node.children, indent + 1)
