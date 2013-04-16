#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .core import Failure, Environment, env, _to_name
from .log import warn, debug, fail
import sys
import types
import os, os.path
try:
    import importlib._bootstrap
except ImportError:
    importlib = None
    import imputil; imputil._os_stat = os.stat
import pkg_resources
import yaml


env.add(shell=Environment(name="Cogs",
                          description="""A task dispatching utility""",
                          local_package='cogs.local',
                          entry_point='cogs.extensions',
                          config_name='cogs.conf',
                          config_dirs=['/etc',
                                       os.path.join(sys.prefix, '/etc'),
                                       os.path.expanduser('~/.cogs'),
                                       os.path.abspath('.')]),
        debug=False,
        task_map={},
        setting_map={},
        topic_map={})


def run(argv):

    # Load standard tasks and settings.
    __import__('cogs.std')

    # Load extensions registered using the entry point.
    if env.shell.entry_point:
        for entry in pkg_resources.iter_entry_points(env.shell.entry_point):
            debug("loading extensions from {}", entry)
            entry.load()

    # Load extensions from the current directory.
    if env.shell.local_package:
        local_prefix = os.path.join(os.getcwd(), env.shell.local_package)
        local_module = None
        for path, is_package in [(local_prefix+'.py', False),
                                 (local_prefix+'/__init__.py', True)]:
            if os.path.exists(path):
                local_module = path
                break
        if local_module is not None:
            uid = os.stat(local_module).st_uid
            if not (uid == os.getuid() or uid == 0):
                warn("cannot load extensions from {}:"
                     " not owned by the user or the root", local_module)
            else:
                debug("loading extensions from {}", local_module)
                local = types.ModuleType(env.shell.local_package)
                sys.modules[env.shell.local_package] = local
                if is_package:
                    local.__package__ = env.shell.local_package
                    local.__path__ = [local_prefix]
                if importlib is not None:
                    loader = importlib._bootstrap.SourceFileLoader(
                            env.shell.local_package, local_module)
                    code = loader.get_code()
                else:
                    code = imputil.py_suffix_importer(local_module,
                            os.stat(local_module), env.shell.local_package)[1]
                exec code in local.__dict__

    # Initialize settings.
    settings = {}

    # Load settings from configuration files.
    if env.shell.config_name and env.shell.config_dirs:
        for config_dir in env.shell.config_dirs:
            config_path = os.path.join(config_dir, env.shell.config_name)
            if not os.path.isfile(config_path):
                continue
            debug("loading configuration from {}", config_path)
            try:
                data = yaml.load(open(config_path, 'r'))
            except yaml.YAMLError, exc:
                warn("failed to load configuration from {}: {}",
                     config_path, exc)
                continue
            if data is None:
                continue
            if not isinstance(data, dict):
                warn("ill-formed configuration file {}", config_path)
                continue
            for key in sorted(data):
                if not isinstance(key, str):
                    warn("invalid setting {!r}"
                         " in configuration file {}", key, config_path)
                    continue
                name = _to_name(key)
                if name not in env.setting_map:
                    warn("unknown setting {} in configuration file {}",
                         key, config_path)
                    continue
                settings[name] = data[key]

    # Load settings from environment variables.
    prefix = "%s_" % env.shell.name.upper().replace('-', '_')
    for key in sorted(os.environ):
        if not key.startswith(prefix):
            continue
        name = _to_name(key[len(prefix):])
        if name not in env.setting_map:
            warn("unknown setting {} in the environment", key)
            continue
        settings[name] = os.environ[key]

    # Parse command-line parameters.
    task = None
    attrs = {}
    no_more_opts = False
    params = argv[1:]
    while params:
        param = params.pop(0)
        if param == '--' and not no_more_opts:
            no_more_opts = True
        elif param.startswith('--') and not no_more_opts:
            if '=' in param:
                key, value = param.split('=', 1)
                no_value = False
            else:
                key = param
                value = None
                no_value = True
            name = _to_name(key[2:])
            if name in env.setting_map:
                spec = env.setting_map[name]
                if spec.has_value and no_value:
                    if not params:
                        raise fail("missing value for setting {}", key)
                    value = params.pop(0)
                    no_value = False
                if not spec.has_value:
                    if not no_value:
                        raise fail("unexpected value for toggle"
                                   " setting {}", key)
                    value = True
                settings[name] = value
            else:
                if task is None:
                    task = env.task_map['']
                if name not in task.opt_by_name:
                    raise fail("unknown option or setting {}", key)
                opt = task.opt_by_name[name]
                if opt.has_value and no_value:
                    if not params:
                        raise fail("missing value for option {}", key)
                    value = params.pop(0)
                    no_value = False
                if not opt.has_value:
                    if not no_value:
                        raise fail("unexpected value for a toggle"
                                   " option {}", key)
                    value = True
                if not opt.is_plural:
                    if opt.attr in attrs:
                        raise fail("duplicate option {}", key)
                    attrs[opt.attr] = value
                else:
                    if opt.attr not in attrs:
                        attrs[opt.attr] = []
                    attrs[opt.attr].append(value)
        elif param.startswith('-') and param != '-' and not no_more_opts:
            if task is None:
                task = env.task_map['']
            keys = param[1:]
            while keys:
                key = keys[0]
                keys = keys[1:]
                if key not in task.opt_by_key:
                    raise fail("unknown option -{}", key)
                opt = task.opt_by_key[key]
                if opt.has_value:
                    if keys:
                        value = keys
                        keys = ''
                    else:
                        if not params:
                            raise fail("missing value for option -{}", key)
                        value = params.pop(0)
                else:
                    value = True
                if not opt.is_plural:
                    if opt.attr in attrs:
                        raise fail("duplicate option -{}", key)
                    attrs[opt.attr] = value
                else:
                    if opt.attr not in attrs:
                        attrs[opt.attr] = ()
                    attrs[opt.attr] += (value,)
        elif task is None:
            if param == '-' and not no_more_opts:
                task = env.task_map['']
            else:
                name = _to_name(param)
                if name not in env.task_map:
                    raise fail("unknown task {}", param)
                task = env.task_map[name]
        else:
            if param == '-' and not no_more_opts:
                param = None
            for arg in task.args:
                if arg.attr not in attrs or arg.is_plural:
                    break
            else:
                if task.name:
                    raise fail("too many arguments for task {}", task.name)
                else:
                    raise fail("too many arguments")
            if arg.is_plural:
                if arg.attr not in attrs:
                    attrs[arg.attr] = ()
                attrs[arg.attr] += (param,)
            else:
                attrs[arg.attr] = param
    if task is None:
        task = env.task_map['']
    for opt in task.opts:
        if opt.attr in attrs:
            if opt.check is not None:
                try:
                    if opt.is_plural:
                        attrs[opt.attr] = tuple(opt.check(value)
                                                for value in attrs[opt.attr])
                    else:
                        attrs[opt.attr] = opt.check(attrs[opt.attr])
                except ValueError, exc:
                    raise fail("invalid value for option --{}: {}",
                               opt.name, exc)
        else:
            attrs[opt.attr] = opt.default
    for arg in task.args:
        if arg.attr in attrs:
            if arg.check is not None:
                try:
                    if arg.is_plural:
                        attrs[arg.attr] = tuple(arg.check(value)
                                                for value in attrs[arg.attr])
                    else:
                        attrs[arg.attr] = arg.check(attrs[arg.attr])
                except ValueError, exc:
                    raise fail("invalid value for argument <{}>: {}",
                               arg.name, exc)
        else:
            if not arg.is_optional:
                raise fail("missing argument <{}>", arg.name)
            attrs[arg.attr] = arg.default

    # Initialize settings.
    for name in sorted(env.setting_map):
        spec = env.setting_map[name]
        try:
            if name in settings:
                spec.code(settings[name])
            else:
                spec.code()
        except ValueError, exc:
            raise fail("invalid value for setting --{}: {}", name, exc)

    # Execute the task.
    try:
        instance = task.code(**attrs)
    except ValueError, exc:
        raise fail("{}", exc)
    return instance()


def main():
    """Loads configuration, parses parameters and executes a task."""
    with env():
        debug_var = '%s_DEBUG' % env.shell.name.upper().replace('-', '_')
        if (os.environ.get(debug_var) in ['true', '1'] or
                (len(sys.argv) > 1 and sys.argv[1] == '--debug')):
            env.set(debug=True)
        try:
            return run(sys.argv)
        except (Failure, IOError, KeyboardInterrupt), exc:
            if env.debug:
                raise
            return exc


