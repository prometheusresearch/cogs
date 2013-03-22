#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .core import env
from .log import debug, fail
import sys
import os
import shutil
import subprocess


def cp(src_path, dst_path):
    """Copy a file or a directory."""
    debug("cp {} {}", src_path, dst_path)
    shutil.copy(src_path, dst_path)


def mv(src_path, dst_path):
    """Rename a file."""
    debug("mv {} {}", src_path, dst_path)
    os.rename(src_path, dst_path)


def rm(path):
    """Remove a file."""
    debug("rm {}", path)
    os.unlink(path)


def rmtree(path):
    """Remove a directory tree."""
    debug("rmtree {}", path)
    shutil.rmtree(path)


def mktree(path):
    """Create a directory tree."""
    if not os.path.isdir(path):
        debug("mktree {}", path)
        os.makedirs(path)


def exe(cmd, cd=None, environ=None):
    """Execute the command replacing the current process."""
    debug("{}", cmd)
    line = cmd.split()
    if environ:
        overrides = environ
        environ = os.environ.copy()
        environ.update(overrides)
    if cd:
        os.chdir(cd)
    try:
        if environ:
            os.execvpe(line[0], line, environ)
        else:
            os.execvp(line[0], line)
    except OSError, exc:
        raise fail(str(exc))


def sh(cmd, data=None, cd=None, environ=None):
    """Execute a command using shell."""
    if cd is None:
        debug("{}", cmd)
    else:
        debug("cd {}; {}", cd, cmd)
    stream = subprocess.PIPE
    if env.debug:
        stream = None
    if environ:
        overrides = environ
        environ = os.environ.copy()
        environ.update(overrides)
    proc = subprocess.Popen(cmd, shell=True, stdin=stream,
                            stdout=stream, stderr=stream,
                            cwd=cd, env=environ)
    proc.communicate(data)
    if proc.returncode != 0:
        raise fail("`{}`: non-zero exit code", cmd)


def pipe(cmd, data=None, cd=None, environ=None):
    """Execute the command, return the output."""
    if cd is None:
        debug("| {}", cmd)
    else:
        debug("$ cd {}; | {}", cd, cmd)
    stream = subprocess.PIPE
    if environ:
        overrides = environ
        environ = os.environ.copy()
        environ.update(overrides)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=stream, stderr=stream,
                            cwd=cd, env=environ)
    out, err = proc.communicate(data)
    if proc.returncode != 0:
        if env.debug:
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
        raise fail("`{}`: non-zero exit code", cmd)
    return out


