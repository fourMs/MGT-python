"""A Flow holds its video by weak reference, so it can outlive it.

`MgVideo` keeps a strong reference to its `Flow` and the `Flow` keeps a weak one
back, which avoids a cycle. It also means `flow = mg.MgVideo(path).flow` leaves
nothing holding the video: it is collected at the end of the expression and the
flow's `self.parent()` resolves to None from then on. Dereferencing that raised
an AttributeError naming whichever attribute was reached for, which said nothing
about the cause.
"""
import gc

import pytest

import musicalgestures
from musicalgestures._flow import Flow


class _Detached:
    """A Flow whose parent is already gone, without needing a real video."""

    def __init__(self):
        import weakref

        class _Doomed:
            pass

        doomed = _Doomed()
        self.flow = Flow.__new__(Flow)
        self.flow.parent = weakref.ref(doomed)
        del doomed
        gc.collect()


class TestParentResolution:
    def test_a_live_parent_is_returned(self):
        import weakref

        class _Alive:
            pass

        alive = _Alive()
        flow = Flow.__new__(Flow)
        flow.parent = weakref.ref(alive)
        assert flow._parent() is alive

    def test_a_collected_parent_raises_something_explaining_itself(self):
        flow = _Detached().flow
        with pytest.raises(RuntimeError) as excinfo:
            flow._parent()
        message = str(excinfo.value)
        assert "no longer exists" in message
        assert "mv.flow.dense()" in message, "the message must show the working pattern"

    def test_the_failure_is_not_an_attributeerror(self):
        """An AttributeError here names an attribute, not the reason."""
        flow = _Detached().flow
        with pytest.raises(RuntimeError):
            flow._parent()


class TestFlowIsStillWeak:
    """The weak reference is deliberate. A well-meaning change to a strong one
    would make every MgVideo that touched .flow immortal, since the video holds
    the flow and the flow would hold the video."""

    def test_the_stored_parent_is_a_weak_reference_not_the_video(self):
        import weakref

        class _Video:
            pass

        video = _Video()
        flow = Flow.__new__(Flow)
        Flow.__init__(flow, video, filename="f.avi", color=True, has_audio=False)
        assert isinstance(flow.parent, weakref.ref)
        assert flow.parent() is video

    def test_the_flow_does_not_keep_the_video_alive(self):
        import weakref

        class _Video:
            pass

        video = _Video()
        flow = Flow.__new__(Flow)
        Flow.__init__(flow, video, filename="f.avi", color=True, has_audio=False)
        del video
        gc.collect()
        assert flow.parent() is None, "the flow kept its video alive"
