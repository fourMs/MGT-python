# Contributing to MGT-python

Thank you for your interest in contributing to the Musical Gestures Toolbox for Python!

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Style](#code-style)
3. [Type Hints](#type-hints)
4. [Tests](#tests)
5. [Documentation](#documentation)
6. [Pull Request Workflow](#pull-request-workflow)
7. [Adding New Features](#adding-new-features)

---

## Development Setup

### Prerequisites

- Python ≥ 3.10
- [FFmpeg](https://ffmpeg.org/download.html) must be on your `PATH`
- Git

### Quick start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/MGT-python.git
cd MGT-python

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode with development dependencies
pip install -e ".[dev]"

# 4. Verify the installation
python -c "import musicalgestures; print('OK')"
```

### Using nox (recommended)

[nox](https://nox.thea.codes) provides isolated, reproducible sessions:

```bash
pip install nox          # one-time install
nox -s tests             # run the test suite on Python 3.12
nox -s lint              # ruff linting + format check
nox -s typecheck         # mypy type checking
nox -s coverage          # pytest + coverage report
nox -l                   # list all available sessions
```

---

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.
Run checks before committing:

```bash
ruff check musicalgestures/
ruff format musicalgestures/
```

Key conventions:

- **Line length**: 100 characters.
- **Imports**: standard library first, then third-party, then local. One import per line.
- **Strings**: double quotes for docstrings; prefer single quotes for non-docstring strings.
- **Logging**: use `logging.getLogger(__name__)` inside modules; never use bare `print()` for library output.
- **Progress bars**: use `tqdm` or the existing `MgProgressbar` wrapper.

---

## Type Hints

All new code **must** include type annotations (PEP 484/526).

```python
from __future__ import annotations

def compute_qom(frame: np.ndarray, threshold: float = 0.05) -> float:
    ...
```

Check annotations with mypy:

```bash
mypy musicalgestures/ --ignore-missing-imports
```

---

## Tests

Tests live in `tests/` and are run with pytest.

```bash
pytest tests/ -v             # run all tests
pytest tests/ -k "motion"   # run tests matching "motion"
pytest tests/ --cov=musicalgestures --cov-report=term-missing
```

### Writing tests

- Add a new test file `tests/test_<feature>.py`.
- Use `pytest.fixture` for shared resources.
- Assert on **array shapes**, **file existence**, and **return types** – not just that code runs without error.
- Mark slow tests with `@pytest.mark.slow` and skip in fast CI runs.

Example:

```python
import numpy as np
import pytest
from musicalgestures._features import MgFeatures


def test_mgfeatures_shape():
    feat = MgFeatures({"qom": np.array([1.0, 2.0, 3.0])}, sr=25.0)
    assert feat.shape == (1, 3)
    assert feat.to_numpy().shape == (1, 3)


def test_mgfeatures_round_trip(tmp_path):
    feat = MgFeatures({"a": np.arange(5.0), "b": np.ones(5)}, sr=10.0)
    p = tmp_path / "feat.json"
    feat.to_json(p)
    feat2 = MgFeatures.from_json(p)
    np.testing.assert_array_equal(feat["a"], feat2["a"])
```

---

## Documentation

Docs are built with [MkDocs](https://www.mkdocs.org/):

```bash
pip install mkdocs mkdocs-material
mkdocs serve          # live preview at http://127.0.0.1:8000
mkdocs build --clean  # build static site in site/
```

### Regenerating the API reference

The API-reference pages under `docs/musicalgestures/` and `docs/MODULES.md` are auto-generated
from the source docstrings with [handsdown](https://pypi.org/project/handsdown/) and committed to
the repo. Regenerate them whenever the public API changes:

```bash
pip install "handsdown==1.1.0" "setuptools<81"   # 1.1.0 matches the committed format
./scripts/regenerate_api_docs.sh
```

The script only rewrites the auto-generated stubs — the hand-written pages (`index.md`, `README.md`,
`quickstart.md`, `installation.md`, `user-guide/*`, `releases.md`) are left untouched.

### Docstring style

Use NumPy-style docstrings consistently:

```python
def my_function(x: np.ndarray, threshold: float = 0.5) -> float:
    """One-line summary.

    Extended description (optional).

    Parameters
    ----------
    x:
        Input array.
    threshold:
        Value between 0 and 1. Default: 0.5.

    Returns
    -------
    float
        The result.

    Examples
    --------
    >>> my_function(np.array([1, 2, 3]), threshold=0.3)
    2.0
    """
```

---

## Pull Request Workflow

1. **Branch** off `master`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make focused commits** – one logical change per commit. Use conventional commits format:
   ```
   feat: add MgFeatures.to_zarr() method
   fix: handle empty video in MgVideoReader
   docs: update CONTRIBUTING.md
   ```

3. **Run all checks** before pushing:
   ```bash
   nox -s lint tests
   ```

4. **Open a Pull Request** against `master` and fill in the PR template.
   - Describe what changed and why.
   - Reference any related issues.
   - Add or update tests.

5. **CI must pass** before merging.

---

## Adding New Features

### Adding a new analysis method

1. Create `musicalgestures/_myfeature.py` with a standalone function.
2. Import it in `musicalgestures/_video.py` via the `from ... import ... as ...` pattern used by existing methods.
3. Export it from `musicalgestures/__init__.py` if it is a public class or function.
4. Add a test in `tests/test_myfeature.py`.
5. Document it in `docs/`.

### Adding a new enum value

Add the value to the appropriate class in `musicalgestures/_enums.py`. Enum members support case-insensitive string construction, so no existing code will break.

### Adding a new optional dependency

1. Add it to the appropriate extras group in `pyproject.toml`.
2. Guard the import with `try / except ImportError` and raise `MgDependencyError` with a helpful message.
3. Document the install command in the docstring.
