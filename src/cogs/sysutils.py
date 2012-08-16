#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .logutils import LogUtils
import sys
import glob
import os
import shutil
import subprocess


class SysUtils(object):

    def __init__(self, shell):
        self.shell = shell
        self.env = shell.environment
        log_utils = LogUtils(shell)
        self._debug = log_utils.debug
        self._fail = log_utils.fail

    def cp(self, src_path, dst_path):
        # Copy a file or a directory.
        self._debug("cp `%s` `%s`" % (src_path, dst_path))
        shutil.copy(src_path, dst_path)

    def mv(self, src_path, dst_path):
        # Rename a file.
        self._debug("mv `%s` `%s`" % (src_path, dst_path))
        os.rename(src_path, dst_path)

    def rm(self, path):
        # Remove a file.
        self._debug("rm `%s`" % path)
        os.unlink(path)

    def rmtree(self, path):
        # Remove a directory tree.
        self._debug("rmtree `%s`" % path)
        shutil.rmtree(path)

    def mktree(self, path):
        # Create a directory tree.
        if not os.path.isdir(path):
            self._debug("mktree `%s`" % path)
            os.makedirs(path)

    def exe(self, cmd):
        # Execute the command replacing the current process.
        self._debug("`%s`" % cmd)
        line = cmd.split()
        try:
            os.execvp(line[0], line)
        except OSError, exc:
            raise self._fail(exc)

    def sh(self, cmd, data=None, cd=None):
        # Execute a command using shell.
        if cd is not None:
            cmd = "cd %s && %s" % (cd, cmd)
        stream = subprocess.PIPE
        if self.env.debug:
            stream = None
        self._debug("`sh %s`" % cmd)
        proc = subprocess.Popen(cmd, shell=True, stdin=stream,
                                stdout=stream, stderr=stream)
        proc.communicate(data)
        if proc.returncode != 0:
            raise self._fail("`sh %s`: non-zero exit code" % cmd)

    def pipe(self, cmd, data=None, cd=None):
        # Execute the command, return the output.
        if cd is not None:
            cmd = "cd %s && %s" % (cd, cmd)
        stream = subprocess.PIPE
        self._debug("`| %s`" % cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=stream, stderr=stream)
        out, err = proc.communicate(data)
        if proc.returncode != 0:
            if self.env.debug:
                if out:
                    sys.stdout.write(out)
                if err:
                    sys.stderr.write(err)
            raise self._fail("`| %s`: non-zero exit code" % cmd)
        return out


