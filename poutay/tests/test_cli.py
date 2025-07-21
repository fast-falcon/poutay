import sys
from pathlib import Path
from unittest import mock
import subprocess

# Ensure the project root is on the path so that ``import poutay`` resolves to
# the CLI module defined at the repository root rather than the ``poutay``
# package directory. ``parents[2]`` points to the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import poutay
from poutay import (
    RunCommand,
    BuildCommand,
    StartProjectCommand,
    StartAppCommand,
    CreateSvgColorsCommand,
    DesignerCommand,
)


def test_build_parser_returns_command_instances():
    parser = poutay.build_parser()
    args = parser.parse_args(["run"])
    assert isinstance(args.command, RunCommand)
    args = parser.parse_args(["designer"])
    assert isinstance(args.command, DesignerCommand)


def test_designer_run_handles_missing_executable():
    parser = poutay.build_parser()
    args = parser.parse_args(["designer"])
    with mock.patch("subprocess.run", side_effect=FileNotFoundError) as mock_run:
        args.command.run(args)
        mock_run.assert_called_once()


def test_module_execution_via_dash_m(tmp_path):
    """Ensure ``python -m poutay`` executes without error."""
    result = subprocess.run(
        [sys.executable, "-m", "poutay", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()


