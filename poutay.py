"""Command line interface for the Poutay framework."""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from poutay.conf import settings
import runner

TEMPLATES_DIR = Path(__file__).parent / "poutay" / "templates"


class CommandBase:
    """Base class for CLI commands."""

    name: str = ""
    help: str = ""

    @classmethod
    def handler(cls, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(cls.name, help=cls.help)
        cls.add_arguments(parser)
        parser.set_defaults(command=cls())

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Register command specific arguments."""
        pass

    def run(self, args: argparse.Namespace) -> None:  # pragma: no cover - base class
        raise NotImplementedError


class RunCommand(CommandBase):
    name = "run"
    help = "Start the application defined in your settings."

    def run(self, args: argparse.Namespace) -> None:
        runner.run()


class BuildCommand(CommandBase):
    name = "build"
    help = "Create a standalone executable using PyInstaller."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("script", default="manage.py", nargs="?")

    def run(self, args: argparse.Namespace) -> None:
        target = Path(args.script)
        build_dir = Path("build")
        build_dir.mkdir(exist_ok=True)
        subprocess.run([
            "pyinstaller",
            "--onefile",
            str(target),
            "--distpath",
            str(build_dir),
            "-y",
        ], check=True)


class StartProjectCommand(CommandBase):
    name = "startproject"
    help = "Generate a new project skeleton."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name")

    def run(self, args: argparse.Namespace) -> None:
        project_dir = Path(args.name)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)
        template = TEMPLATES_DIR / "project"
        print(template)
        print(project_dir)
        copytree(template, project_dir)
        print(f"Project created at {project_dir}")


class StartAppCommand(CommandBase):
    name = "startapp"
    help = "Create a new application skeleton."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name")

    def run(self, args: argparse.Namespace) -> None:
        app_dir = Path(args.name)
        if not os.path.exists(app_dir):
            os.makedirs(app_dir, exist_ok=True)
        template = TEMPLATES_DIR / "app"
        copytree(template, app_dir)
        print(f"App created at {app_dir}")


class CreateSvgColorsCommand(CommandBase):
    name = "createsvgcolors"
    help = "Build colored SVG resources."

    def run(self, args: argparse.Namespace) -> None:
        from bootstrap.multi_color_svg import SvgColorBuilder

        colors = getattr(settings, "SVG_COLORS", {})
        out_dir = getattr(settings, "SVG_COLORS_DIR", "build/svg_colors")
        builder = SvgColorBuilder(colors, out_dir)
        builder.build()


class DesignerCommand(CommandBase):
    name = "designer"
    help = "Launch Qt Designer (pyside6-designer)."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("ui_file", nargs="?", help="Optional .ui file to open")

    def run(self, args: argparse.Namespace) -> None:
        cmd = ["pyside6-designer"]
        if args.ui_file:
            cmd.append(args.ui_file)
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            print("pyside6-designer not found. Please install PySide6.")


COMMANDS = [
    RunCommand,
    BuildCommand,
    StartProjectCommand,
    StartAppCommand,
    CreateSvgColorsCommand,
    DesignerCommand,
]


def copytree(src: Path, dst: Path, name_map=None) -> None:
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_root = dst / rel
        target_root.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_file = Path(root) / f
            dst_file = target_root / f
            if name_map and src_file.name in name_map:
                dst_file = target_root / name_map[src_file.name]
            shutil.copy2(src_file, dst_file)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="poutay")
    sub = parser.add_subparsers(dest="command")
    for cmd in COMMANDS:
        cmd.handler(sub)
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "command"):
        args.command.run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
