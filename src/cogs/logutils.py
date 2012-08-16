#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .shell import Failure
import sys
import os
import re


class LogUtils(object):

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

    def __init__(self, shell):
        self.shell = shell
        self.env = shell.environment

    def _colorize(self, msg, has_colors=True):
        def replace(match):
            indicator = match.group('indicator')
            data = match.group('data')
            assert indicator in self.styles, "unknown style %r" % indicator
            if not has_colors:
                return data
            lesc = "\x1b[%sm" % ";".join(str(style)
                                         for style in self.styles[indicator])
            resc = "\x1b[%sm" % self.S_RESET
            return lesc+data+resc
        return re.sub(r"(?::(?P<indicator>[a-zA-Z]+):)?`(?P<data>[^`]*)`",
                      replace, msg)

    def log(self, *msgs, **opts):
        sep = opts.pop('sep', " ")
        end = opts.pop('end', "\n")
        file = opts.pop('file', sys.stdout)
        assert not opts, opts
        has_colors = (file.isatty() and os.environ.get('COLORTERM'))
        data = sep.join(self._colorize(str(msg), has_colors)
                        for msg in msgs) + end
        file.write(data)
        file.flush()

    def debug(self, *msgs, **opts):
        if self.env.debug:
            return self.log(":footnote:`...`", file=sys.stderr, *msgs, **opts)

    def warn(self, *msgs, **opts):
        return self.log(":warning:`WARNING`:", file=sys.stderr, *msgs, **opts)

    def fail(self, *msgs, **opts):
        self.log(":warning:`FATAL ERROR`:", file=sys.stderr, *msgs, **opts)
        return Failure()

    def prompt(self, msg):
        value = ""
        while not value:
            value = raw_input(msg+" ").strip()
        return value


