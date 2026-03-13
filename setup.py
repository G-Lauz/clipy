"""Setup clipy package"""

import os

import setuptools


def read(fname: str):
    """Helper function to read files"""
    with open(os.path.join(os.path.dirname(__file__), fname), "r", encoding="utf-8") as file:
        return file.read()


setuptools.setup(
    name="clipy",
    version=read("VERSION").strip(),
    description="Python package for creating command-line interfaces in a pythonic way.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="cli",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src", exclude=["tests", "tests.*"]),
    install_requires=[],
)
