"""The package version has one source, and the build reads it from there.

This package exposed no ``__version__`` at all: the number lived only in
``pyproject.toml``, so code could not ask the package what it was without
going through the installed metadata. Adding the attribute creates the
second copy that drifts, unless the build reads it rather than repeating
it. Across these toolboxes the drift has already happened twice --
ambiscape shipped three releases reporting a version other than their own,
and musiscape shipped one -- so the number is single-sourced here from the
start.

Anything citing a toolbox by version -- a report, a deposit, a methods
section -- is otherwise citing a number the installed package will not
confirm, which makes the drift a correctness problem rather than a
cosmetic one.

The checks read ``pyproject.toml`` with a small section scanner rather
than a TOML parser, because ``tomllib`` is standard only from Python 3.11
and this package supports 3.10. What is needed here is whether a key is
present in a section, which does not warrant a dependency.
"""
import re
from pathlib import Path

import pytest

import musicalgestures

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# Running against an installed wheel rather than a checkout: there is no
# pyproject.toml to inspect and nothing here applies.
pytestmark = pytest.mark.skipif(not PYPROJECT.exists(),
                                reason="no pyproject.toml (installed package)")


def _section(name: str) -> list[str]:
    """Non-comment, non-blank lines of one top-level ``[section]``."""
    out, inside = [], False
    for raw in PYPROJECT.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            inside = line == f"[{name}]"
            continue
        if inside and line and not line.startswith("#"):
            out.append(line)
    return out


def _value(section: str, key: str) -> str | None:
    for line in _section(section):
        m = re.match(rf"{re.escape(key)}\s*=\s*(.+)$", line)
        if m:
            return m.group(1).strip()
    return None


def test_package_exposes_a_version():
    assert hasattr(musicalgestures, "__version__"), \
        "musicalgestures should expose __version__"
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[.-]?\w+)?",
                        musicalgestures.__version__), \
        f"__version__ is not a version string: {musicalgestures.__version__!r}"


def test_pyproject_declares_no_second_version():
    """A static version in pyproject.toml is the second copy that drifts."""
    assert _value("project", "version") is None, (
        "pyproject.toml carries its own version again. It must stay dynamic, "
        "or the two numbers will drift as they did in the sibling toolboxes."
    )
    dynamic = _value("project", "dynamic") or ""
    assert "version" in dynamic, \
        "pyproject.toml should declare version in [project].dynamic"


def test_build_reads_the_module_attribute():
    attr = _value("tool.setuptools.dynamic", "version") or ""
    assert "musicalgestures.__version__" in attr, (
        f"the build resolves the version from {attr!r}; it should read "
        "musicalgestures.__version__ so there is exactly one place to edit"
    )


def test_setuptools_resolves_the_declared_version():
    """The number the build would package equals the one the module reports.

    setuptools is a build-time dependency and is absent from a plain
    runtime environment, so this cross-check skips rather than fails where
    it is not installed. The three checks above need no imports and carry
    the guard on their own.
    """
    try:
        from setuptools.config.pyprojecttoml import read_configuration
    except ImportError:
        pytest.skip("setuptools is a build-time dependency and is not "
                    "installed in this environment")

    resolved = read_configuration(str(PYPROJECT))["project"].get("version")
    assert resolved == musicalgestures.__version__, (
        f"build would package {resolved!r} while the module reports "
        f"{musicalgestures.__version__!r}"
    )
