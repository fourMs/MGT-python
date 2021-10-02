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

    def test_adjust_printlength_tw_width_0(self):
        pb = MgProgressbar()
        # spoof terminal window stuff
        pb.tw_width = 0
        pb.could_not_get_terminal_window = False
        assert pb.adjust_printlength() == None

    def test_adjust_printlength_no_terminal(self):
        pb = MgProgressbar()
        # spoof terminal window stuff
        pb.tw_width = 1
        pb.could_not_get_terminal_window = True
        assert pb.adjust_printlength() == None

    def test_adjust_printlength_shorten_by_1(self):
        pb = MgProgressbar()
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - 1
        pb.could_not_get_terminal_window = False
        suffix_before = pb.suffix
        length_before = pb.length
        pb.adjust_printlength()
        assert pb.suffix == suffix_before
        # shortened it by 1
        assert pb.length == length_before - 1

    def test_adjust_printlength_shorten_to_1(self):
        pb = MgProgressbar()
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length + 1
        pb.could_not_get_terminal_window = False
        suffix_before = pb.suffix
        pb.adjust_printlength()
        assert pb.suffix == suffix_before
        assert pb.length == 1

    def test_adjust_printlength_only_remove_suffix(self):
        my_suffix = "very long testsuffix"
        pb = MgProgressbar(suffix=my_suffix, length=len(my_suffix))
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length
        pb.could_not_get_terminal_window = False
        length_before = pb.length
        pb.adjust_printlength()
        assert pb.suffix == ""
        assert pb.length == length_before

    def test_adjust_printlength_remove_suffix_and_shorten(self):
        pb = MgProgressbar(suffix="testsuffix")
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length - 1
        pb.could_not_get_terminal_window = False
        length_before = pb.length
        pb.adjust_printlength()
        assert pb.suffix == ""
        assert pb.length < length_before

    def test_adjust_printlength_only_remove_prefix_and_suffix(self):
        my_suffix = "very long testsuffix"
        my_prefix = "very long testprefix"
        pb = MgProgressbar(suffix=my_suffix, prefix=my_prefix, length=len(my_suffix))
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length - len(pb.suffix)
        pb.could_not_get_terminal_window = False
        length_before = pb.length
        pb.adjust_printlength()
        assert pb.suffix == ""
        assert pb.prefix == ""
        assert pb.length == length_before

    def test_adjust_printlength_only_remove_prefix_and_suffix_and_shorten(self):
        my_suffix = "very long testsuffix"
        my_prefix = "very long testprefix"
        pb = MgProgressbar(suffix=my_suffix, prefix=my_prefix, length=len(my_suffix))
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length - len(pb.suffix) - 1
        pb.could_not_get_terminal_window = False
        length_before = pb.length
        pb.adjust_printlength()
        assert pb.suffix == ""
        assert pb.prefix == ""
        assert pb.length == length_before - 1

    def test_adjust_printlength_display_only_percent(self):
        my_suffix = "very long testsuffix"
        my_prefix = "very long testprefix"
        pb = MgProgressbar(suffix=my_suffix, prefix=my_prefix, length=len(my_suffix))
        _current_length = len(pb.prefix) + pb.length + pb.decimals + len(pb.suffix) + 10
        # spoof terminal window stuff
        pb.tw_width = _current_length - pb.length - len(pb.suffix) - len(pb.prefix)
        pb.could_not_get_terminal_window = False
        assert pb.display_only_percent == False
        pb.adjust_printlength()
        assert pb.suffix == ""
        assert pb.prefix == ""
        assert pb.display_only_percent == True

    def test_progress(self):
        pb = MgProgressbar(total=100)
        assert pb.progress(1) == None

    def test_progress_only_percent(self):
        pb = MgProgressbar(total=100)
        # spoof terminal window stuff
        pb.could_not_get_terminal_window = True
        pb.display_only_percent = True
        pb.tw_width = 1
        assert pb.progress(1) == None
        assert pb.display_only_percent == True

    def test_repr(self):
        pb = MgProgressbar(total=100)
        assert print(pb) == None


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
def testvideo_avi_silent(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testvideo.avi"
    target_name_silent = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testvideo_silent.avi"
    testvideo_avi = extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)
    cmd = ["ffmpeg", "-y", "-i", target_name, "-an", target_name_silent]
    ffmpeg_cmd(cmd, get_length(testvideo_avi), stream=False)
    return target_name_silent

