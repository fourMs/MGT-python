import os
import subprocess
import tempfile
from enum import Enum
from typing import Dict, Union
from pathlib import Path
from functools import partial
from musicalgestures._video import MgVideo
from musicalgestures._utils import (ffmpeg_cmd, get_length,
                                    generate_outfilename, get_widthheight,
                                    has_audio)


class Projection(Enum):
    """
    same as https://ffmpeg.org/ffmpeg-filters.html#v360.
    """

    e = 0
    equirect = 1
    c3x2 = 2
    c6x1 = 3
    c1x6 = 4
    eac = 5  # Equi-Angular Cubemap.
    flat = 6
    gnomonic = 7
    rectilinear = 8  # Regular video.
    dfisheye = 9  # Dual fisheye.
    barrel = 10
    fb = 11
    barrelsplit = 12  # Facebook’s 360 formats.
    sg = 13  # Stereographic format.
    mercator = 14  # Mercator format.
    ball = 15  # Ball format, gives significant distortion toward the back.
    hammer = 16  # Hammer-Aitoff map projection format.
    sinusoidal = 17  # Sinusoidal map projection format.
    fisheye = 18  # Fisheye projection.
    pannini = 19  # Pannini projection.
    cylindrical = 20  # Cylindrical projection.
    perspective = 21  # Perspective projection. (output only)
    tetrahedron = 22  # Tetrahedron projection.
    tsp = 23  # Truncated square pyramid projection.
    he = 24
    hequirect = 25  # Half equirectangular projection.
    equisolid = 26  # Equisolid format.
    og = 27  # Orthographic format.
    octahedron = 28  # Octahedron projection.
    cylindricalea = 29

    equirectangular = 30  # extra option for equirectangular
    erp = 31
    gopro_360 = 32  # special gopro .360 format

    def __str__(self):
        # collapse all aliases of erp
        if self.name in ["equirectangular", "erp", "e"]:
            return "equirect"
        else:
            return self.name

    def __eq__(self, other):
        # collapse all aliases of erp
        if self.name in ["equirectangular", "erp", "e", "equirect"] and other.name in [
            "equirectangular",
            "erp",
            "e",
            "equirect",
        ]:
            return True
        elif self.name == other.name:
            return True
        else:
            return False


# TODO: add settings for cameras and files
CAMERA = {
    "gopro max": {
        "ext": "360",
        "projection": Projection.eac,
    },
    "insta360 x3": {
        "ext": "insv",
        "projection": Projection.fisheye,
    },
    "garmin virb 360": {
        "ext": "MP4",
        "projection": Projection.erp,
    },
    "ricoh theta xs00": {
        "ext": "MP4",
        "projection": Projection.erp,
    },
    "gopro max2": {
        "ext": "360",
        "projection": Projection.gopro_360,   # probe-scaled; experimental
    },
    # legacy rotated dual-fisheye: use _remap360.flatten_theta360, plain
    # v360=dfisheye cannot unwrap the 90-degree in-plane rotation
    "ricoh theta s": {
        "ext": "MP4",
        "projection": Projection.dfisheye,
    },
}


def make_seam_mask(width: int, height: int, feather_deg: float = 8.0):
    """
    Column mask for feather-blending two hemispheres on an equirectangular
    canvas: 0 where the front lens (yaw 0) should be used, 255 for the back
    lens (yaw 180), with a linear ramp of ±feather_deg around the seams at
    longitude ±90°.
    Args:
        width (int): Mask width in pixels (full 360° canvas).
        height (int): Mask height in pixels.
        feather_deg (float): Half-width of the blend ramp in degrees.
    Returns:
        np.ndarray: uint8 mask of shape (height, width).
    """
    import numpy as np

    lon = (np.arange(width) + 0.5) / width * 360.0 - 180.0
    dist = np.minimum(np.abs(lon - 90.0), np.abs(lon + 90.0))
    back = np.abs(lon) > 90.0
    ramp = np.where(back, 128 + 127 * (dist / feather_deg),
                    128 - 127 * (dist / feather_deg))
    row = np.where(dist >= feather_deg,
                   np.where(back, 255.0, 0.0), ramp).astype(np.uint8)
    return np.tile(row, (height, 1))


