"""Fail CI if production app code bypasses the approved broker-write boundary.

The AST scanner checks adapter-named receivers (adapter, *_adapter, or
*upstox*) and ignores comments/docstrings. Normal PAPER
ExecutionService.place_order calls are not broker API writes. Production code
that wraps a broker adapter must keep its write-capable receiver explicitly
adapter-named. Dynamic dispatch/reflection is prohibited for broker writes and
cannot be reliably found by this source guard alone.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

WRITE_METHODS = {"place_order", "modify_order", "cancel_order"}
APPROVED_CALLER = Path("services/live_broker_write_service.py")


def _attribute_chain(node: ast.AST) -> list[str]:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr.lower())
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id.lower())
    return parts


def find_violations(app_root: Path) -> list[str]:
    violations: list[str] = []
    if not app_root.is_dir():
        raise FileNotFoundError(f"Application source directory not found: {app_root}")

    for source in sorted(app_root.rglob("*.py")):
        relative = source.relative_to(app_root)
        if relative == Path("brokers/upstox/adapter.py"):
            continue  # Defines the low-level HTTP adapter methods.
        if relative == APPROVED_CALLER:
            continue  # Sole production call site, once the boundary is implemented.
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(relative))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(f"{relative}: cannot safely inspect source ({type(exc).__name__})")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or node.attr.lower() not in WRITE_METHODS:
                continue
            chain = _attribute_chain(node.value)
            if not any("adapter" in part or "upstox" in part for part in chain):
                continue
            violations.append(
                f"{relative}:{node.lineno}: unapproved broker-adapter write reference: {node.attr}"
            )
    return violations


def main() -> int:
    app_root = Path(__file__).resolve().parents[1] / "app"
    violations = find_violations(app_root)
    if violations:
        print("Broker-write boundary guard FAILED:")
        print("\n".join(f" - {item}" for item in violations))
        return 1
    print("Broker-write boundary guard passed: no unapproved adapter write references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
