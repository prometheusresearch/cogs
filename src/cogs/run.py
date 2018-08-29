#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from .core import Failure, Environment, env, _to_name
from .log import warn, debug, fail
import sys
import types
import os.path
try:
    # Python 3.
    import importlib._bootstrap
except ImportError:
    # Python 2.
    importlib = None
    import imputil
    imputil._os_stat = os.stat
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
        config_file=None,
        task_map={},
        setting_map={},
        topic_map={})


_DEFAULT = object()
def _init_setting(name, value=_DEFAULT, seen=set()):
    # Initialize the setting once.

    # Terrible abuse of a mutable default value to prevent the setting from
    # being initialized more than once.
    if name in seen:
        return
    seen.add(name)

    spec = env.setting_map[name]
    try:
        if value is not _DEFAULT:
            spec.code(value)
        else:
            spec.code()
    except ValueError, exc:
        raise fail("invalid value for setting --{}: {}", name, exc)


def _load_extensions():
    # Load standard tasks and settings.
    __import__('cogs.std')

    # Load extensions registered using the entry point.
    if env.shell.entry_point:
        for entry in pkg_resources.iter_entry_points(env.shell.entry_point):
            debug("loading extensions from {}", entry)
            entry.load()

    # Load extensions from the current directory.
    if env.shell.local_package:
        package = env.shell.local_package
        prefix = os.path.join(os.getcwd(), package)
        module = None
        for path, is_package in [(prefix+'.py', False),
                                 (prefix+'/__init__.py', True)]:
            if os.path.exists(path):
                module = path
                break
        if module is not None:
            uid = os.stat(module).st_uid
            if not (uid == os.getuid() or uid == 0):
                warn("cannot load extensions from {}:"
                     " not owned by the user or the root", module)
            else:
                # Create and import a module object.
                debug("loading extensions from {}", module)
                local = types.ModuleType(package)
                sys.modules[package] = local
                if is_package:
                    local.__package__ = package
                    local.__path__ = [prefix]
                if importlib is not None:
                    # Python 3.
                    loader = importlib._bootstrap.SourceFileLoader(
                            package, module)
                    code = loader.get_code(None)
                else:
                    # Python 2.
                    code = imputil.py_suffix_importer(
                            module, os.stat(module), package)[1]
                exec code in local.__dict__


def _parse_argv(argv):
    # Parse command line parameters.

    # Task and values for its arguments and options.
    task = None
    attrs = {}

    # Have we seen `--`?
    no_more_opts = False
    # Parameters to process.
    params = argv[1:]
    # Parameters containing task arguments.
    arg_params = []
    while params:
        param = params.pop(0)

        # Treat the remaining parameters as arguments even
        # if they start with `-`.
        if param == '--' and not no_more_opts:
            no_more_opts = True

        # Must be a setting or an option in the long form.
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
                # Ok, it is a setting.
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
                _init_setting(name, value)
            else:
                # Must be a task option.
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

        # Option or a collection of options in short form.
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

        # First parameter that is not a setting or an option must be
        # the task name.
        elif task is None:
            if param == '-' and not no_more_opts:
                task = env.task_map['']
            else:
                name = _to_name(param)
                if name not in env.task_map:
                    raise fail("unknown task {}", param)
                task = env.task_map[name]

        # A task argument.
        else:
            if param == '-' and not no_more_opts:
                param = None
            arg_params.append(param)

    # It is the default task.
    if task is None:
        task = env.task_map['']

    # Verify the number of arguments.
    min_args = max_args = 0
    for arg in task.args:
        if max_args is not None:
            max_args += 1
        if not arg.is_optional:
            min_args += 1
        if arg.is_plural:
            max_args = None
    if max_args is not None and len(arg_params) > max_args:
        if task.name:
            raise fail("too many arguments for task {}", task.name)
        else:
            raise fail("too many arguments")
    if len(arg_params) < min_args:
        missing = []
        for arg in task.args:
            if not arg.is_optional:
                if arg_params:
                    arg_params.pop(0)
                else:
                    missing.append(arg.name)
        missing = " ".join("<%s>" % name for name in missing)
        if task.name:
            raise fail("too few arguments for task {}: missing {}",
                       task.name, missing)
        else:
            raise fail("too few arguments: missing {}", missing)

    # Extract arguments into attributes.
    for pos, arg in reversed(list(enumerate(task.args))):
        if arg.is_optional and pos >= len(arg_params):
            continue
        if arg.is_plural:
            attrs[arg.attr] = ()
            while pos < len(arg_params):
                attrs[arg.attr] = (arg_params.pop(),)+attrs[arg.attr]
        else:
            attrs[arg.attr] = arg_params.pop()

    # Validate options.
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

    # Validate arguments.
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
            attrs[arg.attr] = arg.default

    return task, attrs


def _configure_environ():
    # Load settings from environment variables.
    prefix = "%s_" % env.shell.name.upper().replace('-', '_')
    for key in sorted(os.environ):
        if not key.startswith(prefix):
            continue
        name = _to_name(key[len(prefix):])
        if name not in env.setting_map:
            warn("unknown setting {} in the environment", key)
            continue
        _init_setting(name, os.environ[key])


def _configure_file(config_path):
    debug("loading configuration from {}", config_path)
    try:
        data = yaml.load(open(config_path, 'r'))
    except yaml.YAMLError, exc:
        warn("failed to load configuration from {}: {}",
             config_path, exc)
        return

    if data is None:
        return

    if not isinstance(data, dict):
        warn("ill-formed configuration file {}", config_path)
        return

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

        _init_setting(name, data[key])


def _configure():
    # Load and initialize settings.

    # Load settings from the process environment.
    _configure_environ()

    # Load settings from configuration files.
    if env.config_file:
        if not os.path.isfile(env.config_file):
            raise fail('specified configuration file {} does not exist',
                       env.config_file)
        _configure_file(env.config_file)
    if env.shell.config_name and env.shell.config_dirs:
        for config_dir in reversed(env.shell.config_dirs):
            config_path = os.path.join(config_dir, env.shell.config_name)
            if os.path.isfile(config_path):
                _configure_file(config_path)

    # Initialize the remaining settings.
    for name in sorted(env.setting_map):
        _init_setting(name)


def run(argv):
    # Load all the extensions.
    _load_extensions()

    # Parse command-line parameters.
    task, attrs = _parse_argv(argv)

    # Load settings from environment variables and configuration files.
    _configure()

    # Execute the task.
    try:
        instance = task.code(**attrs)
    except ValueError, exc:
        raise fail("{}", exc)
    return instance()


def main():
    """Loads configuration, parses parameters and executes a task."""
    with env():
        # Enable debugging early if we are certain it's turned on.
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


