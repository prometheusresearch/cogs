#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .core import env, task, default_task, setting, argument, option
from .log import log, fail
import sys
import os.path


@default_task
class USAGE(object):
    """run when no task is supplied"""

    help = option()
    #version = option()
    #license = option()

    def __init__(self, help=False):
        self.help = help

    def __call__(self):
        if self.help:
            t = HELP(None)
            return t()
        if env.shell.description:
            log("{} - {}", env.shell.name, env.shell.description)
        else:
            log("{}", env.shell.name)
        executable = os.path.basename(sys.argv[0])
        log("Usage: `{} [<settings>...] <task> [<arguments>...]`", executable)
        log()
        log("Run `{} help` for general usage and a list of tasks and settings.",
            executable)
        log("Run `{} help <topic>` for help on a specific task or setting.",
            executable)


@task
class HELP(object):
    """display help on tasks and settings

    When started without arguments, displays a list of available tasks,
    settings and toggles.

    When `<topic>` is given, describes the usage of the specified task
    or setting.
    """

    topic = argument(default=None)

    def __init__(self, topic):
        self.topic = topic

    def __call__(self):
        if self.topic is None:
            return self.describe_all()
        if self.topic in env.task_map and self.topic != '':
            spec = env.task_map[self.topic]
            return self.describe_task(spec)
        elif self.topic in env.setting_map:
            spec = env.setting_map[self.topic]
            return self.describe_setting(spec)
        elif self.topic in env.topic_map:
            spec = env.topic_map[self.topic]
            return self.describe_topic(spec)
        else:
            raise fail("unknown help topic `{}`", self.topic)

    def describe_all(self):
        if env.shell.description:
            log("{} - {}", env.shell.name, env.shell.description)
        else:
            log("{}", env.shell.name)
        executable = os.path.basename(sys.argv[0])
        log("Usage: `{} [<settings>...] <task> [<arguments>...]`", executable)
        log()
        log("Run `{} help` for general usage and a list of tasks,", executable)
        log("settings and other help topics.")
        log()
        log("Run `{} help <topic>` for help on a specific topic.", executable)
        log()
        if env.task_map:
            log("Available tasks:")
            for name in sorted(env.task_map):
                if not name:
                    continue
                spec = env.task_map[name]
                usage = spec.name
                for arg in spec.args:
                    if arg.is_optional:
                        continue
                    usage = "%s <%s>" % (usage, arg.name)
                    if arg.is_plural:
                        usage += "..."
                if spec.hint:
                    log("  {:<24} : {}", usage, spec.hint)
                else:
                    log("  {}", usage)
            log()
        if env.setting_map:
            log("Settings:")
            for name in sorted(env.setting_map):
                spec = env.setting_map[name]
                if spec.has_value:
                    usage = "--%s=%s" % (spec.name, spec.value_name.upper())
                else:
                    usage = "--%s" % spec.name
                if spec.hint:
                    log("  {:<24} : {}", usage, spec.hint)
                else:
                    log("  {}", usage)
            log()
        if env.topic_map:
            log("Other topics:")
            for name in sorted(env.topic_map):
                spec = env.topic_map[name]
                if spec.hint:
                    log("  {:<24} : {}", spec.name, spec.hint)
                else:
                    log("  {}", spec.name)
            log()

    def describe_task(self, spec):
        if spec.hint:
            log("{} - {}", spec.name.upper(), spec.hint)
        else:
            log("{}", spec.name.upper())
        usage = spec.name
        optionals = 0
        for arg in spec.args:
            if arg.is_optional:
                usage = "%s [<%s>" % (usage, arg.name)
                optionals += 1
            elif optionals > 0:
                usage += "]"*optionals
                optionals = 0
                usage = "%s <%s>" % (usage, arg.name)
            else:
                usage = "%s <%s>" % (usage, arg.name)
            if arg.is_plural:
                usage += "..."
        if optionals:
            usage += "]"*optionals
        executable = os.path.basename(sys.argv[0])
        log("Usage: `{} {}`", executable, usage)
        log()
        if spec.help:
            log(spec.help)
            log()
        if spec.opts:
            log("Options:")
            for opt in spec.opts:
                usage = "--%s" % opt.name
                if opt.key is not None:
                    usage = "-%s/%s" % (opt.key, usage)
                if opt.has_value:
                    usage = "%s=%s" % (usage, opt.value_name)
                if spec.hint:
                    log("  {:<24} : {}", usage, opt.hint)
                else:
                    log("  {}", opt.name)
            log()

    def describe_setting(self, spec):
        if spec.hint:
            log("{} - {}", spec.name.upper(), spec.hint)
        else:
            log("{}", spec.name.upper())
        executable = os.path.basename(sys.argv[0])
        usage = "--%s" % spec.name
        usage_conf = "%s" % spec.name
        usage_environ = ("%s_%s" % (env.shell.name, spec.name)) \
                        .upper().replace('-', '_')
        if spec.has_value:
            usage += "=%s" % spec.value_name
            usage_conf += ": %s" % spec.value_name
            usage_environ += "=%s" % spec.value_name
        else:
            usage_conf += ": true"
            usage_environ += "=1"
        log("Usage: `{} {}`", executable, usage)
        if env.shell.config_name:
            log("       `{}` ({})", usage_conf, env.shell.config_name)
        log("       `{}` (environment)", usage_environ)
        log()
        if spec.help:
            log(spec.help)
            log()

    def describe_topic(self, spec):
        if spec.hint:
            log("{} - {}", spec.name.upper(), spec.hint)
        else:
            log("{}", spec.name.upper())
        log()
        if spec.help:
            log(spec.help)
            log()
        spec.code()


@setting
def DEBUG(value=False):
    """print debug information"""
    if value is None or value in ['false', '', '0', 0]:
        value = False
    if value in ['true', '1', 1]:
        value = True
    if not isinstance(value, bool):
        raise ValueError("debug: expected a Boolean value; got %r" % value)
    env.set(debug=value)


@setting
def CONFIG(config_file=None):
    """config file to retrieve settings from"""
    if not (config_file is None or isinstance(config_file, str)):
        raise ValueError("config: expected a path; got %r" % config_file)
    env.set(config_file=config_file)


