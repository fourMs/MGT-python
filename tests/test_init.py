import musicalgestures


def test_repr():
    mg = musicalgestures.MgObject(musicalgestures.examples.dance)
    assert mg.__repr__() == f"MgObject('{musicalgestures.examples.dance}')"
