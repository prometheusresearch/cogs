#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from ddt.core import Failure, env
import sys
import os
import re


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
    'footnote': [S_DIM],
    'warning': [S_BRIGHT, FG_RED],
    'success': [S_BRIGHT, FG_GREEN],
}


def colorize(msg, has_colors=True):
    def replace(match):
        indicator = match.group('indicator')
        data = match.group('data')
        assert indicator in styles, "unknown style %r" % indicator
        if not has_colors:
            return data
        lesc = "\x1b[%sm" % ";".join(str(style)
                                     for style in styles[indicator])
        resc = "\x1b[%sm" % S_RESET
        return lesc+data+resc
    return re.sub(r"(?::(?P<indicator>[a-zA-Z]+):)?`(?P<data>[^`]*)`",
                  replace, msg)


def log(*msgs, **opts):
    sep = opts.pop('sep', " ")
    end = opts.pop('end', "\n")
    file = opts.pop('file', sys.stdout)
    assert not opts, opts
    has_colors = (file.isatty() and os.environ.get('COLORTERM'))
    data = sep.join(colorize(str(msg), has_colors) for msg in msgs) + end
    file.write(data)
    file.flush()


def debug(*msgs, **opts):
    if env.debug:
        return log(":footnote:`...`", file=sys.stderr, *msgs, **opts)


def warn(*msgs, **opts):
    return log(":warning:`WARNING`:", file=sys.stderr, *msgs, **opts)


def fail(*msgs, **opts):
    log(":warning:`FATAL ERROR`:", file=sys.stderr, *msgs, **opts)
    return Failure()


def prompt(msg):
    value = ""
    while not value:
        value = raw_input(msg+" ").strip()
    return value


