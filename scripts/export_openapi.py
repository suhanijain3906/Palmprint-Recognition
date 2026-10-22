#!/usr/bin/env python3
"""Write the OpenAPI document of a FastAPI app to a JSON file.

Run this with the interpreter that has the dependencies of the service you
want to export. The backend and the ML service have different dependencies,
so use their respective virtual environments.

Examples:
    cd backend
    python ../scripts/export_openapi.py --app app.main:app \
        --output ../shared/api-contracts/backend.openapi.json

    cd ml-service
    python ../scripts/export_openapi.py --app app.main:app \
        --output ../shared/api-contracts/ml-service.openapi.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app",
        default="app.main:app",
        help="import path of the FastAPI application (module:attribute)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openapi.json"),
        help="destination file",
    )
    args = parser.parse_args()

    if ":" not in args.app:
        parser.error("--app must use the form 'module:attribute'")
    module_name, attribute = args.app.split(":", 1)

    sys.path.insert(0, str(Path.cwd()))
    module = importlib.import_module(module_name)
    application = getattr(module, attribute)

    document = application.openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.output} ({len(document.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
