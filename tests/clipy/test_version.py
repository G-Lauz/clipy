import importlib

import clipy


def test_version_match():
    assert clipy.__version__ == importlib.metadata.version("clipyx")
