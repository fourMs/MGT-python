"""Time-axis labelling on audio figures, and the warnings filter that hid its bugs.

`musicalgestures/_audio.py` used to call a bare `warnings.filterwarnings("ignore")`
at import, silencing every warning in the process. Among the things it silenced
was matplotlib telling this package that `format_time` paired a `FixedFormatter`
with a `LinearLocator`, so the labels were not guaranteed to land on the ticks
they describe. Removing the blanket filter surfaced that, and two further bugs in
the same twelve lines: labels were assigned into a float array, which crashed on
files over an hour and silently mangled whole-minute labels on shorter ones.
"""
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from musicalgestures._audio import MgAudio


class _Bare(MgAudio):
    """An MgAudio without a file behind it: format_time only needs the duration."""

    def __init__(self):
        pass


def _labels_for(duration, xlim=(0.0, 1.0)):
    fig, ax = plt.subplots()
    ax.set_xlim(*xlim)
    _Bare().format_time(ax, original_duration=duration)
    fig.canvas.draw()
    out = [t.get_text() for t in ax.xaxis.get_majorticklabels()]
    positions = list(ax.xaxis.get_majorticklocs())
    plt.close(fig)
    return out, positions


class TestTheFilterIsNarrow:
    def test_the_package_does_not_silence_warnings_globally(self):
        """A bare filter here would swallow warnings from user code too."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warnings.warn("from the user's own code", UserWarning)
        assert caught, "musicalgestures has silenced warnings process-wide"

    def test_deprecation_warnings_still_reach_the_caller(self):
        """The deprecated attribute aliases are worthless if nobody sees them."""
        import musicalgestures as mg

        v = mg.MgVideo.__new__(mg.MgVideo)
        v.motiongram_vertical_image = "x"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _ = v.motiongram_x
        assert any(issubclass(c.category, DeprecationWarning) for c in caught)


class TestLabelsLandOnTicks:
    def test_no_locator_formatter_mismatch_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _labels_for(120.0)
        assert not [c for c in caught if "FixedFormatter" in str(c.message)]

    def test_one_label_per_tick(self):
        labels, positions = _labels_for(120.0)
        assert len(labels) == len(positions) == 10

    def test_ticks_sit_inside_the_axis_not_at_the_label_values(self):
        """Axis is decoded seconds, labels are original time; they differ when
        frames were skipped, which is the case this method exists for."""
        _, positions = _labels_for(3000.0, xlim=(0.0, 10.0))
        assert min(positions) == pytest.approx(0.0)
        assert max(positions) == pytest.approx(10.0)


class TestLabelFormatting:
    def test_a_whole_minute_keeps_both_second_digits(self):
        """The float round-trip turned '10.00' into 10.0 and displayed '10:0'.

        The last tick sits on the duration itself, so a round duration puts a
        whole minute in the labels without having to hunt for one."""
        labels, _ = _labels_for(600.0)
        assert labels[-1] == "10:00"

    def test_files_over_an_hour_do_not_crash(self):
        """Assigning '0.13.20' into a float array raised ValueError."""
        labels, _ = _labels_for(7200.0)
        assert labels[0] == "0:00:00"
        assert labels[-1] == "2:00:00"

    def test_short_files_are_labelled_in_seconds(self):
        labels, _ = _labels_for(30.0)
        assert labels[0] == "0.0"
        assert labels[-1] == "30.0"

    def test_every_label_is_well_formed(self):
        """No label may lose a digit on the way through, at any scale."""
        import re

        for duration, pattern in ((45.0, r"^\d+\.\d$"),
                                  (600.0, r"^\d+:\d\d$"),
                                  (7200.0, r"^\d+:\d\d:\d\d$")):
            labels, _ = _labels_for(duration)
            bad = [l for l in labels if not re.match(pattern, l)]
            assert not bad, f"malformed labels at {duration}s: {bad}"
