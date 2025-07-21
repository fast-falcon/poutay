"""Entry point for ``python -m poutay``.

This module proxies execution to the CLI implementation defined in the
``poutay.py`` module located alongside this package.
"""
from importlib import import_module
from pathlib import Path
import runpy


def main() -> None:
    # Resolve path to the CLI module installed as ``poutay.py`` next to this
    # package and execute it as a script. This mirrors the behaviour of the
    # ``poutay`` console script defined in ``setup.py``.
    module_path = Path(__file__).resolve().parent.parent / "poutay.py"
    runpy.run_path(str(module_path), run_name="__main__")


if __name__ == "__main__":
    main()
