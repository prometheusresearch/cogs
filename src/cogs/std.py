#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .logutils import LogUtils
from .shell import ArgDsc
import os.path
import sys


def register_std(shell):
    log_utils = LogUtils(shell)
    log = log_utils.log
    fail = log_utils.fail


    @shell.register_default_task
    class Usage(object):
        """explain how to obtain help on DDT"""

        # FIXME: implement common options: `--help`, `--version`, `--license`
        #help = option()
        #version = option()
        #license = option()

        def __init__(self, help=False, version=False, license=False):
            self.help = help
            self.version = version
            self.license = license

        def __call__(self):
            #if self.help:
            #    t = Help()
            #    return t()
            #if self.version:
            #    t = Version()
            #    return t()
            #if self.license:
            #    t = License()
            #    return t()
            if shell.description:
                log("%s - %s" % (shell.name, shell.description))
            else:
                log(shell.name)
            executable = os.path.basename(sys.argv[0])
            log("Usage: %s [<settings>...] <task> [<arguments>...]"
                % executable)
            log()
            log("Run `%s help` for general usage and a list of tasks"
                " and settings." % executable)
            log("Run `%s help <task>` for help on a specific task."
                % executable)


    @shell.register_task
    class Help(object):
        """display help on tasks and options

        When started without arguments, displays a list of available tasks,
        options and toggles.

        When `<name>` is given, describes the usage of the specified task
        or option.
        """

        name = ArgDsc(default=None)

        def __init__(self, name):
            self.name = name

        def __call__(self):
            if self.name is None:
                return self.describe_all()
            if self.name in shell.task_by_name:
                task = shell.task_by_name[self.name]
                return self.describe_task(task)
            elif self.name in shell.setting_by_name:
                setting = shell.setting_by_name[self.name]
                return self.describe_setting(setting)
            else:
                raise fail("unknown task or setting `%s`" % self.name)

        def describe_all(self):
            if shell.description:
                log("%s - %s" % (shell.name, shell.description))
            else:
                log(shell.name)
            executable = os.path.basename(sys.argv[0])
            log("Usage: %s [<settings>...] <task> [<arguments>...]"
                % executable)
            log()
            log("Run `%s help` for general usage and a list of tasks"
                " and settings." % executable)
            log("Run `%s help <task>` for help on a specific task."
                % executable)
            log()
            log("Available tasks:")
            for name in sorted(shell.task_by_name):
                if not name:
                    continue
                task = shell.task_by_name[name]
                usage = task.usage
                hint = task.hint
                if hint:
                    log("  %-24s : %s" % (usage, hint))
                else:
                    log("  %s" % usage)
            log()
            log("Settings:")
            for name in sorted(shell.setting_by_name):
                setting = shell.setting_by_name[name]
                usage = setting.usage
                hint = setting.hint
                if hint:
                    log("  %-24s : %s" % (usage, hint))
                else:
                    log("  %s" % usage)
            log()

        def describe_task(self, task):
            name = task.name
            hint = task.hint
            if hint:
                log("%s - %s" % (name.upper(), hint))
            else:
                log(name.upper())
            usage = task.usage
            executable = os.path.basename(sys.argv[0])
            log("Usage: `%s %s`" % (executable, usage))
            log()
            help = task.help
            if help:
                log(help)
                log()
            if task.opts:
                log("Options:")
                for opt in task.opts:
                    usage = opt.usage
                    hint = opt.hint
                    if hint:
                        log("  %-24s : %s" % (usage, hint))
                    else:
                        log("  %s" % usage)

        def describe_setting(self, setting):
            name = setting.name
            hint = setting.hint
            if hint:
                log("%s - %s" % (name.upper(), hint))
            else:
                log(name.upper())
            executable = os.path.basename(sys.argv[0])
            usage = setting.usage
            usage_conf = setting.usage_conf
            usage_environ = setting.usage_environ
            log("Usage: `%s %s`" % (executable, usage))
            if shell.config_name:
                log("       `%s` (%s)" % (usage_conf, shell.config_name))
            log("       `%s` (environment)" % usage_environ)
            log()
            help = setting.help
            if help:
                log(help)
                log()


    @shell.register_setting
    def Debug(value=False):
        """print debug information"""
        if value is None or value in ['false', '', '0', 0]:
            value = False
        if value in ['true', '1', 1]:
            value = True
        if not isinstance(value, bool):
            raise ValueError("debug: expected a Boolean value; got %r" % value)
        shell.environment.set(debug=value)


