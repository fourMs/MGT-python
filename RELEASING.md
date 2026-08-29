# Releasing

Two rules, both learned from getting them wrong.

## Bump the version in all THREE places, in the same commit

`__version__`, `CITATION.cff` and `docs/releases.md` state the same version, and they are bumped
together. This file said "both places" until 2026-08-23, when a release commit bumped the two it
named and CI went red on five jobs over the third: `docs/releases.md` opens with the current stable
release and `tests/test_release_consistency.py` checks it, along with the newest CHANGELOG heading.
Run that file before tagging and it will name whatever was missed:

    python3 -m pytest tests/test_release_consistency.py -q

`__version__` and `CITATION.cff` are bumped together. Four records
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

## Publish the release only AFTER CI is green on the release commit

`pypi-publish.yml` opens with a job called *Refuse to publish from a commit CI has not passed*,
which reads the CI run for the release commit and stops the build and publish jobs if it is not
already green. `in_progress` counts as not green.

So the order is: push the commit, WAIT for CI, then `gh release create`. Pushing the commit and
creating the release in the same breath fails --- the release exists, the publish run goes red at
its first job, nothing is built, and nothing reaches PyPI. That happened on 2026-08-24 with
1.14.0. The guard did its job; the procedure just did not say so.

The repair is to re-run the failed publish run once CI is green:

    gh run list --limit 1 --workflow='Publish to PyPI' --json databaseId --jq '.[0].databaseId'
    gh run rerun <id>

and then check PyPI, because a green re-run is still not a published version.

## A tag on its own publishes NOTHING

Because the trigger is `release: published`, `git push --tags` runs no workflow at all. No job is
queued, nothing goes red, no mail arrives, and the version simply never reaches PyPI. This is the
quietest failure in the release path and it has already cost real versions: eight micromotion
tags between 0.9.0 and 1.1.0 went out this way and were found only when the tags were compared
against PyPI by hand, ten days later.

So a release is finished when the version is ON PyPI, not when the tag is pushed. Check it:

    pip index versions <package>

and across all four toolboxes at once, from the Still Standing repository:

    python3 deposit/_curation/toolbox_pypi_check.py

which lists every tag that never published and says, for each, whether the release is missing or
whether the release exists and its run failed -- those two want different repairs.

## After the release

A release publishes to PyPI and cannot be undone, so it is deliberate rather than routine.

If this is the first release since the Zenodo GitHub integration was switched on, it will begin a
NEW concept DOI and freeze the old lineage: the integration cannot see a deposition it did not
create. Repoint `CITATION.cff`, the README badge and the docs landing page at the new concept, and
signpost the old record. `deposit/_curation/toolbox_doi_check.py` in the Still Standing project
checks all of this and names what is wrong.

## Two environmental snags, each worth a failed attempt once

`gh` is installed as a snap and cannot read files under `/tmp`, so release notes passed
with `--notes-file` must live somewhere real — the home directory works. And
`gh release create --target` rejects a short SHA; give it the full 40 characters from
`git rev-parse`. When the tag already exists at the right commit, `--target` is not
needed at all.
