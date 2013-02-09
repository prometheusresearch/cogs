#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


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


def exe(cmd):
    """Execute the command replacing the current process."""
    debug("exe {}", cmd)
    line = cmd.split()
    try:
        os.execvp(line[0], line)
    except OSError, exc:
        raise fail(str(exc))


def sh(cmd, data=None, cd=None):
    """Execute a command using shell."""
    if cd is None:
        debug("sh {}", cmd)
    else:
        debug("cd {}; sh {}", cd, cmd)
    stream = subprocess.PIPE
    if env.debug:
        stream = None
    if cd is not None:
        cwd = os.getcwd()
        os.chdir(cd)
    try:
        proc = subprocess.Popen(cmd, shell=True, stdin=stream,
                                stdout=stream, stderr=stream)
        proc.communicate(data)
    finally:
        if cd is not None:
            os.chdir(cwd)
    if proc.returncode != 0:
        raise fail("sh `{}`: non-zero exit code", cmd)


def pipe(cmd, data=None, cd=None):
    """Execute the command, return the output."""
    if cd is None:
        debug("pipe {}", cmd)
    else:
        debug("cd {}; pipe {}", cd, cmd)
    stream = subprocess.PIPE
    if cd is not None:
        cwd = os.getcwd()
        os.chdir(cd)
    try:
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=stream, stderr=stream)
        out, err = proc.communicate(data)
    finally:
        if cd is not None:
            os.chdir(cwd)
    if proc.returncode != 0:
        if env.debug:
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
        raise fail("pipe `{}`: non-zero exit code", cmd)
    return out


