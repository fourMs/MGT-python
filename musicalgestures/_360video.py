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

    equirectangular = 30  # extra option for equirectangular
    erp = 31

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
        elif self == other:
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
}


class Mg360Video(MgVideo):
    """
    Class for 360 videos.
    """

    def __init__(
        self,
        filename: str,
        projection: str | Projection,
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

    def convert_projection(
        self, target_projection: Projection | str, options: dict[str, str] = None
    ):
        """
        Convert the video to a different projection.
        Args:
            target_projection (Projection): Target projection.
            options (dict[str, str], optional): Options for the conversion. Defaults to None.
        """
        target_projection = self._parse_projection(target_projection)

        if target_projection == self.projection:
            print(f"{self} is already in target projection {target_projection}.")
            return
        else:
            output_name = generate_outfilename(
                f"{self.filename.split('.')[0]}_{target_projection}.mp4"
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
            self.projection = target_projection

    def _parse_projection(self, projection: str | Projection):
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
