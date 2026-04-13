# Cli

> Auto-generated documentation for [musicalgestures.cli](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/cli.py) module.

Command-line interface for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Cli
    - [main](#main)

The [Musicalgestures](index.md#musicalgestures) command provides quick access to the most common
analysis and visualisation operations without writing Python code.

Usage

```python
musicalgestures --help
musicalgestures motion dancer.avi --thresh 0.05 --filtertype Regular
musicalgestures videograms dancer.avi
musicalgestures average dancer.avi
musicalgestures info dancer.avi
musicalgestures convert dancer.avi --to mp4
```

Install CLI dependencies with

```python
pip install musicalgestures[cli]
```

## main

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/cli.py#L40)

```python
def main() -> None:
```

Entry point registered in pyproject.toml as [Musicalgestures](index.md#musicalgestures).
