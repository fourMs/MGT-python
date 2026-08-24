"""The version must say the same thing in every place that states it.

WHY THIS EXISTS. Releasing 1.11.4 on 2026-08-22 turned up two silent
inconsistencies that nothing had caught:

  - `docs/releases.md` announced "the current stable release is 1.8.0" while
    PyPI had been serving 1.11.3. Four versions of drift in a page whose whole
    job is to say what the current release is.
  - 1.11.3 was published to PyPI with no git tag, so the changelog's compare
    link for it could not resolve. It was tagged retroactively at the commit
    that set its version. (Reading `git tag | tail` suggests a worse gap than
    there is: that sorts lexicographically, so v1.10.0 and v1.11.x come BEFORE
    v1.9.x. Use --sort=v:refname.)

Neither breaks an install, which is why neither was noticed. These tests make
the next drift fail in CI instead of on a reader.
"""
import os
import re
import subprocess

import pytest

import musicalgestures

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _changelog_versions():
    txt = open(os.path.join(HERE, "CHANGELOG.md"), encoding="utf-8").read()
    return re.findall(r"^## \[(\d+\.\d+\.\d+)\]", txt, re.M)


class Test_ReleaseConsistency:
    def test_changelog_has_an_entry_for_this_version(self):
        vs = _changelog_versions()
        assert musicalgestures.__version__ in vs, (
            f"__version__ is {musicalgestures.__version__} and the changelog's versions are "
            f"{vs[:5]}. Add the entry, or the release notes will not describe what was released.")

    def test_changelog_newest_entry_is_this_version(self):
        vs = _changelog_versions()
        assert vs and vs[0] == musicalgestures.__version__, (
            f"the newest changelog entry is {vs[0] if vs else None}, not "
            f"{musicalgestures.__version__}")

    def test_releases_page_states_this_version(self):
        p = os.path.join(HERE, "docs", "releases.md")
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"current stable release is \*\*MGT-python (\d+\.\d+\.\d+)\*\*", txt)
        assert m, "docs/releases.md no longer states a current stable release"
        assert m.group(1) == musicalgestures.__version__, (
            f"docs/releases.md says {m.group(1)}, __version__ says "
            f"{musicalgestures.__version__}. This page drifted four versions behind PyPI once.")

    def test_every_changelog_version_has_a_tag(self):
        """A compare link to a tag that does not exist is a dead link."""
        try:
            tags = set(subprocess.run(["git", "tag"], cwd=HERE, capture_output=True,
                                      text=True, timeout=30).stdout.split())
        except Exception:                                    # noqa: BLE001
            pytest.skip("git not available")
        if not tags:
            pytest.skip("no tags in this checkout")
        # the version being prepared has no tag until it is released
        #
        # BOTH TAG CONVENTIONS COUNT. This project tagged `v1.2.3` until
        # 2026-08-16 and `1.2.3` after it, because the Zenodo integration takes
        # a record's version from the tag name and a `v` made one toolbox read
        # two ways in a reference list. RELEASING.md carries the reason. A
        # check that knows only the old form passes for exactly as long as the
        # newest release is the one it skips: 1.13.0 was tagged bare on
        # 2026-08-23 and this test went red the moment 1.14.0 was prepared
        # above it, blaming a release that was correctly tagged.
        missing = [v for v in _changelog_versions()[1:]
                   if f"v{v}" not in tags and v not in tags]
        assert not missing, (
            "released versions with no git tag, so their changelog compare links are dead: "
            + ", ".join(missing))
