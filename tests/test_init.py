import musicalgestures


def test_repr():
    mg = musicalgestures.MgVideo(musicalgestures.examples.dance)
    assert mg.__repr__() == f"MgVideo('{musicalgestures.examples.dance}')"
