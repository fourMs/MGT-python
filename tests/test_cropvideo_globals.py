"""The cropping window's shared state, and the crop box it produces.

`cropping_window` reads `ref_point` after the user presses "c". The name used to
be created only by the mouse callback, so pressing "c" without having dragged a
rectangle---which is exactly what the on-screen prompt invites---raised
`NameError: name 'ref_point' is not defined` at the user. The box arithmetic
that followed it needed a window and a mouse to reach, so none of it was tested.
It now lives in `crop_box_from_points`, which needs neither. See issue #350.
"""
import pytest

import musicalgestures._cropvideo as cv
from musicalgestures._cropvideo import crop_box_from_points


class TestSharedState:
    def test_every_callback_global_is_bound_at_import(self):
        """The mouse callback declares these global; none may wait for an event to exist."""
        for name in ("ref_point", "crop", "drawing", "xi", "yi", "x", "y", "w", "h"):
            assert hasattr(cv, name), f"{name} is not bound until a callback runs"

    def test_ref_point_starts_empty(self):
        assert cv.ref_point == []


class TestCropBoxFromPoints:
    """The two corners arrive in click order, so either may be the top-left one."""

    EXPECTED = (100, 200, 10, 20)  # w, h, x, y

    def test_top_left_dragged_first(self):
        assert crop_box_from_points([(10, 20), (110, 220)]) == self.EXPECTED

    def test_bottom_right_dragged_first(self):
        assert crop_box_from_points([(110, 220), (10, 20)]) == self.EXPECTED

    def test_top_right_dragged_first(self):
        assert crop_box_from_points([(110, 20), (10, 220)]) == self.EXPECTED

    def test_bottom_left_dragged_first(self):
        assert crop_box_from_points([(10, 220), (110, 20)]) == self.EXPECTED

    def test_zero_area_selection_is_allowed_through(self):
        """A click without a drag is a real box of no size, not an error."""
        assert crop_box_from_points([(5, 5), (5, 5)]) == (0, 0, 5, 5)

    @pytest.mark.parametrize("points", [[], [(1, 2)]])
    def test_no_rectangle_drawn_tells_the_user_what_to_do(self, points):
        with pytest.raises(ValueError, match="Drag a rectangle"):
            crop_box_from_points(points)
