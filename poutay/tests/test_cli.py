import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


