import musicalgestures
from musicalgestures._utils import *
import numpy as np
import os
import itertools
import pytest


class Test_MgProgressbar:
    def test_init(self):
        pb = MgProgressbar(total=42, time_limit=0.42, prefix="Test",
                           suffix="Done", decimals=3, length=30, fill="@")
        assert pb.total == 41
        assert pb.time_limit == 0.42
        assert pb.prefix == "Test"
        assert pb.suffix == "Done"
        assert pb.decimals == 3
        assert pb.length == 30
        assert pb.fill == "@"


class Test_roundup:
    def test_positive(self):
        assert roundup(10, 4) == 12

    def test_negative(self):
        assert roundup(-71, 3) == -69


class Test_clamp:
    def test_int_hi(self):
        assert clamp(100, 1, 42) == 42

    def test_int_lo(self):
        assert clamp(1, 42, 200) == 42

    def test_int_normal(self):
        assert clamp(100, 42, 200) == 100

    def test_float_hi(self):
        assert clamp(0.942, 0.4, 0.9) == 0.9

    def test_float_lo(self):
        assert clamp(0.1, 0.42, 0.9) == 0.42

    def test_float_normal(self):
        assert clamp(0.42, 0.1, 0.9) == 0.42


class Test_scale_num:
    def test_inrange(self):
        assert scale_num(13.1, 12.2, 15.3, -42.42,
                         42.42) == -17.789032258064516

    def test_outrange_lo(self):
        assert scale_num(13.1, 14.2, 15.3, -42.42,
                         42.42) == -127.25999999999986

    def test_outrange_hi(self):
        assert scale_num(16.1, 14.2, 15.3, -42.42, 42.42) == 104.12181818181817


class Test_scale_array:
    def test_positive(self):
        assert scale_array(np.array([1, 2, 3]), 0.1, 0.3).all(
        ) == np.array([0.1, 0.2, 0.3]).all()

    def test_negative(self):
        assert scale_array(
            np.array([1, 2, 3]), -0.1, -0.3).all() == np.array([-0.1, -0.2, -0.3]).all()


class Test_generate_outfilename:
    def test_increment_once(self, tmp_path):
        p = tmp_path / "testfile.txt"
        p.write_text("test")
        assert os.path.basename(generate_outfilename(str(p))) == "testfile_0.txt"

    def test_increment_twice(self, tmp_path):
        p1 = tmp_path / "testfile.txt"
        p1.write_text("test")
        p2 = tmp_path / "testfile_0.txt"
        p2.write_text("test")
        assert os.path.basename(generate_outfilename(str(p1))) == "testfile_1.txt"


class Test_get_frame_planecount:
    def test_3plane(self):
        frame = np.random.rand(3, 1920, 1080)
        assert get_frame_planecount(frame) == 3

    def test_1plane(self):
        frame = np.random.rand(1920, 1080)
        assert get_frame_planecount(frame) == 1


class Test_frame2ms:
    def test_expected(self):
        assert frame2ms(1234, 56) == 22036

    def test_unexpected(self):
        assert frame2ms(1234.56, 78.9) == 15647


class Test_MgImage:
    def test_init(self):
        img = MgImage("test_image.png")
        assert img.filename == "test_image.png"
        assert img.of == "test_image"
        assert img.fex == ".png"


class Test_MgFigure:
    def test_init(self):
        import matplotlib.pyplot as plt
        x = np.arange(0, 5, 0.1)
        y = np.sin(x)
        data = {"x": x, "y": y}
        plt.plot(x, y)
        fig = MgFigure(figure=plt, figure_type="testy.test", data=data, layers="layers", image="image")
        assert fig.figure == plt
        assert fig.figure_type == "testy.test"
        assert fig.data["x"].all() == data["x"].all()
        assert fig.data["y"].all() == data["y"].all()
        assert fig.layers == "layers"
        assert fig.image == "image"


@pytest.fixture(scope="class")
def testvideo_mp4(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testvideo.avi"
    testvideo_avi = extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)
    testvideo_mp4 = convert_to_mp4(testvideo_avi)
    return testvideo_mp4

@pytest.fixture(scope="class")
def testvideo_avi(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testvideo.avi"
    testvideo_avi = extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi

@pytest.fixture(scope="class")
def format_pairs():
    video_formats = ['.avi', '.mp4', '.mov', '.mkv', '.mpg', '.mpeg', '.webm', '.ogg']
    all_combinations = list(itertools.combinations(video_formats, 2))
    return all_combinations


class Test_pass_if_containers_match:
    def test_match(self):
        pass_if_containers_match("file_1.avi", "file_2.avi")
        assert 42 == 42 # no error thrown

    def test_mismatch(self):
        with pytest.raises(WrongContainer):
            pass_if_containers_match("file_1.avi", "file_2.mp4")


class Test_pass_if_container_is:
    def test_match(self):
        pass_if_container_is(".avi", "file.avi")
        assert 42 == 42 # no error thrown

    def test_mismatch(self):
        with pytest.raises(WrongContainer):
            pass_if_container_is(".avi", "file_2.mp4")


class Test_convert:
    @pytest.mark.parametrize("execution_number", range(len(list(itertools.combinations(['.avi', '.mp4', '.mov', '.mkv', '.mpg', '.mpeg', '.webm', '.ogg'], 2)))))
    def test_output(self, format_pairs, execution_number, tmp_path, testvideo_avi):
        fex_from, fex_to = format_pairs[execution_number]
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted" + fex_to
        startfile = ""
        if fex_from != '.avi':
            startfile = convert(testvideo_avi, os.path.splitext(testvideo_avi)[0] + fex_from)
        else:
            startfile = testvideo_avi
        result = convert(startfile, target_name)
        # length_in = get_length(startfile)
        # length_out = get_length(result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == fex_to
        assert target_name == result
        # assert length_in == length_out # often fails due to ffmpeg


class Test_convert_to_avi:
    # @pytest.mark.xfail(raises=AssertionError)
    def test_output(self, tmp_path, testvideo_mp4):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.avi"
        testvideo_avi = convert_to_avi(testvideo_mp4, target_name=target_name)
        # length_in = get_length(testvideo_mp4)
        # length_out = get_length(testvideo_avi)
        assert os.path.isfile(testvideo_avi) == True
        assert os.path.splitext(testvideo_avi)[1] == ".avi"
        assert target_name == testvideo_avi
        # assert length_in == length_out # this will fail due to ffmpeg bug: https://trac.ffmpeg.org/ticket/9443#ticket


class Test_convert_to_mp4:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.mp4"
        testvideo_mp4 = convert_to_mp4(testvideo_avi, target_name=target_name)
        length_in = get_length(testvideo_avi)
        length_out = get_length(testvideo_mp4)
        assert os.path.isfile(testvideo_mp4) == True
        assert os.path.splitext(testvideo_mp4)[1] == ".mp4"
        assert target_name == testvideo_mp4
        assert length_in == length_out


class Test_convert_to_webm:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.webm"
        testvideo_webm = convert_to_webm(testvideo_avi, target_name=target_name)
        assert os.path.isfile(testvideo_webm) == True
        assert os.path.splitext(testvideo_webm)[1] == ".webm"
        assert target_name == testvideo_webm


class Test_cast_into_avi:
    def test_output(self, tmp_path, testvideo_mp4):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_casted.avi"
        testvideo_casted_avi = cast_into_avi(testvideo_mp4, target_name=target_name)
        assert os.path.isfile(testvideo_casted_avi) == True
        assert os.path.splitext(testvideo_casted_avi)[1] == ".avi"
        assert target_name == testvideo_casted_avi