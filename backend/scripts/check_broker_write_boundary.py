"""Fail CI if production app code bypasses the approved broker-write boundary.

The AST scanner rejects every production attribute reference to place/modify/
cancel methods, regardless of receiver variable name. The only exception is
the known PAPER strategy-to-ExecutionService.place_order call. Low-level method
definitions in the Upstox adapter are allowed; the central live write service
must not call an adapter until a later reviewed implementation. Dynamic
dispatch/reflection cannot be fully proven safe by this source guard alone.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

WRITE_METHODS = {"place_order", "modify_order", "cancel_order"}
PAPER_EXECUTION_CALLER = Path("services/strategy_execution_service.py")


def _is_approved_paper_execution_call(relative: Path, node: ast.Attribute, chain: list[str]) -> bool:
    # Strategy entry/exit orchestration delegates to the PAPER execution service.
    if (
        relative == PAPER_EXECUTION_CALLER
        and node.attr.lower() == "place_order"
        and chain == ["execution", "self"]
    ):
        return True

    # Existing HTTP order endpoints delegate to ExecutionService, which rejects
    # non-PAPER mode and never calls broker order-write methods.
    if (
        relative == Path("api/v1/portfolios.py")
        and node.attr.lower() in {"place_order", "cancel_order"}
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "ExecutionService"
    ):
        return True
    return False


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
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(relative))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(f"{relative}: cannot safely inspect source ({type(exc).__name__})")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or node.attr.lower() not in WRITE_METHODS:
                continue
            chain = _attribute_chain(node.value)
            if _is_approved_paper_execution_call(relative, node, chain):
                continue
            violations.append(
                f"{relative}:{node.lineno}: unapproved broker-write reference: {node.attr}"
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
