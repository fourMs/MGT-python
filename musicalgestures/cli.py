"""Command-line interface for MGT-python.

The ``musicalgestures`` command provides quick access to the most common
analysis and visualisation operations without writing Python code.

Usage::

    musicalgestures --help
    musicalgestures motion dancer.avi --threshold 0.05 --filtertype Regular
    musicalgestures videograms dancer.avi
    musicalgestures average dancer.avi
    musicalgestures info dancer.avi
    musicalgestures convert dancer.avi --to mp4

Install CLI dependencies with::

    pip install musicalgestures[cli]
"""
from __future__ import annotations

import sys
import logging

logger = logging.getLogger(__name__)


def _require_click():
    try:
        import click
        return click
    except ImportError:
        print(
            "The CLI requires the 'click' package.\n"
            "Install it with:  pip install musicalgestures[cli]",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Entry point registered in pyproject.toml as ``musicalgestures``."""
    click = _require_click()

    @click.group(
        context_settings={"help_option_names": ["-h", "--help"]},
        invoke_without_command=True,
    )
    @click.version_option(package_name="musicalgestures", prog_name="musicalgestures")
    @click.pass_context
    def cli(ctx):
        """Musical Gestures Toolbox – command-line interface.

        Analyse and visualise video and audio files from the command line.
        Run 'musicalgestures COMMAND --help' for details on each command.
        """
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    # ------------------------------------------------------------------
    # info
    # ------------------------------------------------------------------

    @cli.command("info")
    @click.argument("filename", type=click.Path(exists=True))
    def cmd_info(filename):
        """Print metadata about a video or audio file."""
        try:
            from musicalgestures._utils import get_length, get_framecount, get_fps, get_widthheight, has_audio
            length = get_length(filename)
            fps = get_fps(filename)
            width, height = get_widthheight(filename)
            audio = has_audio(filename)
            click.echo(f"File:     {filename}")
            click.echo(f"Size:     {width} × {height} px")
            click.echo(f"FPS:      {fps:.2f}")
            click.echo(f"Length:   {length:.3f} s")
            click.echo(f"Audio:    {'yes' if audio else 'no'}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # motion
    # ------------------------------------------------------------------

    @cli.command("motion")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--filtertype", default="Regular",
                  type=click.Choice(["Regular", "Binary", "Blob"], case_sensitive=False),
                  help="Filter type for motion detection.")
    @click.option("--threshold", default=0.05, type=float, show_default=True,
                  help="Pixel-value threshold (0–1).")
    @click.option("--blur", default="None",
                  type=click.Choice(["None", "Average"], case_sensitive=False),
                  help="Blur type.")
    @click.option("--color/--no-color", default=True, show_default=True,
                  help="Process in colour (default) or grayscale.")
    @click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
    def cmd_motion(filename, filtertype, threshold, blur, color, overwrite):
        """Render a motion video for FILENAME."""
        try:
            import musicalgestures as mg
            v = mg.MgVideo(filename, color=color)
            out = v.motion(filtertype=filtertype, threshold=threshold, blur=blur,
                           save_video=True, save_plot=False, save_data=False,
                           overwrite=overwrite)
            click.echo(f"Motion video saved: {out.filename}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # videograms
    # ------------------------------------------------------------------

    @cli.command("videograms")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
    def cmd_videograms(filename, overwrite):
        """Render horizontal and vertical videograms for FILENAME."""
        try:
            import musicalgestures as mg
            v = mg.MgVideo(filename)
            out = v.videograms(overwrite=overwrite)
            click.echo(f"Videograms saved: {[o.filename for o in out]}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # average
    # ------------------------------------------------------------------

    @cli.command("average")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
    def cmd_average(filename, overwrite):
        """Render a pixel-average (blend) image for FILENAME."""
        try:
            import musicalgestures as mg
            v = mg.MgVideo(filename)
            out = v.average(overwrite=overwrite)
            click.echo(f"Average image saved: {out.filename}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # history
    # ------------------------------------------------------------------

    @cli.command("history")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
    def cmd_history(filename, overwrite):
        """Render a motion history image for FILENAME."""
        try:
            import musicalgestures as mg
            v = mg.MgVideo(filename)
            out = v.history(overwrite=overwrite)
            click.echo(f"History image saved: {out.filename}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # convert
    # ------------------------------------------------------------------

    @cli.command("convert")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--to", "target_format", default="mp4", show_default=True,
                  help="Target container format (e.g. mp4, avi, mov).")
    @click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
    def cmd_convert(filename, target_format, overwrite):
        """Convert FILENAME to another container format."""
        try:
            import os
            from musicalgestures._utils import convert
            of = os.path.splitext(filename)[0]
            out = convert(filename, f"{of}.{target_format.lstrip('.')}", overwrite=overwrite)
            click.echo(f"Converted: {out}")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # motiongrams
    # ------------------------------------------------------------------

    @cli.command("motiongrams")
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--filtertype", default="Regular",
                  type=click.Choice(["Regular", "Binary", "Blob"], case_sensitive=False))
    @click.option("--threshold", default=0.05, type=float, show_default=True)
    @click.option("--overwrite", is_flag=True)
    def cmd_motiongrams(filename, filtertype, threshold, overwrite):
        """Render horizontal and vertical motiongrams for FILENAME."""
        try:
            import musicalgestures as mg
            v = mg.MgVideo(filename)
            out = v.motiongrams(filtertype=filtertype, threshold=threshold, overwrite=overwrite)
            click.echo(f"Motiongrams saved.")
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    cli()


if __name__ == "__main__":
    main()
