#!/usr/bin/env python3
"""Pre-flight check for the Palmprint Research Platform.

Verifies the local toolchain, Python dependencies and configuration files.
Docker is reported as optional because the application can also be run
directly with uvicorn + Vite.

Usage:
    python scripts/check_environment.py
    python scripts/check_environment.py --strict   # Docker becomes required
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PYTHON = (3, 11)
BACKEND_MODULES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "httpx",
    "reportlab",
]
ML_MODULES = [
    "fastapi",
    "uvicorn",
    "numpy",
    "cv2",
    "PIL",
    "skimage",
    "sklearn",
    "scipy",
]
FRONTEND_FILES = ["package.json", "vite.config.ts", "src/main.tsx"]
CONFIG_FILES = [".env.example", "docker-compose.yml", "backend/alembic.ini"]


def _status(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def check_python() -> bool:
    return sys.version_info >= REQUIRED_PYTHON


def check_modules(names: list[str]) -> list[tuple[str, bool]]:
    results = []
    for name in names:
        try:
            importlib.import_module(name)
            results.append((name, True))
        except Exception:  # noqa: BLE001 - any import failure means "missing"
            results.append((name, False))
    return results


def check_ports(ports: dict[int, str]) -> list[tuple[int, str, bool]]:
    results = []
    for port, label in ports.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            in_use = sock.connect_ex(("127.0.0.1", port)) == 0
        results.append((port, label, in_use))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="require Docker")
    args = parser.parse_args()

    failures: list[str] = []

    print("Palmprint Research Platform - environment check")
    print("=" * 52)

    py_ok = check_python()
    print(
        f"[{_status(py_ok)}] Python >= {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]} (found {sys.version.split()[0]})"
    )
    if not py_ok:
        failures.append("Python version")

    for label, modules in (("backend", BACKEND_MODULES), ("ml-service", ML_MODULES)):
        print(f"\n{label} Python packages:")
        for name, ok in check_modules(modules):
            print(f"  [{_status(ok)}] {name}")
            if not ok:
                failures.append(f"{label}:{name}")

    node = shutil.which("node")
    npm = shutil.which("npm")
    print(f"\n[{'OK' if node else 'MISSING'}] Node.js ({node or 'not found'})")
    print(f"[{'OK' if npm else 'MISSING'}] npm ({npm or 'not found'})")
    if not node or not npm:
        failures.append("Node.js/npm")

    frontend_ok = all((ROOT / "frontend" / item).exists() for item in FRONTEND_FILES)
    print(f"[{_status(frontend_ok)}] frontend sources")
    if not frontend_ok:
        failures.append("frontend sources")

    config_ok = all((ROOT / item).exists() for item in CONFIG_FILES)
    print(f"[{_status(config_ok)}] configuration files")
    if not config_ok:
        failures.append("configuration files")

    env_file = ROOT / ".env"
    print(
        f"[{'OK' if env_file.exists() else 'OPTIONAL'}] .env (copy .env.example to .env)"
    )

    docker = shutil.which("docker")
    docker_ok = bool(docker)
    print(f"[{'OK' if docker_ok else 'OPTIONAL'}] Docker ({docker or 'not installed'})")
    if args.strict and not docker_ok:
        failures.append("Docker")

    print("\nPort usage (a free port is required before starting a service):")
    for port, label, in_use in check_ports(
        {8000: "backend", 8001: "ml-service", 5173: "frontend", 5432: "postgres"}
    ):
        print(f"  [{'IN USE' if in_use else 'FREE'}] {port} ({label})")

    print()
    if failures:
        print("FAILED checks: " + ", ".join(sorted(set(failures))))
        print("Install the missing pieces or activate the correct virtual environment.")
        return 1

    print("All required checks passed.")
    if not docker_ok:
        print(
            "Docker is not installed; local uvicorn + Vite development is still possible."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
