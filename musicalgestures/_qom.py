"""Re-exported from the ``micromotion`` package.

These functions used to live here. They were moved to ``micromotion`` on 2026-07-29 so that
one implementation of quantity of motion exists rather than two, and MGT now depends on that
package instead of carrying its own copy. Behaviour is unchanged: this module's tests pass
against ``micromotion`` unmodified.

The dependency points this way round on purpose. ``micromotion`` needs only numpy, scipy and
pandas, so someone analysing accelerometer data does not have to install a computer-vision
stack; MGT already depends on ``ambiscape`` the same way, and neither of those packages
imports MGT.

Import from ``micromotion`` directly in new code.
"""

from micromotion.qom import (  # noqa: F401
    accel_to_speed,
    band_limited_qom,
    bin_series,
    body_scale,
    envelope,
    grid_qom,
    group_qom,
    normalized_qom,
    pose_qom,
)

__all__ = [
    "accel_to_speed",
    "band_limited_qom",
    "bin_series",
    "body_scale",
    "envelope",
    "grid_qom",
    "group_qom",
    "normalized_qom",
    "pose_qom",
]
