# Releasing

Two rules, both learned from getting them wrong.

## Bump the version in both places, in the same commit

`__version__` and `CITATION.cff` state the same version, and they are bumped together. Four records
in this project's sibling deposit once stated two different versions about themselves because one
file was edited and the other was not.

## Tag WITHOUT a leading `v`

Tag `1.2.3`, not `v1.2.3`.

The Zenodo GitHub integration builds the archived record from `CITATION.cff` -- authors, ORCIDs,
licence, keywords and abstract all come out right -- with one exception: it takes `version` from the
TAG NAME. A `v`-prefixed tag therefore produces a record stating `v1.2.3` where the citation file,
the package and every hand-made deposit state `1.2.3`, so one toolbox reads two ways in a reference
list. Ten records had to be corrected by hand on 2026-08-16 for this.

Nothing in CI depends on the prefix: `pypi-publish.yml` triggers on `release: published`, not on a
tag pattern. Tags made before 2026-08-16 keep their `v` and are left alone.

## After the release

A release publishes to PyPI and cannot be undone, so it is deliberate rather than routine.

If this is the first release since the Zenodo GitHub integration was switched on, it will begin a
NEW concept DOI and freeze the old lineage: the integration cannot see a deposition it did not
create. Repoint `CITATION.cff`, the README badge and the docs landing page at the new concept, and
signpost the old record. `deposit/_curation/toolbox_doi_check.py` in the Still Standing project
checks all of this and names what is wrong.
