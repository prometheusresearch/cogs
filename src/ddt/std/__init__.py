#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from ddt.core import env, task, default_task, argument, setting
from ddt.out import log, fail


@default_task
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
        log("DDT - Development, Deployment and Testing automation toolkit")
        log("Copyright (c) 2012, Prometheus Research, LLC")
        log()
        log("Run `ddt help` for general usage and a list of tasks"
            " and settings.")
        log("Run `ddt help <task>` for help on a specific task.")


@task
class Help(object):
    """display help on tasks and options

    When started without arguments, displays a list of available tasks,
    options and toggles.

    When `<name>` is given, describes the usage of the specified task
    or option.
    """

    name = argument(default=None)

    def __init__(self, name):
        self.name = name

    def __call__(self):
        if self.name is None:
            return self.describe_all()
        if self.name in env._task_by_name:
            T = env._task_by_name[self.name]
            return self.describe_task(T)
        elif self.name in env._setting_by_name:
            S = env._setting_by_name[self.name]
            return self.describe_setting(S)
        else:
            raise fail("unknown task or setting `%s`" % self.name)

    def describe_all(self):
        log("DDT - Development, Deployment and Testing automation toolkit")
        log("Copyright (c) 2012, Prometheus Research, LLC")
        log("Usage: `ddt [<settings>...] <task> [<arguments>...]`")
        log()
        log("Run `ddt help` for general usage and a list of tasks"
            " and settings.")
        log("Run `ddt help <task>` for help on a specific task.")
        log()
        log("Available tasks:")
        for name in sorted(env._task_by_name):
            if not name:
                continue
            T = env._task_by_name[name]
            usage = T._usage
            hint = T._hint
            if hint:
                log("  %-24s : %s" % (usage, hint))
            else:
                log("  %s" % usage)
        log()
        log("Settings:")
        for name in sorted(env._setting_by_name):
            S = env._setting_by_name[name]
            usage = S._usage
            hint = S._hint
            if hint:
                log("  %-24s : %s" % (usage, hint))
            else:
                log("  %s" % usage)
        log()

    def describe_task(self, T):
        name = T._name
        hint = T._hint
        if hint:
            log("%s - %s" % (name.upper(), hint))
        else:
            log(name.upper())
        usage = T._usage
        log("Usage: `ddt %s`" % usage)
        log()
        help = T._help
        if help:
            log(help)
            log()
        options = T._opts
        if options:
            log("Options:")
            for O in options:
                usage = O.usage
                hint = O.hint
                if hint:
                    log("  %-24s : %s" % (usage, hint))
                else:
                    log("  %s" % usage)

    def describe_setting(self, S):
        name = S._name
        hint = S._hint
        if hint:
            log("%s - %s" % (name.upper(), hint))
        else:
            log(name.upper())
        usage = S._usage
        usage_conf = S._usage_conf
        usage_environ = S._usage_environ
        log("Usage: `ddt %s`" % usage)
        log("       `%s` (ddt.conf)" % usage_conf)
        log("       `%s` (environment)" % usage_environ)
        log()
        help = S._help
        if help:
            log(help)
            log()


@setting
def Debug(value=False):
    """print debug information"""
    if value is None or value in ['false', '', '0', 0]:
        value = False
    if value in ['true', '1', 1]:
        value = True
    if not isinstance(value, bool):
        raise ValueError("debug: expected a Boolean value; got %r" % value)
    env.set(debug=value)


