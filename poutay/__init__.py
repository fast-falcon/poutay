"""Poutay package initializer.

This package primarily exposes the command line interface implemented in the
``poutay.py`` module that lives alongside this package in the distribution. The
objects are imported dynamically so that ``import poutay`` provides access to
the same API regardless of whether the module or package is imported first.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_cli_path = Path(__file__).resolve().parent.parent / "poutay.py"
_spec = spec_from_file_location("poutay_cli", _cli_path)
_cli = module_from_spec(_spec)
_spec.loader.exec_module(_cli)

RunCommand = _cli.RunCommand
BuildCommand = _cli.BuildCommand
StartProjectCommand = _cli.StartProjectCommand
StartAppCommand = _cli.StartAppCommand
CreateSvgColorsCommand = _cli.CreateSvgColorsCommand
DesignerCommand = _cli.DesignerCommand
build_parser = _cli.build_parser
main = _cli.main

__all__ = [
    "RunCommand",
    "BuildCommand",
    "StartProjectCommand",
    "StartAppCommand",
    "CreateSvgColorsCommand",
    "DesignerCommand",
    "build_parser",
    "main",
]