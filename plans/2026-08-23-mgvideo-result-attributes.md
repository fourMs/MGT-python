# MgVideo Result Attributes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Declare every result attribute on `MgVideo` with a consistent, self-describing name, closing issue #346 and the 24 `no-any-return` errors of issue #350 in one pass.

**Architecture:** Each analysis method stashes its result on the parent object under an attribute the method conjures at runtime, so `MgVideo` never declares it. Two consequences follow from that one fact: the names drifted (#346), and typing the `self` parameter of any producing function is impossible, because mypy immediately asks where the attribute was declared (#350). Declaring the attributes on `MgVideo` as **bare class-level annotations** fixes both. A bare annotation (`heatmap_image: MgImage`, no value) tells the type checker the attribute exists without creating a class attribute, so it stays absent from the instance dictionary until a method assigns it, and `show(key=...)`---which resolves results by looking in `self.__dict__`---keeps working unchanged.

**Tech Stack:** Python ≥3.10, mypy, pytest. Repo: `~/github/MGT-python`, system `python3`, mypy via `/tmp/.../mypyenv/bin/mypy` or `pip install mypy`.

**Spec:** `plans/2026-08-22-road-to-2.0-design.md` (Track 1: API hygiene). Decisions taken by ARJ 2026-08-23 are recorded there and repeated below.

## Global Constraints

- **Renames are breaking, so every one keeps a deprecated property alias**, following the pattern established in `9ef2a4f` (`ssm_fig` → `ssm_figure`): a `@property` with getter, setter and deleter that reads and writes the canonical attribute and emits `DeprecationWarning`. Not a second attribute---two plain attributes drift apart the moment either side is reassigned.
- **An alias getter re-raises under the name that was asked for**, so `hasattr(v, "old_name")` is `False` on an object that has no result, rather than raising about an attribute the caller never mentioned.
- **Aliases are removed in 2.0**, not before. Every alias carries that in its docstring and warning text.
- **Declarations are bare annotations with no value.** `motion_video: MgVideo` — never `motion_video = None`, which would put the name in the class dictionary and change `hasattr` semantics.
- Aliases live on the class that owns the attribute: `MgVideo` for video results, `MgAudio` for audio results (`MgVideo` inherits from `MgAudio`).
- British spelling in prose and docstrings; identifiers, CLI flags and dict keys are untouched by that rule.
- Tests: `python3 -m pytest tests/ -q` from the repo root. Full suite is ~3 minutes and currently reports **625 passed, 4 skipped**.
- Type check: `mypy musicalgestures/` currently reports **74 errors in 19 files**. It must never go up between tasks.
- Work on branch `mgvideo-result-attributes`. Commit per task. Do not push until ARJ asks.

## The names

Decided by ARJ. `pixelarray` → `frameaverage_image` ("says what it holds, where `pixelarray` says how it's stored"). Grams are named by what a viewer sees, not by which axis was collapsed.

| current | type | new | note |
|---|---|---|---|
| `motion_plot` | MgImage | `motion_plot_image` | |
| `motiongram_x` | MgImage | `motiongram_vertical_image` | x-collapse renders the **vertical** gram |
| `motiongram_y` | MgImage | `motiongram_horizontal_image` | y-collapse renders the **horizontal** gram |
| `videogram_x` | MgImage | `videogram_vertical_image` | |
| `videogram_y` | MgImage | `videogram_horizontal_image` | |
| `pixelarray` | MgImage | `frameaverage_image` | ffmpeg implementation |
| `pixelarray_cv2` | MgImage | `frameaverage_cv2_image` | cv2 implementation |
| `ssm_combined` | MgImage | `ssm_combined_image` | |
| `movement_beat_statistics` | MgFigure | `movement_beat_statistics_figure` | |
| `pose_average` | MgImage | `pose_average_image` | |
| `pose_trajectories` | MgImage | `pose_trajectories_image` | |

**The axis inversion is the reason the gram rename is worth doing.** `_show.py` already carries `mgh`/`mgv` aliases precisely because horizontal and vertical get confused with x and y; renaming the attributes moves the fix from the alias layer to the attribute itself.

**Deliberately NOT renamed**, and each task must leave them alone:

- `audio` (MgAudio) — core public API, `mv.audio` is in every example.
- `as_avi` (MgVideo) — a format-conversion cache, not an analysis result.
- `flow` (Flow) — a sub-object, not a result.

---

### Task 1: Declare the conforming attributes and prove the technique

Declares the 26 attributes that already have correct names, and types `self` in one producing function to prove the mechanism end to end before any rename touches it.

**Files:**
- Modify: `musicalgestures/_video.py` (class body of `MgVideo`, after `__init__`, before the class-scoped method imports at the `# Methods are bound by importing` comment)
- Modify: `musicalgestures/_audio.py` (class body of `MgAudio`, one declaration — see Step 4)
- Modify: `musicalgestures/_heatmap.py:10` (`def mg_heatmap`)
- Test: `tests/test_result_attributes.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a declarations block in `MgVideo`'s class body that Tasks 3–9 append their new names to. `MgImage` is already imported in `_video.py`; this task adds `MgFigure` to the same `from musicalgestures._utils import (...)` block.

- [ ] **Step 1: Write the failing test**

Create `tests/test_result_attributes.py`:

```python
"""MgVideo declares its result attributes, without creating them.

Analysis methods stash results on the parent object. Declaring those
attributes lets a type checker follow them; declaring them as bare
annotations means they still do not exist until a method assigns one, which
is what `show(key=...)` relies on when it looks in `self.__dict__`.
"""
import musicalgestures as mg

CONFORMING = [
    "blend_image", "blur_faces_video", "body_audio_coupling_figure",
    "dynamics_coupling_figure", "eulerian_video", "heatmap_image",
    "history_video", "mhi_image", "motion_video", "motiondescriptors_figure",
    "motionvectors_video", "phase_synchrony_figure", "pose_centered_figure",
    "pose_distance_figure", "pose_segments_figure", "pose_video",
    "pose_waterfall_figure", "silhouette_waterfall_figure",
    "sonomotiongram_audio", "spacetime_volume_figure", "ssm_figure",
    "stroboscope_image", "structure_comparison_figure", "subtract_video",
    "tempo_similarity_figure", "warp_video",
]


class TestDeclarations:
    def test_every_conforming_attribute_is_declared(self):
        # __annotations__ does not inherit, and `ssm_figure` is set on MgAudio
        # instances by mg_ssm's audio paths, so both classes are checked.
        declared = {**mg.MgAudio.__annotations__, **mg.MgVideo.__annotations__}
        missing = [n for n in CONFORMING if n not in declared]
        assert not missing, f"undeclared result attributes: {missing}"

    def test_declaring_does_not_create_a_class_attribute(self):
        """A bare annotation must not put the name in the class dictionary."""
        for name in CONFORMING:
            for cls in (mg.MgVideo, mg.MgAudio):
                assert name not in cls.__dict__, (
                    f"{name} was given a value on {cls.__name__}; "
                    "show() and hasattr would both change")

    def test_every_declared_name_ends_in_its_type(self):
        for name in CONFORMING:
            assert name.endswith(("_video", "_image", "_figure", "_audio")), name
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: FAIL on `test_every_conforming_attribute_is_declared` — "undeclared result attributes: ['blend_image', ...]" listing all 26.

- [ ] **Step 3: Add MgFigure to the imports in `_video.py`**

In `musicalgestures/_video.py`, the existing block is:

```python
from musicalgestures._utils import (
    convert,
    convert_to_mp4,
    get_framecount,
    ffmpeg_cmd,
    merge_videos,
    extract_frame,
    MgImage
)
```

Change the last entry to add `MgFigure`:

```python
from musicalgestures._utils import (
    convert,
    convert_to_mp4,
    get_framecount,
    ffmpeg_cmd,
    merge_videos,
    extract_frame,
    MgImage,
    MgFigure
)
```

- [ ] **Step 4: Add the declarations block to the MgVideo class body**

In `musicalgestures/_video.py`, immediately before the line
`    # Methods are bound by importing the implementing function at class scope.`
insert:

```python
    # Results stashed by the analysis methods.
    #
    # These are declarations, not assignments: a bare annotation tells a type
    # checker the attribute exists and what it holds, while leaving it absent
    # from the instance until a method sets it. `show(key=...)` decides what a
    # video has by looking in `self.__dict__`, so giving any of these a value
    # here would make every video claim every result. See issue #346.
    blend_image: MgImage
    blur_faces_video: "musicalgestures.MgVideo"
    body_audio_coupling_figure: MgFigure
    dynamics_coupling_figure: MgFigure
    eulerian_video: "musicalgestures.MgVideo"
    heatmap_image: MgImage
    history_video: "musicalgestures.MgVideo"
    mhi_image: MgImage
    motion_video: "musicalgestures.MgVideo"
    motiondescriptors_figure: MgFigure
    motionvectors_video: "musicalgestures.MgVideo"
    phase_synchrony_figure: MgFigure
    pose_centered_figure: MgFigure
    pose_distance_figure: MgFigure
    pose_segments_figure: MgFigure
    pose_video: "musicalgestures.MgVideo"
    pose_waterfall_figure: MgFigure
    silhouette_waterfall_figure: MgFigure
    sonomotiongram_audio: MgAudio
    spacetime_volume_figure: MgFigure
    stroboscope_image: MgImage
    structure_comparison_figure: MgFigure
    subtract_video: "musicalgestures.MgVideo"
    tempo_similarity_figure: MgFigure
    warp_video: "musicalgestures.MgVideo"

```

Note the quoted `"musicalgestures.MgVideo"` — the class cannot name itself unquoted inside its own body. `MgAudio` is already imported at the top of the file.

`ssm_figure` is deliberately absent from this block. `mg_ssm`'s audio paths set it on **MgAudio** instances, and its `ssm_fig` alias already lives there from `9ef2a4f`. Python's `__annotations__` does not inherit, so declaring it on `MgVideo` would leave `MgAudio` undeclared and break Task 8 the moment an audio producer's `self` is typed. Declare it in `musicalgestures/_audio.py` instead, in the `MgAudio` class body immediately above the existing `ssm_fig` alias:

```python
    ssm_figure: MgFigure
```

`MgFigure` is already imported in `_audio.py`; confirm with `grep -n "MgFigure" musicalgestures/_audio.py`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: PASS, 3 passed.

- [ ] **Step 6: Type `self` in the heatmap producer**

In `musicalgestures/_heatmap.py`, add the import after the existing `from musicalgestures._utils import ...` line:

```python
import musicalgestures
```

and change the signature at line 10 from:

```python
def mg_heatmap(
        self,
```

to:

```python
def mg_heatmap(
        self: "musicalgestures.MgVideo",
```

- [ ] **Step 7: Verify the type check improved and nothing regressed**

Run: `mypy musicalgestures/ 2>&1 | tail -1`
Expected: **73 errors in 19 files** (down one from 74; `_heatmap.py:131` `no-any-return` is gone).

Run: `mypy musicalgestures/ 2>&1 | grep _heatmap.py`
Expected: no output.

- [ ] **Step 8: Run the full suite**

Run: `python3 -m pytest tests/ -q`
Expected: **625 passed, 4 skipped**.

- [ ] **Step 9: Commit**

```bash
git add musicalgestures/_video.py musicalgestures/_audio.py musicalgestures/_heatmap.py tests/test_result_attributes.py
git commit -m "Declare MgVideo's result attributes instead of conjuring them"
```

---

### Task 2: A reusable deprecation alias helper

Eleven renames each need the same three-method property. Writing it eleven times invites eleven small divergences.

**Files:**
- Modify: `musicalgestures/_utils.py` (append after the `MgFigure` class)
- Test: `tests/test_deprecated_alias.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `deprecated_alias(old: str, new: str) -> property`, used by Tasks 3–9. Returns a property whose getter, setter and deleter proxy to `new` and warn with `f"{old} is deprecated and will be removed in 2.0; use {new}."`

- [ ] **Step 1: Write the failing test**

Create `tests/test_deprecated_alias.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_deprecated_alias.py -q`
Expected: FAIL at import — "cannot import name 'deprecated_alias' from 'musicalgestures._utils'".

- [ ] **Step 3: Implement the helper**

Append to `musicalgestures/_utils.py`:

```python
def deprecated_alias(old: str, new: str) -> property:
    """A property that reads and writes `new` under the retired name `old`.

    Renaming a result attribute is a breaking change, because `show(key=...)`
    and user code both reach these by name. The old name keeps working through
    one release and warns, and it is a property rather than a second attribute
    so the two names cannot drift apart when either side is reassigned.

    Args:
        old (str): The retired attribute name, used only in the warning.
        new (str): The canonical attribute this proxies to.

    Returns:
        property: Assign it in a class body as ``old_name = deprecated_alias(...)``.
    """
    message = f"{old} is deprecated and will be removed in 2.0; use {new}."

    def getter(self):
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        try:
            return getattr(self, new)
        except AttributeError:
            # report the name that was asked for, so hasattr(obj, old) is False
            # rather than raising about an attribute the caller never mentioned
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {old!r}") from None

    def setter(self, value):
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        setattr(self, new, value)

    def deleter(self):
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        delattr(self, new)

    getter.__doc__ = f"Deprecated alias for :attr:`{new}`. Removed in 2.0."
    return property(getter, setter, deleter)
```

`warnings` is already imported at the top of `_utils.py`; confirm with `grep -n "^import warnings" musicalgestures/_utils.py` and add it if absent.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_deprecated_alias.py -q`
Expected: PASS, 6 passed.

- [ ] **Step 5: Port the existing `ssm_fig` alias onto the helper**

`musicalgestures/_audio.py` carries a hand-written version of exactly this property from `9ef2a4f`. Replace the whole block (the `@property def ssm_fig`, its `.setter` and its `.deleter`, and the explanatory comment above them) with:

```python
    # `ssm_fig` was the odd one out: every other stashed result ends in `_video`,
    # `_image` or `_figure`. See issue #346; the alias goes away in 2.0.
    ssm_fig = deprecated_alias("ssm_fig", "ssm_figure")
```

and add `deprecated_alias` to the existing `from musicalgestures._utils import ...` line in that file.

- [ ] **Step 6: Verify the ported alias behaves identically**

Run: `python3 -m pytest tests/test_ssm.py tests/test_deprecated_alias.py -q`
Expected: PASS, 30 passed (24 in `test_ssm.py`, 6 here). The five `TestSsmFigureAlias` tests written in `9ef2a4f` must pass unchanged against the helper — that is what makes this a safe refactor.

- [ ] **Step 7: Commit**

```bash
git add musicalgestures/_utils.py musicalgestures/_audio.py tests/test_deprecated_alias.py
git commit -m "One deprecation-alias helper, and put ssm_fig on it"
```

---

### Task 3: Rename `motion_plot` to `motion_plot_image`

The only outlier `show()` reaches, so it is the one with real breakage risk and it goes first, alone.

**Files:**
- Modify: `musicalgestures/_motionvideo.py:327`
- Modify: `musicalgestures/_motionvideo_mp_run.py:260`
- Modify: `musicalgestures/_show.py` (the `elif key.lower() == 'plot':` branch)
- Modify: `musicalgestures/_video.py` (declarations block from Task 1, and the alias)
- Test: `tests/test_result_attributes.py` (extend)

**Interfaces:**
- Consumes: `deprecated_alias` from Task 2; the declarations block from Task 1.
- Produces: `MgVideo.motion_plot_image: MgImage`, with `motion_plot` as a deprecated alias.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_result_attributes.py`:

```python
import pytest

RENAMED = [
    ("motion_plot", "motion_plot_image"),
]


class TestRenames:
    @pytest.mark.parametrize("old,new", RENAMED)
    def test_the_new_name_is_declared(self, old, new):
        assert new in mg.MgVideo.__annotations__

    @pytest.mark.parametrize("old,new", RENAMED)
    def test_the_old_name_still_works_and_warns(self, old, new):
        v = mg.MgVideo.__new__(mg.MgVideo)
        setattr(v, new, "sentinel")
        with pytest.warns(DeprecationWarning, match=f"use {new}"):
            assert getattr(v, old) == "sentinel"

    @pytest.mark.parametrize("old,new", RENAMED)
    def test_writing_the_old_name_lands_under_the_new_one(self, old, new):
        v = mg.MgVideo.__new__(mg.MgVideo)
        with pytest.warns(DeprecationWarning):
            setattr(v, old, "sentinel")
        assert v.__dict__[new] == "sentinel"
        assert old not in v.__dict__
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: FAIL on `test_the_new_name_is_declared` — `motion_plot_image` is not in `__annotations__`.

- [ ] **Step 3: Rename the two assignment sites**

`musicalgestures/_motionvideo.py:327` — change `self.motion_plot = MgImage(save_analysis(` to `self.motion_plot_image = MgImage(save_analysis(`.

`musicalgestures/_motionvideo_mp_run.py:260` — change `self.motion_plot = MgImage(save_analysis(` to `self.motion_plot_image = MgImage(save_analysis(`.

- [ ] **Step 4: Update the `show()` lookup**

In `musicalgestures/_show.py`, the branch reads:

```python
        elif key.lower() == 'plot':
            # filename = self.of + '_motion_com_qom.png'
            if "motion_plot" in keys:
                filename = self.motion_plot.filename
```

Change both references:

```python
        elif key.lower() == 'plot':
            # filename = self.of + '_motion_com_qom.png'
            if "motion_plot_image" in keys:
                filename = self.motion_plot_image.filename
```

A class-level property does not appear in `self.__dict__`, so the `in keys` test must name the canonical attribute, never the alias.

- [ ] **Step 5: Declare the new name and add the alias**

In `musicalgestures/_video.py`, add to the declarations block, in alphabetical position after `motiondescriptors_figure`:

```python
    motion_plot_image: MgImage
```

Add `deprecated_alias` to the `from musicalgestures._utils import (...)` block, and after the declarations block add:

```python
    # Retired names, kept working for one release. See issue #346.
    motion_plot = deprecated_alias("motion_plot", "motion_plot_image")
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: PASS, 6 passed.

- [ ] **Step 7: Verify `show()` still finds the plot end to end**

```bash
python3 - <<'EOF'
import matplotlib; matplotlib.use('Agg')
import shutil, musicalgestures as mg
shutil.copy(mg.examples.dance, 'plan_check.avi')
mv = mg.MgVideo('plan_check.avi')
mv.motion()
assert 'motion_plot_image' in mv.__dict__, mv.__dict__.keys()
assert 'motion_plot' not in mv.__dict__
print("OK: result stored under the new name only")
EOF
```

Expected: `OK: result stored under the new name only`.

- [ ] **Step 8: Run the full suite and the type check**

Run: `python3 -m pytest tests/ -q`
Expected: **637 passed, 4 skipped** (625 baseline, +3 from Task 1, +6 from Task 2, +3 here).

Run: `mypy musicalgestures/ 2>&1 | tail -1`
Expected: 73 errors or fewer. Never more.

- [ ] **Step 9: Commit**

```bash
git add musicalgestures/_motionvideo.py musicalgestures/_motionvideo_mp_run.py \
        musicalgestures/_show.py musicalgestures/_video.py tests/test_result_attributes.py
git commit -m "Rename motion_plot to motion_plot_image, keeping the old name"
```

---

### Task 4: Rename the motiongram AND videogram pairs, fixing the axis inversion

`motiongram_x` is the **vertical** gram and `motiongram_y` is the **horizontal** one, because the name records which axis was collapsed rather than what the reader sees. `_show.py` already carries `mgh`/`mgv` aliases to work around that. This moves the fix to the attribute.

**Both pairs are renamed in one task, deliberately.** `show()` resolves all four by interpolating one attribute name, so renaming the motiongrams alone would leave every videogram key (`vgh`, `vgv`, `vgx`, `vgy`, and `horizontal`/`vertical` falling through to videogram) raising `FileNotFoundError` until the videograms followed. There is no point in the sequence where the tree is half-renamed.

**Files:**
- Modify: `musicalgestures/_motionvideo.py:307-308`
- Modify: `musicalgestures/_motionvideo_mp_run.py:212-213`
- Modify: `musicalgestures/_videograms.py` (five references: two assignment pairs, two `MgList` returns, one comment)
- Modify: `musicalgestures/_ssm.py` (two comments mentioning `motiongram_x`/`motiongram_y`)
- Modify: `musicalgestures/_show.py` (the orientation branch, which builds the attribute name by interpolation)
- Modify: `musicalgestures/_video.py`
- Test: `tests/test_result_attributes.py` (extend `RENAMED`)

**Interfaces:**
- Consumes: `deprecated_alias` from Task 2; the declarations and retired-names blocks from Tasks 1 and 3.
- Produces: `MgVideo.motiongram_vertical_image`, `MgVideo.motiongram_horizontal_image`, `MgVideo.videogram_vertical_image`, `MgVideo.videogram_horizontal_image`, all `MgImage`, with `motiongram_x`/`motiongram_y`/`videogram_x`/`videogram_y` as deprecated aliases.

- [ ] **Step 1: Extend the test**

In `tests/test_result_attributes.py`, extend `RENAMED` to:

```python
RENAMED = [
    ("motion_plot", "motion_plot_image"),
    ("motiongram_x", "motiongram_vertical_image"),
    ("motiongram_y", "motiongram_horizontal_image"),
    ("videogram_x", "videogram_vertical_image"),
    ("videogram_y", "videogram_horizontal_image"),
]
```

and append a test that pins the inversion, so nobody "corrects" it later:

```python
class TestGramOrientation:
    """The x-collapse produces the vertical gram. Pinning it, because the
    inverted-looking mapping is correct and has been mistaken for a bug."""

    @pytest.mark.parametrize("kind", ["motiongram", "videogram"])
    def test_x_maps_to_vertical_and_y_to_horizontal(self, kind):
        v = mg.MgVideo.__new__(mg.MgVideo)
        with pytest.warns(DeprecationWarning):
            setattr(v, f"{kind}_x", "from-x")
        with pytest.warns(DeprecationWarning):
            setattr(v, f"{kind}_y", "from-y")
        assert getattr(v, f"{kind}_vertical_image") == "from-x"
        assert getattr(v, f"{kind}_horizontal_image") == "from-y"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: FAIL — `motiongram_vertical_image` not declared.

- [ ] **Step 3: Rename the motiongram assignment sites**

`musicalgestures/_motionvideo.py` lines 307-308:

```python
            self.motiongram_vertical_image = MgImage(target_name_mgx)
            self.motiongram_horizontal_image = MgImage(target_name_mgy)
```

`musicalgestures/_motionvideo_mp_run.py` lines 212-213: the same two replacements.

- [ ] **Step 4: Rename the videogram sites**

In `musicalgestures/_videograms.py` there are two code paths (an ffmpeg one and a fallback), each assigning both attributes and each returning an `MgList` of the pair. Replace every occurrence of `self.videogram_x` with `self.videogram_vertical_image` and `self.videogram_y` with `self.videogram_horizontal_image`, including inside both `return MgList(self.videogram_x, self.videogram_y)` statements and the comment at line 144.

Verify none remain: `grep -n "videogram_[xy]" musicalgestures/_videograms.py` must print nothing.

- [ ] **Step 5: Update the two comments in `_ssm.py`**

Two lines (around 253 and 355 — find them by text, since the first edit shifts the second's line number) both read:

```python
        # mg_ssm also saves the motiongrams SSM as MgImages to self.motiongram_x and self.motiongram_y of the parent MgVideo
```

Replace both with:

```python
        # mg_ssm also saves the motiongrams SSM as MgImages to
        # self.motiongram_vertical_image and self.motiongram_horizontal_image of the parent MgVideo
```

- [ ] **Step 6: Rework the `show()` orientation branch**

The branch currently maps a key to an axis letter and interpolates the attribute name. Replace the body from `k = key.lower()` down to the `for kind in kinds:` loop with an orientation word instead of an axis letter:

```python
            k = key.lower()
            horizontal_keys = ('horizontal', 'mgh', 'vgh', 'mgy', 'vgy')
            orientation = 'horizontal' if k in horizontal_keys else 'vertical'
            label = orientation.capitalize()
            if k in ('mgh', 'mgv', 'mgx', 'mgy'):
                kinds = ('motiongram',)
            elif k in ('vgh', 'vgv', 'vgx', 'vgy'):
                kinds = ('videogram',)
            else:
                kinds = ('motiongram', 'videogram')
            target = None
            for kind in kinds:
                attr = f"{kind}_{orientation}_image"
                if attr in keys:
                    target = (kind, getattr(self, attr).filename)
                    break
```

The legacy `mgx`/`mgy` keys keep working and keep their historical meaning: `mgy` is in `horizontal_keys`, so it still resolves to the horizontal gram.

- [ ] **Step 7: Declare and alias**

In `musicalgestures/_video.py` declarations block:

```python
    motiongram_horizontal_image: MgImage
    motiongram_vertical_image: MgImage
    videogram_horizontal_image: MgImage
    videogram_vertical_image: MgImage
```

and in the retired-names block:

```python
    motiongram_x = deprecated_alias("motiongram_x", "motiongram_vertical_image")
    motiongram_y = deprecated_alias("motiongram_y", "motiongram_horizontal_image")
    videogram_x = deprecated_alias("videogram_x", "videogram_vertical_image")
    videogram_y = deprecated_alias("videogram_y", "videogram_horizontal_image")
```

- [ ] **Step 8: Run the tests**

Run: `python3 -m pytest tests/test_result_attributes.py tests/test_videograms.py -q`
Expected: PASS. `test_result_attributes.py` contributes 20 tests (3 declaration tests, 5 renamed pairs x 3 methods, 2 orientation tests). `test_videograms.py` includes the slit-image tests added in `0b84762` and must be unaffected.

- [ ] **Step 9: Verify every `show()` orientation key still resolves, for both kinds**

```bash
python3 - <<'EOF'
import matplotlib; matplotlib.use('Agg')
import shutil, musicalgestures as mg
shutil.copy(mg.examples.dance, 'plan_check2.avi')
mv = mg.MgVideo('plan_check2.avi')
mv.motiongrams()
mv.videograms()
for a in ('motiongram_vertical_image', 'motiongram_horizontal_image',
          'videogram_vertical_image', 'videogram_horizontal_image'):
    assert a in mv.__dict__, a
for key in ('mgh', 'mgv', 'mgx', 'mgy', 'vgh', 'vgv', 'vgx', 'vgy',
            'horizontal', 'vertical'):
    mv.show(key=key, mode='notebook')   # must not raise FileNotFoundError
print("OK: all ten orientation keys resolve, both kinds")
EOF
```

Expected: `OK: all ten orientation keys resolve, both kinds`.

- [ ] **Step 10: Full suite, type check, commit**

Run: `python3 -m pytest tests/ -q` — expected **651 passed, 4 skipped**.
Run: `mypy musicalgestures/ 2>&1 | tail -1` — must not exceed 73.

```bash
git add musicalgestures/_motionvideo.py musicalgestures/_motionvideo_mp_run.py \
        musicalgestures/_videograms.py musicalgestures/_ssm.py musicalgestures/_show.py \
        musicalgestures/_video.py tests/test_result_attributes.py
git commit -m "Name the grams by what they show, not by the axis collapsed"
```

---

### Task 5: folded into Task 4

The videogram rename was merged into Task 4 during the pre-flight scan: `show()` resolves both
kinds through one interpolated attribute name, so renaming the motiongrams alone would have left
every videogram key broken between the two tasks. Nothing to do here; the numbering is kept so
Tasks 6-9 are unchanged.

---

### Task 6: Rename the frame-average pair

`pixelarray` describes how the result is stored rather than what it holds. ARJ chose `frameaverage_image`.

**Files:**
- Modify: `musicalgestures/_frameaverage.py:49, 120`
- Modify: `musicalgestures/_video.py`
- Modify: `docs/examples.md` if it mentions `pixelarray` (check with grep)
- Test: `tests/test_result_attributes.py` (extend `RENAMED`)

**Interfaces:**
- Consumes: `deprecated_alias`, the declarations block.
- Produces: `MgVideo.frameaverage_image` and `MgVideo.frameaverage_cv2_image`, both `MgImage`.

- [ ] **Step 1: Extend `RENAMED`**

```python
    ("pixelarray", "frameaverage_image"),
    ("pixelarray_cv2", "frameaverage_cv2_image"),
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: FAIL — `frameaverage_image` not declared.

- [ ] **Step 3: Rename the assignment sites**

`musicalgestures/_frameaverage.py:49` — `self.pixelarray = MgImage(target_name)` becomes `self.frameaverage_image = MgImage(target_name)`.

`musicalgestures/_frameaverage.py:120` — `self.pixelarray_cv2 = MgImage(target_name)` becomes `self.frameaverage_cv2_image = MgImage(target_name)`.

The two are the ffmpeg and cv2 implementations of the same operation; the names keep that distinction.

- [ ] **Step 4: Check `_video.py` for other references**

Run: `grep -n "pixelarray" musicalgestures/_video.py`

If the grep finds a reference other than the ones you are about to add, update it to the new name. Then add to the declarations block:

```python
    frameaverage_cv2_image: MgImage
    frameaverage_image: MgImage
```

and to the retired-names block:

```python
    pixelarray = deprecated_alias("pixelarray", "frameaverage_image")
    pixelarray_cv2 = deprecated_alias("pixelarray_cv2", "frameaverage_cv2_image")
```

- [ ] **Step 5: Update the documentation**

Run: `grep -rn "pixelarray" docs/ README.md`

Replace any occurrence in prose or example code with `frameaverage_image`. Documentation shows people the current name; the alias exists for code already written, not for new readers.

- [ ] **Step 6: Run the tests**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: PASS, 26 passed.

- [ ] **Step 7: Full suite, type check, commit**

Run: `python3 -m pytest tests/ -q` — expected **657 passed, 4 skipped**.
Run: `mypy musicalgestures/ 2>&1 | tail -1` — must not exceed 73.

```bash
git add musicalgestures/_frameaverage.py musicalgestures/_video.py docs/ tests/test_result_attributes.py
git commit -m "Rename pixelarray to frameaverage_image, after what it holds"
```

---

### Task 7: Rename the four remaining outliers

`ssm_combined`, `movement_beat_statistics`, `pose_average` and `pose_trajectories`. None is reached by `show()`, none has a companion, and each is a single assignment site, so they go together.

**Files:**
- Modify: `musicalgestures/_ssm.py:182`
- Modify: `musicalgestures/_movementbeats.py:190`
- Modify: `musicalgestures/_pose.py:729-730, 896-897`
- Modify: `musicalgestures/_video.py`
- Modify: `docs/examples.md` (mentions `pose_average` and `pose_trajectories`)
- Test: `tests/test_result_attributes.py` (extend `RENAMED`)

**Interfaces:**
- Consumes: `deprecated_alias`, the declarations block.
- Produces: `MgVideo.ssm_combined_image: MgImage`, `MgVideo.movement_beat_statistics_figure: MgFigure`, `MgVideo.pose_average_image: MgImage`, `MgVideo.pose_trajectories_image: MgImage`.

- [ ] **Step 1: Extend `RENAMED`**

```python
    ("ssm_combined", "ssm_combined_image"),
    ("movement_beat_statistics", "movement_beat_statistics_figure"),
    ("pose_average", "pose_average_image"),
    ("pose_trajectories", "pose_trajectories_image"),
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: FAIL — `ssm_combined_image` not declared.

- [ ] **Step 3: Rename the assignment sites**

`musicalgestures/_ssm.py:182` — `self.ssm_combined = MgImage(target_name)` becomes `self.ssm_combined_image = MgImage(target_name)`.

`musicalgestures/_movementbeats.py:190` — `self.movement_beat_statistics = mgf` becomes `self.movement_beat_statistics_figure = mgf`.

`musicalgestures/_pose.py` lines 729-730 and again at 896-897 — both pairs read:

```python
    self.pose_average = average_image
    self.pose_trajectories = trajectories_image
```

Both become:

```python
    self.pose_average_image = average_image
    self.pose_trajectories_image = trajectories_image
```

Verify none remain: `grep -rn "self\.\(ssm_combined\|movement_beat_statistics\|pose_average\|pose_trajectories\) " musicalgestures/` must print nothing.

- [ ] **Step 4: Declare and alias**

Declarations block:

```python
    movement_beat_statistics_figure: MgFigure
    pose_average_image: MgImage
    pose_trajectories_image: MgImage
    ssm_combined_image: MgImage
```

Retired-names block:

```python
    ssm_combined = deprecated_alias("ssm_combined", "ssm_combined_image")
    movement_beat_statistics = deprecated_alias(
        "movement_beat_statistics", "movement_beat_statistics_figure")
    pose_average = deprecated_alias("pose_average", "pose_average_image")
    pose_trajectories = deprecated_alias("pose_trajectories", "pose_trajectories_image")
```

- [ ] **Step 5: Update the documentation**

Run: `grep -rn "pose_average\|pose_trajectories\|ssm_combined\|movement_beat_statistics" docs/ README.md`

Replace occurrences in prose and example code with the new names.

- [ ] **Step 6: Run the tests**

Run: `python3 -m pytest tests/test_result_attributes.py -q`
Expected: PASS, 38 passed.

- [ ] **Step 7: Full suite, type check, commit**

Run: `python3 -m pytest tests/ -q` — expected **669 passed, 4 skipped**.
Run: `mypy musicalgestures/ 2>&1 | tail -1` — must not exceed 73.

```bash
git add musicalgestures/_ssm.py musicalgestures/_movementbeats.py musicalgestures/_pose.py \
        musicalgestures/_video.py docs/ tests/test_result_attributes.py
git commit -m "Rename the last four result attributes to name their type"
```

---

### Task 8: Type `self` in every producing function

With all attributes declared, the `no-any-return` errors can be closed properly rather than cast away. This is the task that turns the declarations into a type-checking benefit.

**Files:**
- Modify: every module named by `mypy musicalgestures/ 2>&1 | grep no-any-return`
- Test: no new test; `mypy` is the test.

**Interfaces:**
- Consumes: the complete declarations block from Tasks 1 and 3–7.
- Produces: no API change. The measurable outcome is the mypy count.

- [ ] **Step 1: List the work**

Run:

```bash
mypy musicalgestures/ 2>&1 | grep no-any-return | sed 's/:.*//' | sort | uniq -c | sort -rn
```

Record the list. Each line is a module whose `self` parameter is unannotated.

- [ ] **Step 2: Annotate one module and confirm the count falls**

Pick the module with the most errors. For each module-level function whose first parameter is `self`, add the annotation and the import.

Add near the other imports, if not already present:

```python
import musicalgestures
```

and change each signature from `def mg_something(self, ...)` to `def mg_something(self: "musicalgestures.MgVideo", ...)`.

Run: `mypy musicalgestures/ 2>&1 | tail -1`
Expected: the total falls by that module's `no-any-return` count and by nothing else. **If the total rises, an attribute is still undeclared** — add it to the declarations block in `_video.py` rather than reverting; that is the mechanism working.

- [ ] **Step 3: Run the suite for that module**

Run: `python3 -m pytest tests/ -q`
Expected: **669 passed, 4 skipped**. Annotations are inert at runtime, so any failure here means a real edit slipped in.

- [ ] **Step 4: Commit that module**

```bash
git add musicalgestures/<module>.py musicalgestures/_video.py
git commit -m "Type self in <module>'s producers"
```

- [ ] **Step 5: Repeat Steps 2–4 for each remaining module**

One module per commit. Never batch them: a rise in the mypy total needs to be attributable to one module.

- [ ] **Step 6: Record the final count**

Run: `mypy musicalgestures/ 2>&1 | tail -1`
Expected: **around 50 errors in ~17 files**, down from 74. The 24 `no-any-return` errors are gone; `union-attr` (18), `arg-type` (10) and the tail remain and are out of scope here.

---

### Task 9: Write it down

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `plans/2026-08-22-road-to-2.0-design.md` (mark step 2 done, record the decisions)
- Test: none.

- [ ] **Step 1: Add the CHANGELOG entry**

Under `## [Unreleased]`, in `### Changed`:

```markdown
- Every result an analysis method stashes on `MgVideo` is now declared on the class and named
  after what it holds: `motion_plot_image`, `frameaverage_image`, `frameaverage_cv2_image`,
  `ssm_combined_image`, `movement_beat_statistics_figure`, `pose_average_image`,
  `pose_trajectories_image`, and the four grams below. Each old name keeps working as a
  deprecated alias and is removed in 2.0. Closes #346.
- The motiongrams and videograms are named for what they show rather than for the axis that was
  collapsed to make them: `motiongram_x` was the *vertical* gram and `motiongram_y` the
  *horizontal* one, which is why `show()` grew `mgh`/`mgv` aliases in the first place. They are
  `motiongram_vertical_image`, `motiongram_horizontal_image`, `videogram_vertical_image` and
  `videogram_horizontal_image` now. Every existing `show()` key, including the legacy `mgx`/`mgy`,
  resolves as before.
- Declaring the attributes also made the producing functions typeable, so `mypy musicalgestures/`
  falls from 74 errors to about 50 and the toolbox's results now autocomplete in an editor.
```

- [ ] **Step 2: Update the design document**

In `plans/2026-08-22-road-to-2.0-design.md`, strike through step 2 of "Order and gates" and mark it done with the commit range. Under "Open decisions for ARJ", replace the `motion_plot` paragraph with the decisions taken: `frameaverage_image` for `pixelarray`, orientation words for the grams, and one combined job for the renames and the declarations.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md plans/2026-08-22-road-to-2.0-design.md
git commit -m "Record the attribute rename and what it bought"
```

---

## What this plan does not do

- **The remaining ~50 mypy errors.** `union-attr` (18, five of them the `Popen`-with-`PIPE` pattern), `arg-type` (10) and a tail of individual cases. Dropping `|| true` from CI needs those or an explicit allowlist, and that is a separate decision recorded in the design document.
- **Removing the aliases.** That is the 2.0 release itself, step 4 of the design document.
- **`audio`, `as_avi` and `flow`.** Named exceptions, explained above.
- **`mg_motiondata`'s return annotation.** A one-line fix (`-> "str | list"`) unrelated to this work; verified by running it, and noted in the design document.
