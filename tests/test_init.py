import musicalgestures


def test_repr():
    mg = musicalgestures.MgVideo(musicalgestures.examples.dance)
    r = mg.__repr__()
    # Informative repr: starts with the class + filename and reports key properties.
    assert r.startswith(f"MgVideo('{musicalgestures.examples.dance}'")
    assert "frames" in r and "fps" in r and "audio=" in r
