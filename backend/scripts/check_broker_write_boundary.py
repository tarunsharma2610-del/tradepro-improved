"""Fail CI if production app code bypasses the approved broker-write boundary.

The AST scanner rejects production attribute references to place/modify/cancel
methods, regardless of receiver variable name. It also rejects literal-name
getattr dispatch to those methods, which would otherwise evade attribute-only
inspection. Exceptions are limited to known PAPER execution calls.
Adapter method definitions are not attribute references and need no file-wide
exemption. Arbitrary reflection or dynamically computed method names cannot be
fully proven safe by a static scanner; keep the reviewed call graph explicit.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

WRITE_METHODS = {"place_order", "modify_order", "cancel_order"}
PAPER_EXECUTION_CALLER = Path("services/strategy_execution_service.py")
PAPER_PORTFOLIO_ENDPOINTS = Path("api/v1/portfolios.py")


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = parents.get(current)
    return None


def _is_approved_paper_execution_call(
    relative: Path, node: ast.Attribute, chain: list[str], function_name: str | None
) -> bool:
    if (
        relative == PAPER_EXECUTION_CALLER
        and node.attr.lower() == "place_order"
        and chain == ["execution", "self"]
    ):
        return True

    if relative == PAPER_PORTFOLIO_ENDPOINTS:
        if (
            function_name == "place_order"
            and node.attr.lower() == "place_order"
            and chain == ["service"]
        ):
            return True
        if (
            function_name == "cancel_order"
            and node.attr.lower() == "cancel_order"
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
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(relative))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(f"{relative}: cannot safely inspect source ({type(exc).__name__})")
            continue
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.lower() in WRITE_METHODS:
                chain = _attribute_chain(node.value)
                function_name = _enclosing_function(node, parents)
                if _is_approved_paper_execution_call(relative, node, chain, function_name):
                    continue
                violations.append(
                    f"{relative}:{node.lineno}: unapproved broker-write reference: {node.attr}"
                )
                continue

            # Catch the common reflection escape hatch: getattr(adapter, "place_order").
            # Only literal method names are decidable here; computed names remain a
            # documented static-analysis limitation rather than being silently allowed.
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
                and node.args[1].value.lower() in WRITE_METHODS
            ):
                violations.append(
                    f"{relative}:{node.lineno}: dynamic broker-write dispatch via getattr: "
                    f"{node.args[1].value}"
                )
    return violations


def main() -> int:
    app_root = Path(__file__).resolve().parents[1] / "app"
    violations = find_violations(app_root)
    if violations:
        print("Broker-write boundary guard FAILED:")
        print("\\n".join(f" - {item}" for item in violations))
        return 1
    print("Broker-write boundary guard passed: no unapproved broker-write references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
