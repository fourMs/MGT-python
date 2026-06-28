"""Nox sessions for MGT-python development."""
from __future__ import annotations

import nox

nox.options.sessions = ["tests", "lint"]
PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest."""
    session.install("-e", ".[dev]")
    session.run("pytest", "tests/", "--tb=short", "-q", *session.posargs)


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run ruff linter and formatter check."""
    session.install("ruff")
    session.run("ruff", "check", "musicalgestures/", "--ignore", "E501")
    session.run("ruff", "format", "--check", "musicalgestures/", success_codes=[0, 1])


@nox.session(python="3.12")
def typecheck(session: nox.Session) -> None:
    """Run mypy type checker."""
    session.install("-e", ".[dev]")
    # follow_imports/exclude/ignore_missing_imports come from [tool.mypy] in pyproject.toml.
    session.run("mypy", "musicalgestures/")


@nox.session(python="3.12")
def coverage(session: nox.Session) -> None:
    """Run tests with coverage reporting."""
    session.install("-e", ".[dev]")
    session.install("pytest-cov")
    session.run(
        "pytest",
        "tests/",
        "--cov=musicalgestures",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--tb=short",
        "-q",
        *session.posargs,
    )
