#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from ddt.core import env, Failure, _attr_to_name
from ddt.out import debug, warn, fail
import sys
import os.path
import collections
import imputil
import pkg_resources
import yaml


def main(argv):
    # Load extensions from entry point `ddt.extensions`.
    for entry in pkg_resources.iter_entry_points('ddt.extensions'):
        debug("loading extensions from `%s`" % entry)
        entry.load()
    # Load extensions from `./ddt.local/`.
    cwd = os.getcwd()
    local_dir = os.path.join(cwd, 'ddt.local')
    if os.path.isdir(local_dir):
        local_package = os.path.join(local_dir, '__init__.py')
        if not os.path.isfile(local_package):
            warn("cannot load extensions from `%s`:"
                 " missing `__init__.py`" % local_dir)
        else:
            uid = os.stat(local_package).st_uid
            if not (uid == os.getuid() or uid == 0):
                warn("cannot load extensions from `%s`:"
                     " not owned by the user or the root" % local_dir)
            else:
                debug("loading extensions from `%s`" % local_dir)
                from . import local
                local.__path__.append(local_dir)
                imputil._os_stat = os.stat
                code = imputil.py_suffix_importer(local_package,
                                                  os.stat(local_package),
                                                  'ddt.local')[1]
                exec code in local.__dict__

    # Load configuration files.
    settings = {}
    conf_paths = []
    conf_paths.append('/etc/ddt.conf')
    conf_paths.append(os.path.join(sys.prefix, '/etc/ddt.conf'))
    conf_paths.append(os.path.expanduser('~/.ddt.conf'))
    conf_paths.append(os.path.abspath('./ddt.conf'))
    for conf_path in conf_paths:
        if not os.path.isfile(conf_path):
            continue
        debug("loading configuration from `%s`" % conf_path)
        try:
            data = yaml.load(open(conf_path, 'r'))
        except yaml.YAMLError, exc:
            warn("failed to load configuration from `%s`: %s"
                 % (conf_path, exc))
            continue
        if data is None:
            continue
        if not isinstance(data, dict):
            warn("ill-formed configuration file `%s`" % conf_path)
            continue
        for key in sorted(data):
            if not isinstance(key, str):
                warn("invalid setting `%r` in `%s`"
                     % (key, conf_path))
                continue
            name = _attr_to_name(key)
            if name not in env._setting_by_name:
                warn("unknown setting `%s` in `%s`"
                     % (key, conf_path))
                continue
            settings[name] = data[key]
    for key in sorted(os.environ):
        if key.startswith('DDT_'):
            name = _attr_to_name(key[4:])
            if name not in env._setting_by_name:
                warn("unknown configuration parameter `%s`"
                     " in the environment" % key)
                continue
            settings[name] = os.environ[key]

    # Parse command-line parameters.
    T = None
    args = {}
    opts = {}
    no_more_opts = False
    argv = argv[1:]
    while argv:
        arg = argv.pop(0)
        if arg == '--':
            no_more_opts = True
        elif arg.startswith('--') and not no_more_opts:
            if '=' in arg:
                key, value = arg.split('=', 1)
                no_value = False
            else:
                key = arg
                value = None
                no_value = True
            name = _attr_to_name(key[2:])
            if name in env._setting_by_name:
                S = env._setting_by_name[name]
                if S._has_value and no_value:
                    if not argv:
                        raise fail("missing value for setting `%s`" % key)
                    value = argv.pop(0)
                    no_value = False
                if not S._has_value:
                    if not no_value:
                        raise fail("unexpected value for a toggle setting `%s`"
                                   % key)
                    value = True
                settings[name] = value
            else:
                if T is None:
                    T = env._task_by_name[None]
                if name not in T._opt_by_name:
                    raise fail("unknown option or setting `%s`" % key)
                O = T._opt_by_name[name]
                if O.has_value and no_value:
                    if not argv:
                        raise fail("missing value for option `%s`" % key)
                    value = argv.pop(0)
                    no_value = False
                if not O.has_value:
                    if not no_value:
                        raise fail("unexpected value for a toggle option `%s`"
                                   % key)
                    value = True
                if O.attribute in opts:
                    raise fail("duplicate option `%s`" % key)
                opts[O.attribute] = value
        elif arg.startswith('-') and arg != '-' and not no_more_opts:
            if T is None:
                T = env._task_by_name[None]
            keys = arg[1:]
            while keys:
                key = keys[0]
                keys = keys[1:]
                if key not in T._opt_by_key:
                    raise fail("unknown option `-%s`" % key)
                O = T._opt_by_key[key]
                if O.has_value:
                    if keys:
                        value = keys
                        keys = ''
                    else:
                        if not argv:
                            raise fail("missing value for option `-%s`" % key)
                        value = argv.pop(0)
                else:
                    value = True
                opts[O.attribute] = value
        elif T is None:
            if arg == '-':
                T = env._task_by_name[None]
            else:
                name = _attr_to_name(arg)
                if name not in env._task_by_name:
                    raise fail("unknown task `%s`" % arg)
                T = env._task_by_name[name]
        else:
            if arg == '-':
                arg = None
            for A in T._args:
                if A.attribute not in args or A.is_list:
                    break
            else:
                if T._name:
                    raise fail("too many arguments for task `%s`"
                               % T._name)
                else:
                    raise fail("too many arguments")
            if A.is_list:
                if A.attribute not in args:
                    args[A.attribute] = []
                args[A.attribute].append(arg)
            else:
                args[A.attribute] = arg
    if T is None:
        T = env._task_by_name[None]
    for O in T._opts:
        if O.attribute in opts:
            if O.check is not None:
                try:
                    opts[O.attribute] = O.check(opts[O.attribute])
                except ValueError, exc:
                    raise fail("invalid option `--%s`: %s" % (O.name, exc))
        else:
            opts[O.attribute] = O.default
    for A in T._args:
        if A.attribute in args:
            if A.check is not None:
                try:
                    args[A.attribute] = A.check(args[A.attribute])
                except ValueError, exc:
                    raise fail("invalid argument <%s>: %s" % (A.name, exc))
        else:
            if not A.is_optional:
                if T._name:
                    raise fail("not enough arguments for task `%s`"
                               % T._name)
                else:
                    raise fail("not enough arguments")
            args[A.attribute] = A.default

    # Process settings.
    for name in sorted(env._setting_by_name):
        S = env._setting_by_name[name]
        try:
            if name in settings:
                S(settings[name])
            else:
                S()
        except ValueError, exc:
            raise fail("invalid setting `%s`: %s" % (name, exc))

    # Start the task.
    kwds = {}
    kwds.update(opts)
    kwds.update(args)
    try:
        t = T(**kwds)
    except ValueError, exc:
        raise fail(str(exc))
    exit = t()

    return exit


def run():
    try:
        return main(sys.argv)
    except (Failure, IOError, KeyboardInterrupt), exc:
        if env.debug:
            raise
        return exc


