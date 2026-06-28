#!/usr/bin/env bash
#
# Regenerate the auto-generated API-reference stubs under docs/musicalgestures/ and docs/MODULES.md
# from the source docstrings, using handsdown.
#
# These pages are committed to the repo (the docs site builds them with mkdocs), so they must be
# regenerated whenever the public API changes. The hand-written docs (docs/index.md, docs/README.md,
# docs/quickstart.md, docs/installation.md, docs/user-guide/*, docs/releases.md) are NOT touched.
#
# Requirements (handsdown 1.1.0 matches the committed format — blob/master, "[[find in source code]]"):
#   pip install "handsdown==1.1.0" "setuptools<81"
# (setuptools<81 is needed because handsdown 1.1.0 imports the deprecated pkg_resources.)
#
# Usage:
#   ./scripts/regenerate_api_docs.sh
#
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_URL="https://github.com/fourMs/MGT-python/"
TMP="$(mktemp -d)"

handsdown -o "$TMP" --external "$REPO_URL" --branch master musicalgestures

# Copy only the auto-generated API reference (module stubs + the Complete Reference index).
cp "$TMP"/musicalgestures/*.md docs/musicalgestures/
cp "$TMP"/MODULES.md docs/MODULES.md

rm -rf "$TMP"
echo "Regenerated docs/musicalgestures/*.md and docs/MODULES.md."
echo "Hand-written docs (docs/index.md, docs/README.md, user-guide/, …) were left untouched."
