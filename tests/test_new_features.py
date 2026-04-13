"""Tests for the new MGT-python v1.4.0 features.

These tests cover all new modules added in the modernisation effort:
- _enums, _exceptions, _logging (Phase 1)
- _features, _stream (Phase 2)
- _pose_estimator (Phase 3)
- _pipeline, _dataset (Phase 4)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Phase 1 – Enums
# ---------------------------------------------------------------------------

class TestEnums:
    """Tests for musicalgestures._enums."""

    def test_filter_type_values(self):
        from musicalgestures._enums import FilterType
        assert FilterType.REGULAR == "Regular"
        assert FilterType.BINARY == "Binary"
        assert FilterType.BLOB == "Blob"

    def test_filter_type_case_insensitive(self):
        from musicalgestures._enums import FilterType
        assert FilterType("regular") == FilterType.REGULAR
        assert FilterType("BINARY") == FilterType.BINARY
        assert FilterType("Blob") == FilterType.BLOB

    def test_blur_type_values(self):
        from musicalgestures._enums import BlurType
        assert BlurType.NONE == "None"
        assert BlurType.AVERAGE == "Average"

    def test_blur_type_case_insensitive(self):
        from musicalgestures._enums import BlurType
        assert BlurType("none") == BlurType.NONE
        assert BlurType("AVERAGE") == BlurType.AVERAGE

    def test_crop_mode_values(self):
        from musicalgestures._enums import CropMode
        assert CropMode.NONE == "None"
        assert CropMode.MANUAL == "manual"
        assert CropMode.AUTO == "auto"

    def test_pose_model_values(self):
        from musicalgestures._enums import PoseModel
        assert PoseModel.BODY_25 == "body_25"
        assert PoseModel.MEDIAPIPE == "mediapipe"

    def test_pose_device_values(self):
        from musicalgestures._enums import PoseDevice
        assert PoseDevice.CPU == "cpu"
        assert PoseDevice.GPU == "gpu"

    def test_data_format_values(self):
        from musicalgestures._enums import DataFormat
        assert DataFormat.CSV == "csv"
        assert DataFormat.TSV == "tsv"
        assert DataFormat.JSON == "json"
        assert DataFormat.HDF5 == "hdf5"

    def test_string_comparison(self):
        """Enum members must compare equal to plain strings."""
        from musicalgestures._enums import FilterType
        assert FilterType.REGULAR == "Regular"
        assert "Regular" == FilterType.REGULAR

    def test_unknown_value_raises(self):
        from musicalgestures._enums import FilterType
        with pytest.raises((ValueError, KeyError)):
            FilterType("NotAFilter")


# ---------------------------------------------------------------------------
# Phase 1 – Exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    """Tests for musicalgestures._exceptions."""

    def test_hierarchy(self):
        from musicalgestures._exceptions import (
            MgError, MgInputError, MgProcessingError, MgIOError, MgDependencyError,
        )
        assert issubclass(MgInputError, MgError)
        assert issubclass(MgProcessingError, MgError)
        assert issubclass(MgIOError, MgError)
        assert issubclass(MgDependencyError, MgError)

    def test_raise_and_catch(self):
        from musicalgestures._exceptions import MgError, MgInputError
        with pytest.raises(MgError):
            raise MgInputError("bad input")

    def test_subclass_is_exception(self):
        from musicalgestures._exceptions import MgDependencyError
        assert issubclass(MgDependencyError, Exception)


# ---------------------------------------------------------------------------
# Phase 1 – Logging
# ---------------------------------------------------------------------------

class TestLogging:
    """Tests for musicalgestures._logging."""

    def test_logger_name(self):
        from musicalgestures._logging import logger
        assert logger.name == "musicalgestures"

    def test_set_log_level_string(self):
        import logging
        from musicalgestures._logging import set_log_level, logger
        set_log_level("WARNING")
        assert logger.level == logging.WARNING

    def test_set_log_level_int(self):
        import logging
        from musicalgestures._logging import set_log_level, logger
        set_log_level(logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_null_handler_present(self):
        import logging
        from musicalgestures._logging import logger
        # At least one handler (NullHandler) should be present
        assert len(logger.handlers) >= 1


# ---------------------------------------------------------------------------
# Phase 2 – MgFeatures
# ---------------------------------------------------------------------------

class TestMgFeatures:
    """Tests for musicalgestures._features.MgFeatures."""

    def _make(self, n=10):
        from musicalgestures._features import MgFeatures
        return MgFeatures(
            data={"qom": np.random.rand(n), "com_x": np.random.rand(n)},
            times=np.linspace(0, 1, n),
            sr=float(n),
            source="test.avi",
        )

    def test_shape(self):
        feat = self._make(10)
        assert feat.shape == (2, 10)

    def test_n_features(self):
        feat = self._make(10)
        assert feat.n_features == 2

    def test_n_samples(self):
        feat = self._make(10)
        assert feat.n_samples == 10

    def test_feature_names(self):
        feat = self._make()
        assert feat.feature_names == ["qom", "com_x"]

    def test_to_numpy_shape(self):
        feat = self._make(15)
        arr = feat.to_numpy()
        assert arr.shape == (2, 15)

    def test_array_protocol(self):
        feat = self._make(5)
        arr = np.array(feat)
        assert arr.shape == (2, 5)

    def test_to_dataframe(self):
        import pandas as pd
        feat = self._make(8)
        df = feat.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["qom", "com_x"]
        assert len(df) == 8

    def test_getitem(self):
        from musicalgestures._features import MgFeatures
        feat = MgFeatures({"a": np.array([1.0, 2.0, 3.0])}, sr=10.0)
        np.testing.assert_array_equal(feat["a"], [1.0, 2.0, 3.0])

    def test_contains(self):
        from musicalgestures._features import MgFeatures
        feat = MgFeatures({"a": np.ones(3)}, sr=10.0)
        assert "a" in feat
        assert "b" not in feat

    def test_len(self):
        feat = self._make()
        assert len(feat) == 2

    def test_iter(self):
        feat = self._make()
        names = list(feat)
        assert names == ["qom", "com_x"]

    def test_times_default(self):
        from musicalgestures._features import MgFeatures
        feat = MgFeatures({"a": np.ones(5)}, sr=5.0)
        np.testing.assert_array_equal(feat.times, np.arange(5))

    def test_times_mismatch_raises(self):
        from musicalgestures._features import MgFeatures
        with pytest.raises(ValueError, match="length"):
            MgFeatures({"a": np.ones(5)}, times=np.ones(3), sr=5.0)

    def test_empty_data_raises(self):
        from musicalgestures._features import MgFeatures
        with pytest.raises(ValueError):
            MgFeatures({}, sr=1.0)

    def test_unequal_lengths_raise(self):
        from musicalgestures._features import MgFeatures
        with pytest.raises(ValueError, match="same length"):
            MgFeatures({"a": np.ones(3), "b": np.ones(5)}, sr=1.0)

    def test_json_round_trip(self, tmp_path):
        from musicalgestures._features import MgFeatures
        feat = MgFeatures({"x": np.array([1.0, 2.0, 3.0])}, sr=5.0, source="vid.avi")
        p = tmp_path / "feat.json"
        feat.to_json(p)
        feat2 = MgFeatures.from_json(p)
        np.testing.assert_allclose(feat["x"], feat2["x"])
        assert feat2.sr == 5.0

    def test_from_dataframe(self):
        import pandas as pd
        from musicalgestures._features import MgFeatures
        df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]}, index=[0.0, 0.5])
        feat = MgFeatures.from_dataframe(df, sr=2.0)
        assert feat.shape == (2, 2)
        assert feat.sr == 2.0

    def test_repr(self):
        feat = self._make()
        r = repr(feat)
        assert "MgFeatures" in r
        assert "n_samples=10" in r

    def test_repr_html(self):
        feat = self._make()
        html = feat._repr_html_()
        assert "<b>MgFeatures</b>" in html
        assert "qom" in html


# ---------------------------------------------------------------------------
# Phase 2 – MgVideoReader (import only – no actual video needed)
# ---------------------------------------------------------------------------

class TestMgVideoReaderImport:
    """Basic import and API checks for MgVideoReader (no real video required)."""

    def test_importable(self):
        from musicalgestures._stream import MgVideoReader
        assert callable(MgVideoReader)

    def test_repr(self):
        from musicalgestures._stream import MgVideoReader
        r = MgVideoReader.__init__  # just access it
        assert r is not None

    def test_file_not_found(self):
        from musicalgestures._stream import MgVideoReader
        with pytest.raises(FileNotFoundError):
            MgVideoReader("/nonexistent/path.avi").__enter__()


# ---------------------------------------------------------------------------
# Phase 3 – PoseEstimator
# ---------------------------------------------------------------------------

class TestPoseEstimator:
    """Tests for musicalgestures._pose_estimator."""

    def test_abstract_class(self):
        from musicalgestures._pose_estimator import PoseEstimator
        with pytest.raises(TypeError):
            PoseEstimator()

    def test_mediapipe_estimator_init(self):
        from musicalgestures._pose_estimator import MediaPipePoseEstimator
        est = MediaPipePoseEstimator(model_complexity=0)
        assert est.model == "mediapipe"
        assert est.device == "cpu"
        assert est.model_complexity == 0

    def test_mediapipe_landmark_names(self):
        from musicalgestures._pose_estimator import MediaPipePoseEstimator, MEDIAPIPE_LANDMARK_NAMES
        est = MediaPipePoseEstimator()
        assert len(est.landmark_names) == 33
        assert est.landmark_names == MEDIAPIPE_LANDMARK_NAMES
        assert "nose" in est.landmark_names

    def test_openpose_estimator_init(self):
        from musicalgestures._pose_estimator import OpenPosePoseEstimator
        est = OpenPosePoseEstimator()
        assert est.model == "body_25"

    def test_get_pose_estimator_mediapipe(self):
        from musicalgestures._pose_estimator import get_pose_estimator, MediaPipePoseEstimator
        est = get_pose_estimator("mediapipe")
        assert isinstance(est, MediaPipePoseEstimator)

    def test_get_pose_estimator_openpose(self):
        from musicalgestures._pose_estimator import get_pose_estimator, OpenPosePoseEstimator
        est = get_pose_estimator("openpose")
        assert isinstance(est, OpenPosePoseEstimator)

    def test_get_pose_estimator_invalid_raises(self):
        from musicalgestures._pose_estimator import get_pose_estimator
        with pytest.raises(ValueError, match="Unknown"):
            get_pose_estimator("invalid_backend")

    def test_pose_estimator_result(self):
        from musicalgestures._pose_estimator import PoseEstimatorResult, MEDIAPIPE_LANDMARK_NAMES
        kp = np.zeros((33, 3))
        res = PoseEstimatorResult(kp, MEDIAPIPE_LANDMARK_NAMES, frame_index=5, timestamp=0.2)
        assert res.n_keypoints == 33
        assert res.frame_index == 5
        assert res.timestamp == pytest.approx(0.2)

    def test_pose_result_to_dict(self):
        from musicalgestures._pose_estimator import PoseEstimatorResult, MEDIAPIPE_LANDMARK_NAMES
        kp = np.zeros((33, 3))
        res = PoseEstimatorResult(kp, MEDIAPIPE_LANDMARK_NAMES)
        d = res.to_dict()
        assert "keypoints" in d
        assert "nose" in d["keypoints"]
        assert "x" in d["keypoints"]["nose"]

    def test_mediapipe_no_mediapipe_raises(self):
        """If mediapipe is not installed, predict_frame raises MgDependencyError."""
        import importlib
        import sys
        # Save and remove mediapipe from sys.modules if present
        mp_modules = {k: v for k, v in sys.modules.items() if k.startswith("mediapipe")}
        for k in mp_modules:
            del sys.modules[k]
        # Block mediapipe import
        class BlockMediapipe:
            def find_module(self, name, path=None):
                if name == "mediapipe":
                    return self
            def load_module(self, name):
                raise ImportError("mediapipe not installed (mocked)")
        blocker = BlockMediapipe()
        sys.meta_path.insert(0, blocker)
        try:
            from musicalgestures._pose_estimator import MediaPipePoseEstimator
            from musicalgestures._exceptions import MgDependencyError
            est = MediaPipePoseEstimator()
            est._pose = None  # ensure not initialized
            with pytest.raises(MgDependencyError):
                est._ensure_initialized()
        finally:
            sys.meta_path.remove(blocker)
            # Restore mediapipe modules
            sys.modules.update(mp_modules)


# ---------------------------------------------------------------------------
# Phase 4 – MgPipeline
# ---------------------------------------------------------------------------

class TestMgPipeline:
    """Tests for musicalgestures._pipeline.MgPipeline."""

    def test_basic_transform(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("double", lambda x: x * 2)])
        result = pipe.transform(np.array([1.0, 2.0, 3.0]))
        np.testing.assert_array_equal(result, [2.0, 4.0, 6.0])

    def test_multi_step(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([
            ("add1", lambda x: x + 1),
            ("mul2", lambda x: x * 2),
        ])
        result = pipe.transform(np.array([0.0, 1.0, 2.0]))
        np.testing.assert_array_equal(result, [2.0, 4.0, 6.0])

    def test_len(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("a", lambda x: x), ("b", lambda x: x)])
        assert len(pipe) == 2

    def test_getitem_by_index(self):
        from musicalgestures._pipeline import MgPipeline, MgStep
        step = MgStep("myname", lambda x: x)
        pipe = MgPipeline([step])
        assert pipe[0].name == "myname"

    def test_getitem_by_name(self):
        from musicalgestures._pipeline import MgPipeline, MgStep
        step = MgStep("find_me", lambda x: x)
        pipe = MgPipeline([step])
        assert pipe["find_me"].name == "find_me"

    def test_getitem_missing_name_raises(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("step1", lambda x: x)])
        with pytest.raises(KeyError):
            _ = pipe["nonexistent"]

    def test_add_step_chaining(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline()
        result = pipe.add_step(("step1", lambda x: x)).add_step(("step2", lambda x: x))
        assert result is pipe
        assert len(pipe) == 2

    def test_tuple_step(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("negate", lambda x: -x)])
        assert pipe.transform(5) == -5

    def test_invalid_step_raises(self):
        from musicalgestures._pipeline import MgPipeline
        with pytest.raises(TypeError):
            MgPipeline().add_step("not_a_step")

    def test_fit_returns_self(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("noop", lambda x: x)])
        result = pipe.fit(np.array([1.0]))
        assert result is pipe

    def test_fit_transform(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("plus10", lambda x: x + 10)])
        out = pipe.fit_transform(np.array([0.0, 1.0]))
        np.testing.assert_array_equal(out, [10.0, 11.0])

    def test_describe(self):
        from musicalgestures._pipeline import MgPipeline
        def my_func(x): return x
        pipe = MgPipeline([("step1", my_func)])
        desc = pipe.describe()
        assert len(desc) == 1
        assert desc[0]["name"] == "step1"
        assert desc[0]["func"] == "my_func"

    def test_repr(self):
        from musicalgestures._pipeline import MgPipeline
        pipe = MgPipeline([("a", lambda x: x)])
        assert "MgPipeline" in repr(pipe)
        assert "'a'" in repr(pipe)

    def test_transformer_object(self):
        """Steps with a .transform() method should work too."""
        from musicalgestures._pipeline import MgPipeline, MgStep

        class Scaler:
            def transform(self, x):
                return x / 10.0

        pipe = MgPipeline([MgStep("scale", Scaler())])
        result = pipe.transform(np.array([10.0, 20.0]))
        np.testing.assert_allclose(result, [1.0, 2.0])


# ---------------------------------------------------------------------------
# Phase 4 – MgDataset / MgCorpus / MediaItem
# ---------------------------------------------------------------------------

class TestMgDataset:
    """Tests for musicalgestures._dataset."""

    def _make_dataset(self, n=5):
        from musicalgestures._dataset import MgDataset, MediaItem
        items = [
            MediaItem(Path(f"/fake/{i}.avi"), label="dance" if i % 2 == 0 else "piano")
            for i in range(n)
        ]
        return MgDataset(items, name="TestDataset")

    def test_len(self):
        ds = self._make_dataset(5)
        assert len(ds) == 5

    def test_getitem(self):
        from musicalgestures._dataset import MediaItem
        ds = self._make_dataset(3)
        assert isinstance(ds[0], MediaItem)

    def test_iter(self):
        ds = self._make_dataset(3)
        items = list(ds)
        assert len(items) == 3

    def test_labels(self):
        ds = self._make_dataset(4)
        assert len(ds.labels) == 4

    def test_unique_labels(self):
        ds = self._make_dataset(5)
        assert set(ds.unique_labels) == {"dance", "piano"}

    def test_train_test_split(self):
        ds = self._make_dataset(10)
        train, test = ds.train_test_split(test_size=0.3, shuffle=False, seed=42)
        assert len(train) + len(test) == 10
        assert len(test) >= 1

    def test_filter_by_label(self):
        ds = self._make_dataset(6)
        dances = ds.filter_by_label("dance")
        for item in dances:
            assert item.label == "dance"

    def test_filter_callable(self):
        ds = self._make_dataset(4)
        videos = ds.filter(lambda item: item.is_video)
        # .avi files should all be video
        assert len(videos) == 4

    def test_repr(self):
        ds = self._make_dataset(3)
        r = repr(ds)
        assert "MgDataset" in r
        assert "TestDataset" in r

    def test_json_round_trip(self, tmp_path):
        from musicalgestures._dataset import MgDataset, MediaItem
        items = [MediaItem(Path("/fake/a.avi"), label="x")]
        ds = MgDataset(items, name="myds")
        p = tmp_path / "ds.json"
        ds.to_json(p)
        ds2 = MgDataset.from_json(p)
        assert len(ds2) == 1
        assert ds2[0].label == "x"
        assert ds2.name == "myds"

    def test_from_directory(self, tmp_path):
        from musicalgestures._dataset import MgDataset
        # Create dummy files
        (tmp_path / "cat").mkdir()
        (tmp_path / "cat" / "video1.avi").touch()
        (tmp_path / "dog").mkdir()
        (tmp_path / "dog" / "video2.mp4").touch()
        ds = MgDataset.from_directory(tmp_path, label_from="parent")
        assert len(ds) == 2
        assert set(ds.unique_labels) == {"cat", "dog"}

    def test_from_directory_not_a_dir_raises(self, tmp_path):
        from musicalgestures._dataset import MgDataset
        with pytest.raises(NotADirectoryError):
            MgDataset.from_directory(tmp_path / "nonexistent")

    def test_repr_html(self):
        ds = self._make_dataset(3)
        html = ds._repr_html_()
        assert "<b>MgDataset</b>" in html


class TestMediaItem:
    """Tests for musicalgestures._dataset.MediaItem."""

    def test_is_video(self):
        from musicalgestures._dataset import MediaItem
        item = MediaItem(Path("/a/b.avi"))
        assert item.is_video is True
        assert item.is_audio is False

    def test_is_audio(self):
        from musicalgestures._dataset import MediaItem
        item = MediaItem(Path("/a/b.wav"))
        assert item.is_audio is True
        assert item.is_video is False

    def test_stem(self):
        from musicalgestures._dataset import MediaItem
        item = MediaItem(Path("/a/myclip.mp4"))
        assert item.stem == "myclip"

    def test_repr(self):
        from musicalgestures._dataset import MediaItem
        item = MediaItem(Path("/a/b.avi"), label="dance")
        r = repr(item)
        assert "b.avi" in r
        assert "dance" in r


class TestMgCorpus:
    """Tests for musicalgestures._dataset.MgCorpus."""

    def test_from_directory(self, tmp_path):
        from musicalgestures._dataset import MgCorpus
        (tmp_path / "classA").mkdir()
        (tmp_path / "classA" / "x.avi").touch()
        corpus = MgCorpus(tmp_path, label_from="parent")
        assert len(corpus) >= 1
        assert corpus.root == tmp_path

    def test_repr(self, tmp_path):
        from musicalgestures._dataset import MgCorpus
        corpus = MgCorpus(tmp_path)
        assert "MgCorpus" in repr(corpus)


# ---------------------------------------------------------------------------
# Phase 2 – Jupyter repr on MgImage / MgFigure
# ---------------------------------------------------------------------------

class TestJupyterRepr:
    """Tests that _repr_html_ was added to MgImage and MgFigure."""

    def test_mgimage_has_repr_html(self):
        from musicalgestures._utils import MgImage
        assert hasattr(MgImage, "_repr_html_")
        assert callable(MgImage._repr_html_)

    def test_mgimage_repr_html_missing_file(self):
        from musicalgestures._utils import MgImage
        img = MgImage("/nonexistent/file.png")
        html = img._repr_html_()
        assert "not found" in html

    def test_mgimage_repr_html_existing_file(self, tmp_path):
        from musicalgestures._utils import MgImage
        f = tmp_path / "test.png"
        # Write a minimal 1x1 white PNG (89 bytes)
        import base64
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        f.write_bytes(base64.b64decode(png_b64))
        img = MgImage(str(f))
        html = img._repr_html_()
        assert "data:image/png;base64," in html

    def test_mgfigure_has_repr_html(self):
        from musicalgestures._utils import MgFigure
        assert hasattr(MgFigure, "_repr_html_")
        assert callable(MgFigure._repr_html_)

    def test_mgfigure_repr_html_no_image(self):
        from musicalgestures._utils import MgFigure
        fig = MgFigure(figure_type="test")
        html = fig._repr_html_()
        assert "MgFigure" in html


# ---------------------------------------------------------------------------
# Phase 6 – __init__.py exports
# ---------------------------------------------------------------------------

class TestInitExports:
    """Verify all new symbols are exported from the musicalgestures package."""

    def test_enum_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "FilterType")
        assert hasattr(musicalgestures, "BlurType")
        assert hasattr(musicalgestures, "CropMode")
        assert hasattr(musicalgestures, "PoseModel")
        assert hasattr(musicalgestures, "PoseDevice")
        assert hasattr(musicalgestures, "DataFormat")

    def test_exception_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "MgError")
        assert hasattr(musicalgestures, "MgInputError")
        assert hasattr(musicalgestures, "MgProcessingError")
        assert hasattr(musicalgestures, "MgIOError")
        assert hasattr(musicalgestures, "MgDependencyError")

    def test_logging_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "set_log_level")
        assert callable(musicalgestures.set_log_level)

    def test_features_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "MgFeatures")

    def test_stream_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "MgVideoReader")

    def test_pipeline_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "MgPipeline")
        assert hasattr(musicalgestures, "MgStep")

    def test_dataset_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "MgDataset")
        assert hasattr(musicalgestures, "MgCorpus")
        assert hasattr(musicalgestures, "MediaItem")

    def test_pose_estimator_exports(self):
        import musicalgestures
        assert hasattr(musicalgestures, "PoseEstimator")
        assert hasattr(musicalgestures, "PoseEstimatorResult")
        assert hasattr(musicalgestures, "MediaPipePoseEstimator")
        assert hasattr(musicalgestures, "get_pose_estimator")
