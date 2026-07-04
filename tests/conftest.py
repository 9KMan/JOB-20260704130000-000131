"""Shared pytest fixtures."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Locate the repo root (one level up from the tests/ dir)."""
    # tests/conftest.py -> parent is tests -> parent is repo
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def tmp_repo():
    """Yield a fresh temp dir; cleaned up after the test."""
    d = tempfile.mkdtemp(prefix="lovable-audit-")
    try:
        yield Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="session")
def has_git():
    return shutil.which("git") is not None
