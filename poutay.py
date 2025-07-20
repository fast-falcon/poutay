"""Command line interface for the Poutay framework."""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from conf import settings
import runner
from bootstrap.multi_color_svg import SvgColorBuilder


TEMPLATES_DIR = Path(__file__).parent / "templates"


def cmd_run(args):
    """Run application using runner module."""
    runner.run()


def cmd_build(args):
    """Build standalone executable using PyInstaller."""
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


def copytree(src: Path, dst: Path, name_map=None):
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


def cmd_startproject(args):
    project_dir = Path(args.name)
    template = TEMPLATES_DIR / "project"
    copytree(template, project_dir)
    print(f"Project created at {project_dir}")


def cmd_startapp(args):
    app_dir = Path(args.name)
    template = TEMPLATES_DIR / "app"
    copytree(template, app_dir)
    print(f"App created at {app_dir}")


def cmd_createsvgcolors(args):
    colors = getattr(settings, "SVG_COLORS", {})
    out_dir = getattr(settings, "SVG_COLORS_DIR", "build/svg_colors")
    builder = SvgColorBuilder(colors, out_dir)
    builder.build()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="poutay")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run")
    p_run.set_defaults(func=cmd_run)

    p_build = sub.add_parser("build")
    p_build.add_argument("script", default="manage.py", nargs="?")
    p_build.set_defaults(func=cmd_build)

    p_sp = sub.add_parser("startproject")
    p_sp.add_argument("name")
    p_sp.set_defaults(func=cmd_startproject)

    p_sa = sub.add_parser("startapp")
    p_sa.add_argument("name")
    p_sa.set_defaults(func=cmd_startapp)

    p_svg = sub.add_parser("createsvgcolors")
    p_svg.set_defaults(func=cmd_createsvgcolors)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
