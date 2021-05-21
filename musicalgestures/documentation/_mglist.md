# MgList

> Auto-generated documentation for [_mglist](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / MgList
    - [MgList](#mglist)
        - [MgList().\_\_add\_\_](#mglist__add__)
        - [MgList().\_\_delitem\_\_](#mglist__delitem__)
        - [MgList().\_\_getitem\_\_](#mglist__getitem__)
        - [MgList().\_\_iadd\_\_](#mglist__iadd__)
        - [MgList().\_\_iter\_\_](#mglist__iter__)
        - [MgList().\_\_len\_\_](#mglist__len__)
        - [MgList().\_\_setitem\_\_](#mglist__setitem__)
        - [MgList().as_figure](#mglistas_figure)
        - [MgList().show](#mglistshow)

## MgList

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L5)

```python
class MgList():
    def __init__(*objectlist):
```

Class for handling lists of MgImage, MgFigure and MgList objects in the Musical Gestures Toolbox.

Attributes
----------
- *objectlist : objects and/or list(s) of objects

MgObjects and/or MgImages to include in the list.

### MgList().\_\_add\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L132)

```python
def __add__(other):
```

Implements `+`.

#### Arguments

other (MgImage, MgFigure, or MgList): The object(s) to add to the MgList.

#### Returns

- `MgList` - The incremented MgList.

### MgList().\_\_delitem\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L89)

```python
def __delitem__(key):
```

Implements deleting elements given an index from the MgList.

#### Arguments

- `key` *int* - The index of the element to delete.

### MgList().\_\_getitem\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L67)

```python
def __getitem__(key):
```

Implements getting elements given an index from the MgList.

#### Arguments

- `key` *int* - The index of the element to retrieve.

#### Returns

MgImage, MgFigure, or MgList: The element at `key`.

### MgList().\_\_iadd\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L107)

```python
def __iadd__(other):
```

Implements `+=`.

#### Arguments

other (MgImage, MgFigure, or MgList): The object(s) to add to the MgList.

#### Returns

- `MgList` - The incremented MgList.

### MgList().\_\_iter\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L98)

```python
def __iter__():
```

Implements `iter()`.

#### Returns

- `iterator` - The iterator of `self.objectlist`.

### MgList().\_\_len\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L58)

```python
def __len__():
```

Implements `len()`.

#### Returns

- `int` - The length of the MgList.

### MgList().\_\_setitem\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L79)

```python
def __setitem__(key, value):
```

Implements setting elements given an index from the MgList.

#### Arguments

- `key` *int* - The index of the element to change.
value (MgImage, MgFigure, or MgList): The element to place at `key`.

### MgList().as_figure

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L163)

```python
def as_figure(dpi=300, autoshow=True, title=None, export_png=True):
```

Creates a time-aligned figure from all the elements in the MgList.

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add a title to the figure. Defaults to None (no title).
- `export_png` *bool, optional* - Whether to export a png image of the resulting figure automatically. Defaults to True.

#### Returns

- `MgFigure` - The MgFigure with all the elements from the MgList as layers.

### MgList().show

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mglist.py#L47)

```python
def show(
    filename=None,
    key=None,
    mode='windowed',
    window_width=640,
    window_height=480,
    window_title=None,
):
```

Iterates all objects in the MgList and calls `mg_show()` on them.
