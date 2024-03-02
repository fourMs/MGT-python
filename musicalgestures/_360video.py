import os
from enum import Enum
from functools import partial
from musicalgestures._video import MgVideo
from musicalgestures._utils import ffmpeg_cmd, get_length, generate_outfilename


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

    def __str__(self):
        return self.name


# TODO: add settings for cameras and files
CAMERA = {
    "gopro max": {},
    "insta360 x3": {},
    "garmin virb 360": {},
    "ricoh theta xs00": {},
}


class Mg360Video(MgVideo):
    """
    Class for 360 videos.
    """

    def __init__(
        self,
        filename: str,
        projection: str,
        camera: str = None,
        **kwargs,
    ):
        """
        Args:
            filename (str): Path to the video file.
            projection (str): Projection type.
            camera (str): Camera type.
        """
        super().__init__(filename, **kwargs)
        self.filename = os.path.abspath(self.filename)

        try:
            self.projection = Projection[projection.lower()]
        except KeyError:
            raise ValueError(
                f"Projection type '{projection}' not recognized. See `Projection` for available options."
            )

        if camera is None:
            self.camera = None
        elif camera.lower() in CAMERA:
            self.camera = CAMERA[camera.lower()]
        else:
            raise Warning(f"Camera type '{camera}' not recognized.")

        # override self.show() with extra ipython kwarg embed=True
        self.show = partial(self.show, embed=True)

    def convert_projection(
        self, target_projection: Projection | str, options: dict[str, str] = None
    ):
        """
        Convert the video to a different projection.
        Args:
            target_projection (Projection): Target projection.
            options (dict[str, str], optional): Options for the conversion. Defaults to None.
        """
        if target_projection == self.projection:
            return
        else:
            output_name = generate_outfilename(
                f"{self.filename.split('.')[0]}_{target_projection}.mp4"
            )
            # convert str to Projection
            if isinstance(target_projection, str):
                try:
                    target_projection = Projection[target_projection.lower()]
                except KeyError:
                    raise ValueError(
                        f"Projection type '{target_projection}' not recognized. See `Projection` for available options."
                    )
            # parse options
            if options:
                options = "".join([f"{k}={v}:" for k, v in options])
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
            )
            self.filename = output_name
