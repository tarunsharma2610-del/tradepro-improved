"""Fail CI if production app code bypasses the approved broker-write boundary.

The guard intentionally scans application sources, not adapter definitions or
tests. Once implemented, only app/services/live_broker_write_service.py may
reference adapter place/modify/cancel methods. Keep this allowlist exact and
reviewed; do not widen it to routes, workers, recovery, or generic services.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WRITE_METHODS = ("place_order", "modify_order", "cancel_order")
APPROVED_CALLER = Path("services/live_broker_write_service.py")
METHOD_REFERENCE = re.compile(r"\.\s*(" + "|".join(WRITE_METHODS) + r")\b")


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
            contents = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            violations.append(f"{relative}: cannot inspect source ({type(exc).__name__})")
            continue
        for line_number, line in enumerate(contents.splitlines(), start=1):
            if METHOD_REFERENCE.search(line):
                methods = sorted({m.group(1) for m in METHOD_REFERENCE.finditer(line)})
                violations.append(f"{relative}:{line_number}: unapproved broker-write reference: {', '.join(methods)}")
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
