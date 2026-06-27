"""Shared pytest configuration.

Force a non-interactive Matplotlib backend so the test suite never tries to open a
GUI window. Without this, some runners (notably Windows) fail with
``_tkinter.TclError: Can't find a usable init.tcl`` when Matplotlib defaults to the Tk
backend during figure-producing tests.
"""
import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib  # noqa: E402
matplotlib.use("Agg", force=True)
