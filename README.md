# Poutay

Poutay is a lightweight desktop framework inspired by Django. It provides a simple
command line interface to create projects and applications, build executables and
generate colored SVG assets.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the CLI directly:

```bash
python poutay.py run
```

Available commands:

- `run` – start the application defined in your settings.
- `build` – create a standalone executable using PyInstaller.
- `startproject NAME` – generate a new project skeleton.
- `startapp NAME` – create a new application skeleton.
- `createsvgcolors` – build colored SVG resources.

Configuration is handled via the `poutay_setting` environment variable which
should contain the import path to a settings module. When not set, defaults from
`conf.global_settings` are used.
