"""Configuration and lazy settings loader."""

import importlib
import os
from types import SimpleNamespace


class Lazy_setting:
    """Load default and project settings lazily."""

    def __init__(self):
        self._wrapped = None

    def _setup(self) -> None:
        if self._wrapped is not None:
            return

        from . import global_settings

        data = {
            key: getattr(global_settings, key)
            for key in dir(global_settings)
            if key.isupper()
        }

        module_path = os.environ.get("poutay_setting")
        if module_path:
            mod = importlib.import_module(module_path)
            data.update({
                key: getattr(mod, key)
                for key in dir(mod)
                if key.isupper()
            })

        self._wrapped = SimpleNamespace(**data)

    def __getattr__(self, item):
        self._setup()
        return getattr(self._wrapped, item)

    def __setattr__(self, key, value):
        if key == "_wrapped":
            super().__setattr__(key, value)
        else:
            self._setup()
            setattr(self._wrapped, key, value)

    def load(self):
        """Force loading settings."""
        self._setup()


settings = Lazy_setting()