def calibrate_dual_fisheye_fov(front_file, back_file, time_s: float = 1.0,
                               candidates=None, print_result: bool = False):
    """
    Estimate the effective lens field of view of a dual-fisheye pair
    (e.g. the two .insv files of an Insta360 camera) by projecting one frame
    of each lens to equirectangular at candidate FOVs and measuring the
    photometric mismatch in the seam bands at longitude ±90°.
    Args:
        front_file (str): Video of the front lens.
        back_file (str): Video of the back lens.
        time_s (float): Timestamp of the probe frame.
        candidates (list): FOVs (degrees) to try. Default 185–203.
    Returns:
        float: The FOV with the smallest seam mismatch.
    """
    import cv2
    import numpy as np

    if candidates is None:
        candidates = [185, 188, 191, 193, 195, 197, 199, 201, 203]
    with tempfile.TemporaryDirectory() as tmp:
        frames = {}
        for name, f in (("front", front_file), ("back", back_file)):
            out = os.path.join(tmp, f"{name}.png")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(time_s),
                            "-i", str(f), "-frames:v", "1", out], check=True)
            frames[name] = out
        best = (None, float("inf"))
        for fov in candidates:
            eqs = {}
            for name, yaw in (("front", 0), ("back", 180)):
                out = os.path.join(tmp, f"{name}_{fov}.png")
                vf = (f"v360=input=fisheye:output=e:ih_fov={fov}:"
                      f"iv_fov={fov}:yaw={yaw}:w=1440:h=720")
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i",
                                frames[name], "-vf", vf, out], check=True)
                eqs[name] = cv2.imread(out, cv2.IMREAD_GRAYSCALE).astype(float)
            h, w = eqs["front"].shape
            band = int(w * 6 / 360)
            errs = []
            for c in (w // 4, 3 * w // 4):
                fb = eqs["front"][h // 5:4 * h // 5, c - band:c + band]
                bb = eqs["back"][h // 5:4 * h // 5, c - band:c + band]
                valid = (fb > 8) & (bb > 8)
                if valid.sum() > 100:
                    errs.append(np.abs(fb - bb)[valid].mean())
            score = float(np.mean(errs)) if errs else float("inf")
            if print_result:
                print(f"  fov {fov}: seam mismatch {score:.2f}")
            if score < best[1]:
                best = (float(fov), score)
    if print_result:
        print(f"=> calibrated lens FOV: {best[0]}")
    return best[0]


def stitch_dual_fisheye(front_file, back_file, target_name: str = None,
                        fov: float = None, feather_deg: float = 8.0,
                        width: int = None, height: int = None,
                        crf: int = 21, preset: str = "fast",
                        print_cmd: bool = False):
    """
    Stitch a dual-fisheye pair (two single-lens files, e.g. Insta360
    `_00_`/`_10_` .insv) into one equirectangular video with a feathered
    seam blend. Each lens is projected to equirectangular separately
    (back lens at yaw 180) and the two are merged with a soft column mask,
    which avoids the hard seams of a plain `v360=dfisheye` conversion.
    Audio is taken from the front-lens file when present.
    Args:
        front_file (str): Video of the front lens.
        back_file (str): Video of the back lens.
        target_name (str): Output path. Defaults to `<front>_equirect.mp4`.
        fov (float): Lens FOV in degrees. None runs
            `calibrate_dual_fisheye_fov` on a probe frame first.
        feather_deg (float): Half-width of the seam blend in degrees.
        width, height (int): Output size. Defaults to lens height × 2 by
            lens height (2:1 equirectangular).
        crf (int), preset (str): x264 rate control.
    Returns:
        str: Path of the stitched video.
    """
    import cv2

    front_file, back_file = str(front_file), str(back_file)
    if fov is None:
        fov = calibrate_dual_fisheye_fov(front_file, back_file,
                                         print_result=print_cmd)
    if width is None or height is None:
        _, lens_h = get_widthheight(front_file)
        height = height or lens_h // 2
        width = width or 2 * height
    if target_name is None:
        target_name = os.path.splitext(front_file)[0] + "_equirect.mp4"
    target_name = generate_outfilename(target_name)

    mask_file = os.path.join(tempfile.mkdtemp(prefix="mgt360_"), "seam.png")
    cv2.imwrite(mask_file, make_seam_mask(width, height, feather_deg))

    proj = (f"v360=input=fisheye:output=e:ih_fov={fov}:iv_fov={fov}"
            f":w={width}:h={height}")
    # the mask is fed as a single frame (NOT -loop 1): framesync's default
    # eof_action=repeat holds it for the whole run while the lens streams
    # set the duration — an infinitely looped mask would keep maskedmerge
    # producing frames forever on inputs that have no audio stream to trip
    # ffmpeg's -shortest
    graph = (f"[0:v]{proj},format=gbrp[f];"
             f"[1:v]{proj}:yaw=180,format=gbrp[b];"
             f"[2:v]format=gray,scale={width}:{height}[m];"
             f"[f][b][m]maskedmerge,format=yuv420p[out]")
    cmds = ["ffmpeg", "-y", "-i", front_file, "-i", back_file,
            "-i", mask_file,
            "-filter_complex", graph, "-map", "[out]"]
    if has_audio(front_file):
        cmds += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"]
    cmds += ["-shortest", "-c:v", "libx264", "-crf", str(crf),
             "-preset", preset, target_name]
    ffmpeg_cmd(cmds, get_length(front_file),
               pb_prefix="Stitching dual fisheye:", print_cmd=print_cmd)
    return target_name


class Mg360Video(MgVideo):
    """
    Class for 360 videos.
    """

    def __init__(
        self,
        filename: str,
        projection: Union[str, Projection],
        camera: str = None,
        **kwargs,
    ):
        """
        Args:
            filename (str): Path to the video file.
            projection (str, Projection): Projection type.
            camera (str): Camera type.
        """
        super().__init__(filename, **kwargs)
        self.filename = os.path.abspath(self.filename)
        self.projection = self._parse_projection(projection)

        if camera is None:
            self.camera = None
        elif camera.lower() in CAMERA:
            self.camera = CAMERA[camera.lower()]
        else:
            raise Warning(f"Camera type '{camera}' not recognized.")

        # override self.show() with extra ipython_kwarg embed=True
        self.show = partial(self.show, embed=True)

    @classmethod
    def from_dual_fisheye(cls, front_file, back_file, camera: str = None,
                          **stitch_kwargs):
        """
        Stitch a dual-fisheye pair (e.g. the `_00_`/`_10_` .insv files of an
        Insta360 camera) into an equirectangular video and open it as an
        Mg360Video. See `stitch_dual_fisheye` for the stitching options
        (`fov=None` auto-calibrates the lens FOV on a probe frame).
        """
        stitched = stitch_dual_fisheye(front_file, back_file, **stitch_kwargs)
        return cls(stitched, Projection.equirect, camera=camera)

    def convert_projection(
        self,
        target_projection: Union[Projection, str],
        options: Dict[str, str] = None,
        print_cmd: bool = False,
        test: bool = False,
    ):
        """
        Convert the video to a different projection.
        Args:
            target_projection (Projection): Target projection.
            options (Dict[str, str], optional): Options for the conversion. Defaults to None.
            print_cmd (bool, optional): Print the ffmpeg command. Defaults to False.
        """
        target_projection = self._parse_projection(target_projection)

        if target_projection == self.projection:
            print(f"{self} is already in target projection {target_projection}.")
            return
        elif self.projection == Projection.gopro_360:
            if test:
                print(
                    f"=> Test mode: would convert {self.filename} to {target_projection} with options {options}."
                )

            # use special gopro conversion scripts
            assert target_projection in [
                Projection.equirect,
                Projection.equirectangular,
            ], (
                f"Invalid target projection from gopro_360: {target_projection}, only equirect and equirectangular are supported."
            )

            from musicalgestures._remap360 import flatten_gopro360
            output_name = flatten_gopro360(self.filename)
            self.filename = output_name
            self.projection = target_projection

        else:
            output_name = generate_outfilename(
                f"{self.filename.split('.')[0]}_{target_projection}.mp4"
            )

            # parse options
            if options:
                options = "".join([f"{k}={options[k]}:" for k in options])[:-1]
                cmds = [
                    "ffmpeg",
                    "-i",
                    self.filename,
                    "-vf",
                    f"v360={self.projection}:{target_projection}:{options}",
                    output_name,
                ]
            else:
                cmds = [
                    "ffmpeg",
                    "-i",
                    self.filename,
                    "-vf",
                    f"v360={self.projection}:{target_projection}",
                    output_name,
                ]

            # execute conversion
            ffmpeg_cmd(
                cmds,
                get_length(self.filename),
                pb_prefix=f"Converting projection to {target_projection}:",
                print_cmd=print_cmd,
            )
            self.filename = output_name
            self.projection = target_projection

    def _parse_projection(self, projection: Union[str, Projection]):
        """
        Parse projection type.
        Args:
            projection (str): Projection type.
        """
        if isinstance(projection, str):
            try:
                return Projection[projection.lower()]
            except KeyError:
                raise ValueError(
                    f"Projection type '{projection}' not recognized. See `Projection` for available options."
                )
        elif isinstance(projection, Projection):
            return projection
        else:
            raise TypeError(f"Unsupported projection type: '{type(projection)}'.")


## testing gopro_360 conversion
if __name__ == "__main__":
    video = Mg360Video("2023-01-01-GS010008.360", Projection.gopro_360)
    video.convert_projection(
        Projection.equirect,
        options={"-r": "0:180:0", "-s": "00:01:10", "-t": "00:01:20"},
        test=True,
    )
    print(f"=> Converted video path: {video.filename}")
    print(f"=> Converted video projection: {video.projection}")

    video = Mg360Video("2023-01-01-GS010008.360", Projection.gopro_360)
    video.convert_projection(
        Projection.dfisheye,
        options={"-s": "00:01:10", "-t": "00:01:20"},
        test=True,
    )
    print(f"=> Converted video path: {video.filename}")
    print(f"=> Converted video projection: {video.projection}")