@pytest.fixture(scope="class")
def testimage(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testimage.png"
    testimage = get_first_frame_as_image(musicalgestures.examples.dance, target_name=target_name)
    return testimage

@pytest.fixture(scope="class")
def testaudio(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testaudio.wav"
    testaudio = extract_wav(musicalgestures.examples.dance, target_name=target_name)
    return testaudio

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


def pass_if_lengths_match(file_1, file_2, tolerance=1):
    frames_in = get_framecount(file_1)
    frames_out = get_framecount(file_2, fast=False)
    # many ffmpeg conversions/filters have the issue of adding an extra fram into the result
    # so if the length difference between the input and output is +/- 1 frame, then we are okay
    assert abs(frames_in - frames_out) <= tolerance


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
        pass_if_lengths_match(startfile, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == fex_to
        assert target_name == result


class Test_convert_to_avi:
    def test_output(self, tmp_path, testvideo_mp4):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.avi"
        result = convert_to_avi(testvideo_mp4, target_name=target_name)
        pass_if_lengths_match(testvideo_mp4, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_convert_to_mp4:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.mp4"
        result = convert_to_mp4(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".mp4"
        assert target_name == result


class Test_convert_to_webm:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_converted.webm"
        result = convert_to_webm(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".webm"
        assert target_name == result


class Test_cast_into_avi:
    def test_output(self, tmp_path, testvideo_mp4):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_casted.avi"
        result = cast_into_avi(testvideo_mp4, target_name=target_name)
        pass_if_lengths_match(testvideo_mp4, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_extract_subclip:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_trimmed.avi"
        result = extract_subclip(testvideo_avi, 3, 4, target_name=target_name)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result

    def test_length(self, tmp_path):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_trimmed.avi"
        result = extract_subclip(musicalgestures.examples.dance, 3, 4, target_name=target_name)
        fps = get_fps(musicalgestures.examples.dance)
        result_framecount = get_framecount(result)
        assert fps - 1 <= result_framecount <= fps + 1


class Test_rotate_video:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_rotated.avi"
        result = rotate_video(testvideo_avi, 90, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_convert_to_grayscale:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_grayscale.avi"
        result = convert_to_grayscale(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_framediff_ffmpeg:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_framediff.avi"
        result = framediff_ffmpeg(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result, tolerance=2)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_threshold_ffmpeg:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_threshold.avi"
        result = threshold_ffmpeg(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_motionvideo_ffmpeg:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_motionvideo.avi"
        result = motionvideo_ffmpeg(testvideo_avi, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result, tolerance=2)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_motiongrams_ffmpeg:
    def test_output(self, tmp_path):
        target_name_x = str(tmp_path).replace("\\", "/") + "/testmotiongram_x.png"
        target_name_y = str(tmp_path).replace("\\", "/") + "/testmotiongram_y.png"
        testmotiongram_x, testmotiongram_y = motiongrams_ffmpeg(musicalgestures.examples.pianist, target_name_x=target_name_x, target_name_y=target_name_y)
        assert os.path.isfile(testmotiongram_x) == True
        assert os.path.isfile(testmotiongram_y) == True
        assert os.path.splitext(testmotiongram_x)[1] == ".png"
        assert os.path.splitext(testmotiongram_y)[1] == ".png"
        assert target_name_x == testmotiongram_x
        assert target_name_y == testmotiongram_y


class Test_crop_ffmpeg:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_cropped.avi"
        result = crop_ffmpeg(testvideo_avi, 50, 50, 0, 0, target_name=target_name)
        pass_if_lengths_match(testvideo_avi, result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".avi"
        assert target_name == result


class Test_extract_wav:
    def test_output(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/testvideo_audio.wav"
        result = extract_wav(testvideo_avi, target_name=target_name)
        length_in = get_length(testvideo_avi)
        length_out = get_length(result)
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".wav"
        assert target_name == result
        assert abs(length_in - length_out) <= 0.05


class Test_ffprobe:
    def test_nofile(self, tmp_path):
        test_input = str(tmp_path).replace("\\", "/") + "/thisfiledoesnotexist.mp4"
        with pytest.raises(FileNotFoundError):
            ffprobe(test_input)

    def test_video(self, testvideo_avi):
        result = ffprobe(testvideo_avi)
        assert type(result) == str
        assert len(result) > 0

    def test_image(self, testimage):
        result = ffprobe(testimage)
        assert type(result) == str
        assert len(result) > 0

    def test_audio(self, testaudio):
        result = ffprobe(testaudio)
        assert type(result) == str
        assert len(result) > 0


class Test_get_widthheight:
    def test_get_widthheight(self):
        width, height = get_widthheight(musicalgestures.examples.dance)
        assert width == 518
        assert height == 496


class Test_has_audio:
    def test_with_audio(self, testvideo_avi):
        assert has_audio(testvideo_avi) == True

    def test_without_audio(self, testvideo_avi_silent):
        assert has_audio(testvideo_avi_silent) == False


class Test_get_length:
    def test_video(self):
        result = get_length(musicalgestures.examples.dance)
        assert type(result) == float
        assert result == 62.84

    def test_audio(self, testaudio):
        result = get_length(testaudio)
        assert type(result) == float
        assert result == 62.86


class Test_get_framecount:
    def test_get_framecount(self):
        result = get_framecount(musicalgestures.examples.dance)
        assert type(result) == int
        assert result == 1571


class Test_get_fps:
    def test_get_fps(self):
        result = get_fps(musicalgestures.examples.dance)
        assert type(result) == float
        assert result == 25.0


class Test_get_first_frame_as_image:
    def test_get_first_frame_as_image(self, tmp_path):
        target_name = str(tmp_path).replace("\\", "/") + "/first_frame.png"
        result = get_first_frame_as_image(musicalgestures.examples.dance, target_name=target_name)
        assert type(result) == str
        assert os.path.isfile(result) == True
        assert os.path.splitext(result)[1] == ".png"


class Test_get_box_video_ratio:
    def test_normal(self):
        result = get_box_video_ratio(musicalgestures.examples.dance)
        assert result == 1
    
    def test_small(self):
        result = get_box_video_ratio(musicalgestures.examples.dance, box_width=100)
        assert result == 0.17374517374517376


class Test_audio_dilate:
    def test_2x(self, tmp_path, testaudio):
        target_name = str(tmp_path).replace("\\", "/") + "/test_dilated.wav"
        result = audio_dilate(testaudio, dilation_ratio=0.5, target_name=target_name)
        length_in = get_length(testaudio)
        length_out = get_length(result)
        assert abs(length_out - (2 * length_in)) < 0.05


    def test_half(self, tmp_path, testaudio):
        target_name = str(tmp_path).replace("\\", "/") + "/test_dilated.wav"
        result = audio_dilate(testaudio, dilation_ratio=2, target_name=target_name)
        length_in = get_length(testaudio)
        length_out = get_length(result)
        assert abs(length_in - (2 * length_out)) < 0.05


class Test_embed_audio_in_video:
    def test_embed_audio_in_video(self, tmp_path, testvideo_avi_silent, testaudio):
        state_before = has_audio(testvideo_avi_silent)
        embed_audio_in_video(testaudio, testvideo_avi_silent)
        state_after = has_audio(testvideo_avi_silent)
        assert state_before == False
        assert state_after == True


class Test_ffmpeg_cmd:
    def test_expected(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/test_result.mp4"
        cmd = ['ffmpeg', '-y', '-i', testvideo_avi, target_name]
        ffmpeg_cmd(cmd, get_length(testvideo_avi))
        assert os.path.isfile(target_name) == True
        assert os.path.splitext(target_name)[1] == ".mp4"

    def test_unexpected(self, tmp_path, testvideo_avi):
        target_name = str(tmp_path).replace("\\", "/") + "/test_result.mp4"
        cmd = ['ffmpeg', '-y', '-i', testvideo_avi, '-stupid', 'argument', target_name]
        with pytest.raises(FFmpegError):
            ffmpeg_cmd(cmd, get_length(testvideo_avi))


class Test_str2sec:
    def test_str2sec(self):
        assert str2sec("01:02:03") == 3723


class Test_wrap_str:
    def test_expected_wrap(self):
        assert wrap_str("one two") == '"one two"'

    def test_expected_no_wrap(self):
        assert wrap_str("onetwo") == "onetwo"


class Test_unwrap_str:
    def test_expected_unwrap(self):
        assert unwrap_str("'one two'") == 'one two'
        assert unwrap_str('"one two"') == "one two"

    def test_expected_no_unwrap(self):
        assert unwrap_str("one two") == "one two"


class Test_in_colab:
    def test_in_colab(self):
        assert in_colab() == False