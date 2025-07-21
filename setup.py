from setuptools import setup, find_packages

setup(
    name="poutay",
    version="0.2.0",
    packages=find_packages(),
    py_modules=["poutay", "runner"],
    include_package_data=True,
    package_data={
        "poutay": ["templates/**/*", "assets/**/*", "*.py"]
    },
    install_requires=[
        "PySide6",
        "cryptography",
        "bcrypt",
        "beautifulsoup4",
    ],
    entry_points={
        "console_scripts": ["poutay=poutay:main"],
    },
)
