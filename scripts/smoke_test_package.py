from __future__ import annotations

import importlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_test_package.py <import_name>")

    import_name = sys.argv[1]
    importlib.import_module(import_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
