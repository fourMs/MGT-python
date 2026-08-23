"""One deprecation-alias helper, so eleven renames cannot diverge eleven ways."""
import pytest

from musicalgestures._utils import deprecated_alias


class Host:
    old_name = deprecated_alias("old_name", "new_name")


def test_reading_the_alias_reads_the_canonical_attribute():
    h = Host()
    h.new_name = "sentinel"
    with pytest.warns(DeprecationWarning, match="use new_name"):
        assert h.old_name == "sentinel"


def test_writing_the_alias_writes_the_canonical_attribute():
    h = Host()
    with pytest.warns(DeprecationWarning, match="use new_name"):
        h.old_name = "sentinel"
    assert h.new_name == "sentinel"
    assert "new_name" in h.__dict__
    assert "old_name" not in h.__dict__


def test_the_alias_tracks_later_reassignment():
    h = Host()
    with pytest.warns(DeprecationWarning):
        h.old_name = "first"
    h.new_name = "second"
    with pytest.warns(DeprecationWarning):
        assert h.old_name == "second"


def test_deleting_through_the_alias():
    h = Host()
    h.new_name = "sentinel"
    with pytest.warns(DeprecationWarning):
        del h.old_name
    assert not hasattr(h, "new_name")


def test_unset_reports_the_name_that_was_asked_for():
    """hasattr(h, 'old_name') must be False, not raise about new_name."""
    h = Host()
    with pytest.warns(DeprecationWarning):
        with pytest.raises(AttributeError, match="old_name"):
            h.old_name


def test_the_warning_names_the_removal_version():
    h = Host()
    h.new_name = "x"
    with pytest.warns(DeprecationWarning, match="2.0"):
        h.old_name
