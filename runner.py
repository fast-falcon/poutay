"""Application runner used by the CLI."""

import importlib
from poutay.conf import settings


def run():
    """Import and execute the configured start callable."""
    target = getattr(settings, "START", None)
    if not target:
        print("No START defined in settings")
        return

    module_path, attr = target.split(":")
    mod = importlib.import_module(module_path)
    func = getattr(mod, attr)
    func()
