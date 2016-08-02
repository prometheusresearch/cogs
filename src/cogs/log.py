#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .core import Failure, env
import sys
import os
import re


class COLORS:
    # ANSI escape sequences and style decorations.

    S_RESET = 0
    S_BRIGHT = 1
    S_DIM = 2
    S_UNDERSCORE = 4
    S_BLINK = 5
    S_REVERSE = 7
    S_HIDDEN = 8
    FG_BLACK = 30
    FG_RED = 31
    FG_GREEN = 32
    FG_YELLOW = 33
    FG_BLUE = 34
    FG_MAGENTA = 35
    FG_CYAN = 36
    FG_WHITE = 37
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_WHITE = 47

    styles = {
        None: [S_BRIGHT],
        'debug': [S_DIM],
        'warning': [S_BRIGHT, FG_RED],
        'success': [S_BRIGHT, FG_GREEN],
    }


def colorize(msg, file=None):
    # Convert styling decorations to ANSI escape sequences.
    if not msg:
        return msg
    if file is None:
        file = sys.stdout
    has_colors = file.isatty()
    def _replace(match):
        style = match.group('style')
        data = match.group('data')
        assert style in COLORS.styles, "unknown style %r" % style
        if not has_colors:
            return data
        lesc = "\x1b[%sm" % ";".join(str(ctrl)
                                     for ctrl in COLORS.styles[style])
        resc = "\x1b[%sm" % COLORS.S_RESET
        return lesc+data+resc
    return re.sub(r"(?::(?P<style>[a-zA-Z]+):)?`(?P<data>[^`]*)`",
                  _replace, msg)


def _out(msg, file, args, kwds):
    # Print a formatted message to a file.
    msg = colorize(msg, file)
    if args or kwds:
        msg = msg.format(*args, **kwds)
    file.write(msg)
    file.flush()


def log(msg="", *args, **kwds):
    """Display a message."""
    _out(msg+"\n", sys.stdout, args, kwds)


def debug(msg, *args, **kwds):
    """Display a debug message."""
    if env.debug:
        _out(":debug:`#` "+msg+"\n", sys.stderr, args, kwds)


def warn(msg, *args, **kwds):
    """Display a warning."""
    _out(":warning:`WARNING`: "+msg+"\n", sys.stderr, args, kwds)


def fail(msg, *args, **kwds):
    """Display an error message and return an exception object."""
    _out(":warning:`FATAL ERROR`: "+msg+"\n", sys.stderr, args, kwds)
    return Failure()


def prompt(msg):
    """Prompt the user for input."""
    value = ""
    while not value:
        value = raw_input(msg+" ").strip()
    return value


