"""Setup clipy package"""

import os

import setuptools


def read(fname: str):
    """Helper function to read files"""
    return open(os.path.join(os.path.dirname(__file__), fname), "r", encoding="utf-8").read()


setuptools.setup(
    name="clipy",
    version="0.2.0",
    description="A command line interface package.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="cli",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src", exclude=["tests", "tests.*"]),
    install_requires=[],
    # entry_points={"console_scripts": ["clipy=clipy.cli:main"]},
)
