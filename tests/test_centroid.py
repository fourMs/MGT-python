import numpy as np
from musicalgestures._centroid import *


class Test_Centroid:
    def test_empty_image(self):
        image_in = np.zeros((1920, 1080, 3)).astype(np.uint8)
        result = centroid(image_in, 1920, 1080)
        assert type(result) == tuple
        assert result[0][0] == 0
        assert result[0][1] == 1080
