#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from ddt.core import env
from ddt.out import debug, fail
import sys
import glob
import os
import shutil
import subprocess


def ls(pattern='.'):
    # List files matching the pattern.
    return sorted(glob.glob(pattern))


def cp(src_path, dst_path):
    # Copy a file or a directory.
    debug("cp `%s` `%s`" % (src_path, dst_path))
    shutil.copy(src_path, dst_path)


def mv(src_path, dst_path):
    # Rename a file.
    debug("mv `%s` `%s`" % (src_path, dst_path))
    os.rename(src_path, dst_path)


def rm(path):
    # Remove a file.
    debug("rm `%s`" % path)
    os.unlink(path)


def rmtree(path):
    # Remove a directory tree.
    debug("rmtree `%s`" % path)
    shutil.rmtree(path)


def mktree(path):
    # Create a directory tree.
    if not os.path.isdir(path):
        debug("mktree `%s`" % path)
        os.makedirs(path)


def exe(cmd):
    # Execute the command replacing the current process.
    log("`%s`" % cmd)
    line = cmd.split()
    try:
        os.execvp(line[0], line)
    except OSError, exc:
        raise fail(exc)


def sh(cmd, data=None, cd=None):
    # Execute a command using shell.
    if cd is not None:
        cmd = "cd %s && %s" % (cd, cmd)
    stream = subprocess.PIPE
    if env.debug:
        stream = None
    debug("`sh %s`" % cmd)
    proc = subprocess.Popen(cmd, shell=True, stdin=stream,
                            stdout=stream, stderr=stream)
    proc.communicate(data)
    if proc.returncode != 0:
        raise fail("`sh %s`: non-zero exit code" % cmd)


def pipe(cmd, data=None, cd=None):
    # Execute the command, return the output.
    if cd is not None:
        cmd = "cd %s && %s" % (cd, cmd)
    stream = subprocess.PIPE
    debug("`| %s`" % cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=stream, stderr=stream)
    out, err = proc.communicate(data)
    if proc.returncode != 0:
        if env.debug:
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
        raise fail("`| %s`: non-zero exit code" % cmd)
    return out


