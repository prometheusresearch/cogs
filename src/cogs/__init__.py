#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .shell import Shell, ArgDsc, OptDsc, Failure
from .sysutils import SysUtils
from .logutils import LogUtils
from .std import register_std
import sys
import os.path


cogs = Shell(name="Cogs",
             description="""A task dispatching utility""",
             local_package='cogs.local',
             entry_point='cogs.extensions',
             config_name='cogs.conf',
             config_dirs=['/etc',
                          os.path.join(sys.prefix, '/etc'),
                          os.path.expanduser('~/.cogs'),
                          os.path.abspath('.')])
env = cogs.environment
task = cogs.register_task
default_task = cogs.register_default_task
setting = cogs.register_setting
argument = ArgDsc
option = OptDsc


sys_utils = SysUtils(cogs)
cp = sys_utils.cp
mv = sys_utils.mv
rm = sys_utils.rm
mktree = sys_utils.mktree
rmtree = sys_utils.rmtree
exe = sys_utils.exe
sh = sys_utils.sh
pipe = sys_utils.pipe


log_utils = LogUtils(cogs)
log = log_utils.log
debug = log_utils.debug
warn = log_utils.warn
fail = log_utils.fail
prompt = log_utils.prompt


register_std(cogs)


run = cogs.run


