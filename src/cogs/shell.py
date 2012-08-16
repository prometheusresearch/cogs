#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


import sys
import re
import os, os.path
import itertools
import types
import imputil; imputil._os_stat = os.stat
import pkg_resources
import yaml


class Failure(Exception):
    pass


class Environment(object):

    __slots__ = ('_states', '__dict__')

    class _context(object):

        def __init__(self, owner, **updates):
            self.owner = owner
            self.updates = updates

        def __enter__(self):
            self.owner.push(**self.updates)

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.owner.pop()

    def __init__(self):
        self._states = []

    def clear(self):
        self.__dict__.clear()

    def add(self, **updates):
        for key in sorted(updates):
            assert not key.startswith('_'), \
                    "parameter should not start with '_': %r" % key
            assert key not in self.__dict__, \
                    "duplicate parameter %r" % key
            self.__dict__[key] = updates[key]

    def set(self, **updates):
        for key in sorted(updates):
            assert key in self.__dict__, \
                    "unknown parameter %r" % key
            self.__dict__[key] = updates[key]

    def push(self, **updates):
        self._states.append(self.__dict__)
        self.__dict__ = self.__dict__.copy()
        self.set(**updates)

    def pop(self):
        assert self._states, "unbalanced pop()"
        self.__dict__ = self._states.pop()

    def __call__(self, **updates):
        return self._context(self, **updates)


class ArgDsc(object):

    CTR = itertools.count(1)
    REQ = object()

    def __init__(self, check=None, default=REQ, plural=False):
        assert isinstance(plural, bool)
        self.check = check
        self.default = default
        self.plural = plural
        self.order = next(self.CTR)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        raise AttributeError("unset argument")


class OptDsc(object):

    CTR = itertools.count(1)
    NOVAL = object()

    def __init__(self, key=None, check=None, default=NOVAL, plural=False,
                 value_name=None, hint=None):
        assert key is None or (isinstance(key, str) and
                               re.match(r'^[a-zA-Z]$', key)), \
                "key must be a letter, got %r" % key
        assert isinstance(plural, bool)
        assert value_name is None or isinstance(value_name, str)
        assert hint is None or isinstance(hint, str)
        self.key = key
        self.check = check
        self.default = default
        self.plural = plural
        self.value_name = value_name
        self.hint = hint
        self.order = next(self.CTR)


class TaskSpec(object):

    def __init__(self, name, code, args, opts,
                 usage=None, hint=None, help=None):
        self.name = name
        self.code = code
        self.args = args
        self.opts = opts
        self.usage = usage
        self.hint = hint
        self.help = help
        self.opt_by_name = {}
        self.opt_by_key = {}
        for opt in self.opts:
            self.opt_by_name[opt.name] = opt
            if opt.key is not None:
                self.opt_by_key[opt.key] = opt


class SettingSpec(object):

    def __init__(self, name, code, has_value=False, value_name=None,
                 usage=None, usage_conf=None, usage_environ=None,
                 hint=None, help=None):
        self.name = name
        self.code = code
        self.has_value = has_value
        self.value_name = value_name
        self.usage = usage
        self.usage_conf = usage_conf
        self.usage_environ = usage_environ
        self.hint = hint
        self.help = help


class ArgSpec(object):

    def __init__(self, attr, name, check, default,
                 is_optional=False, is_plural=False):
        self.attr = attr
        self.name = name
        self.check = check
        self.default = default
        self.is_optional = is_optional
        self.is_plural = is_plural


class OptSpec(object):

    def __init__(self, attr, name, key, check, default,
                 is_plural=False,  has_value=False, usage=None, hint=None):
        self.attr = attr
        self.name = name
        self.key = key
        self.check = check
        self.default = default
        self.is_plural = is_plural
        self.has_value = has_value
        self.usage = usage
        self.hint = hint


class Shell(object):

    def __init__(self,
                 name,
                 description=None,
                 local_package=None,
                 entry_point=None,
                 config_name=None,
                 config_dirs=None):
        self.name = name
        self.description = description
        self.local_package = local_package
        self.entry_point = entry_point
        self.config_name = config_name
        self.config_dirs = config_dirs
        self.environment = Environment()
        self.task_by_name = {}
        self.setting_by_name = {}

    def register_task(self, T, is_default=False):
        norm_T = self._normalize_task(T)
        name = self._to_name(norm_T.__name__)
        if is_default:
            name = None
        args, opts = self._extract_parameters(norm_T)
        hint, help = self._describe(norm_T)
        optionals = 0
        usage = name
        for arg in args:
            if arg.is_plural:
                assert arg is args[-1], "a plural argument must be the last" \
                        " in the argument list: %s" % arg.name
            if optionals:
                assert arg.is_optional, "a mandatory argument must not follow" \
                        " an optional argument: %s" % arg.name
            if arg.is_optional:
                optionals += 1
                usage = "%s [<%s>" % (usage, arg.name)
            else:
                usage = "%s <%s>" % (usage, arg.name)
            if arg.is_plural:
                usage += "..."
        if optionals:
            usage += "]"*optionals
        task = TaskSpec(name, norm_T, args, opts,
                        usage=usage,
                        hint=hint,
                        help=help)
        self.task_by_name[name] = task
        return T

    def register_default_task(self, T):
        return self.register_task(T, True)

    def register_setting(self, S):
        assert isinstance(S, types.FunctionType), \
                "a setting must be a function"
        params, varargs, varkeywords = self._introspect(S)
        assert (len(params) >= 1 and len(params[0]) == 2) or varargs, \
                "a setting must accept zero or one parameter"
        hint, help = self._describe(S)
        name = self._to_name(S.__name__)
        has_value = (not params or params[0][1] is not False)
        value_name = (params and params[0][0] or varargs)
        if has_value:
            usage = "--%s=%s" % (name, value_name.upper())
            usage_conf = "%s: %s" % (name, value_name.upper())
            usage_environ = "%s_%s=%s" % (self.name.upper(),
                                          name.upper().replace('-', '_'),
                                          value_name.upper())
        else:
            usage = "--%s" % name
            usage_conf = "%s: true" % name
            usage_environ = "%s_%s=1" % (self.name.upper(),
                                         name.upper().replace('-', '_'))
        setting = SettingSpec(name, S,
                              has_value=has_value,
                              value_name=value_name,
                              usage=usage,
                              usage_conf=usage_conf,
                              usage_environ=usage_environ,
                              hint=hint,
                              help=help)
        self.setting_by_name[name] = setting
        return S

    def main(self, argv):
        self._load_extensions()
        config_settings = self._parse_config()
        environ_settings = self._parse_environ()
        task, attrs, argv_settings = self._parse_argv(argv)
        self._init_settings(config_settings, environ_settings, argv_settings)
        exit = self._execute_task(task, attrs)
        return exit

    def run(self):
        debug_var = '%s_DEBUG' % self.name.upper()
        debug = (os.environ.get(debug_var) in ['true', '1'] or
                 '--debug' in sys.argv)
        with self.environment():
            self.environment.clear()
            self.environment.add(debug=debug)
            try:
                return self.main(sys.argv)
            except (Failure, IOError, KeyboardInterrupt), exc:
                if self.environment.debug:
                    raise
                return exc

    def _to_name(self, keyword):
        return keyword.lower().replace(' ', '-').replace('_', '-')

    def _introspect(self, fn):
        # Find function parameters and default values.
        params = []
        varargs = None
        varkeywords = None
        code = fn.func_code
        defaults = fn.func_defaults or ()
        idx = 0
        while idx < code.co_argcount:
            name = code.co_varnames[idx]
            if idx < code.co_argcount-len(defaults):
                params.append(name)
            else:
                default = defaults[idx-code.co_argcount+len(defaults)]
                params.append((name, default))
            idx += 1
        if code.co_flags & 0x04: # CO_VARARGS
            varargs = code.co_varnames[idx]
            idx += 1
        if code.co_flags & 0x08: # CO_VARKEYWORDS
            varkeywords = code.co_varnames[idx]
            idx += 1
        return params, varargs, varkeywords

    def _describe(self, fn):
        # Convert a docstring to a hint line and a description.
        hint = ""
        help = ""
        doc = fn.__doc__
        if doc:
            hint = doc.lstrip().splitlines()[0].rstrip()
            lines = doc.strip().splitlines()[1:]
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop(-1)
            indent = None
            for line in lines:
                short_line = line.lstrip()
                if short_line:
                    line_indent = len(line)-len(short_line)
                    if indent is None or line_indent < indent:
                        indent = line_indent
            if indent:
                lines = [line[indent:] for line in lines]
            help = "\n".join(lines)
        return hint, help

    def _normalize_task(self, T):
        assert isinstance(T, (types.ClassType,
                              types.TypeType,
                              types.FunctionType)), \
                "a task must be either a function or a class"
        if isinstance(T, types.FunctionType):
            T_dict = {}
            T_dict['__module__'] = T.__module__
            T_dict['__doc__'] = T.__doc__
            T_dict['_fn'] = staticmethod(T)
            T_dict['_vararg'] = None
            def __init__(self, **params):
                self._params = params
            T_dict['__init__'] = __init__
            def __call__(self):
                args = ()
                kwds = self._params.copy()
                if self._vararg:
                    args = tuple(kwds.pop(self._vararg))
                return self._fn(*args, **kwds)
            T_dict['__call__'] = __call__
            params, varargs, varkeywords = self._introspect(T)
            for param in params:
                if isinstance(param, str):
                    T_dict[param] = ArgDsc()
                else:
                    param, default = param
                    T_dict[param] = ArgDsc(default=default)
            if varargs:
                T_dict[varargs] = ArgDsc(default=(), plural=True)
                T_dict['_vararg'] = varargs
            T = type(T.__name__, (object,), T_dict)
        elif isinstance(T, types.ClassType):
            T_dict = {}
            T_dict['__module__'] = T.__module__
            T_dict['__doc__'] = T.__doc__
            T = type(T.__name__, (T, object), T_dict)
        return T

    def _extract_parameters(self, T):
        args = []
        opts = []
        attrs = {}
        for C in reversed(T.__mro__):
            attrs.update(C.__dict__)
        arg_attrs = []
        opt_attrs = []
        for attr in sorted(attrs):
            value = attrs[attr]
            if isinstance(value, ArgDsc):
                arg_attrs.append((value.order, attr, value))
            if isinstance(value, OptDsc):
                opt_attrs.append((value.order, attr, value))
        arg_attrs.sort()
        opt_attrs.sort()
        names = set()
        keys = set()
        for order, attr, dsc in arg_attrs:
            name = self._to_name(attr)
            assert name not in names, \
                    "duplicate argument name <%s>" % name
            names.add(name)
            check = dsc.check
            default = dsc.default
            is_plural = dsc.plural
            is_optional = True
            if default is dsc.REQ:
                is_optional = False
                default = None
            arg = ArgSpec(attr, name, check,
                          default=default,
                          is_optional=is_optional,
                          is_plural=is_plural)
            args.append(arg)
        for order, attr, dsc in opt_attrs:
            name = self._to_name(attr)
            assert name not in names, \
                    "duplicate option name --%s" % name
            names.add(name)
            key = dsc.key
            if key is not None:
                assert key not in keys, \
                        "duplicate option name -%s" % key
                keys.add(key)
            check = dsc.check
            default = dsc.default
            is_plural = dsc.plural
            has_value = True
            if default is dsc.NOVAL:
                has_value = False
                default = False
            usage = "--%s" % name
            if key is not None:
                usage = "-%s/%s" % (key, usage)
            if has_value:
                value_name = (dsc.value_name or name).upper()
                usage = "%s=%s" % (usage, value_name)
            hint = dsc.hint
            opt = OptSpec(attr, name, key, check, default,
                          is_plural=is_plural,
                          has_value=has_value,
                          usage=usage,
                          hint=hint)
            opts.append(opt)
        return args, opts

    def _load_extensions(self):
        # Load extensions registered using the entry point.
        if self.entry_point:
            for entry in pkg_resources.iter_entry_points(self.entry_point):
                self._debug("loading extensions from %s" % entry)
                entry.load()
        # Load extensions from the current directory.
        if self.local_package:
            local_dir = os.path.join(os.getcwd(), self.local_package)
            if os.path.isdir(local_dir):
                local_init = os.path.join(local_dir, '__init__.py')
                if not os.path.isfile(local_init):
                    self._warn("cannot load extensions from %s:"
                               " missing __init__.py" % local_dir)
                else:
                    uid = os.stat(local_init).st_uid
                    if not (uid == os.getuid() or uid == 0):
                        self._warn("cannot load extensions from %s:"
                                   " not owned by the user or the root"
                                   % local_dir)
                    else:
                        self._debug("loading extensions from %s" % local_dir)
                        local = types.ModuleType(self.local_package)
                        sys.modules[self.local_package] = local
                        local.__package__ = self.local_package
                        local.__path__ = [local_dir]
                        code = imputil.py_suffix_importer(local_init,
                                os.stat(local_init), self.local_package)[1]
                        exec code in local.__dict__

    def _parse_config(self):
        settings = {}
        # Load settings from configuration files.
        if self.config_name and self.config_dirs:
            for config_dir in self.config_dirs:
                config_path = os.path.join(config_dir, self.config_name)
                if not os.path.isfile(config_path):
                    continue
                self._debug("loading configuration from %s" % config_path)
                try:
                    data = yaml.load(open(config_path, 'r'))
                except yaml.YAMLError, exc:
                    self._warn("failed to load configuration from %s: %s"
                               % (config_path, exc))
                    continue
                if data is None:
                    continue
                if not isinstance(data, dict):
                    self._warn("ill-formed configuration file %s"
                               % config_path)
                    continue
                for key in sorted(data):
                    if not isinstance(key, str):
                        self._warn("invalid setting %r"
                                   " in configuration file %s"
                                   % (key, config_path))
                        continue
                    name = self._to_name(key)
                    if name not in self.setting_by_name:
                        self._warn("unknown setting %s"
                                   " in configuration file %s"
                                   % (key, config_path))
                        continue
                    settings[name] = data[key]
        return settings

    def _parse_environ(self):
        settings = {}
        # Load settings from configuration files.
        prefix = "%s_" % self.name.upper()
        for key in sorted(os.environ):
            if not key.startswith(prefix):
                continue
            name = self._to_name(key[len(prefix):])
            if name not in self.setting_by_name:
                self._warn("unknown setting %s in the environment" % key)
                continue
            settings[name] = os.environ[key]
        return settings

    def _parse_argv(self, argv):
        # Parse command-line parameters.
        settings = {}
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
                name = self._to_name(key[2:])
                if name in self.setting_by_name:
                    setting = self.setting_by_name[name]
                    if setting.has_value and no_value:
                        if not params:
                            raise self._fail("missing value for setting %s"
                                             % key)
                        value = params.pop(0)
                        no_value = False
                    if not setting.has_value:
                        if not no_value:
                            raise self._fail("unexpected value for a toggle"
                                             " setting %s" % key)
                        value = True
                    settings[name] = value
                else:
                    if task is None:
                        task = self.task_by_name[None]
                    if name not in task.opt_by_name:
                        raise self._fail("unknown option or setting %s" % key)
                    opt = task.opt_by_name[name]
                    if opt.has_value and no_value:
                        if not params:
                            raise self._fail("missing value for option %s"
                                             % key)
                        value = params.pop(0)
                        no_value = False
                    if not opt.has_value:
                        if not no_value:
                            raise self._fail("unexpected value for a toggle"
                                             " option %s" % key)
                        value = True
                    if not opt.is_plural:
                        if opt.attr in attrs:
                            raise self._fail("duplicate option %s" % key)
                        attrs[opt.attr] = value
                    else:
                        if opt.attr not in attrs:
                            attrs[opt.attr] = []
                        attrs[opt.attr].append(value)
            elif param.startswith('-') and param != '-' and not no_more_opts:
                if task is None:
                    task = self.task_by_name[None]
                keys = param[1:]
                while keys:
                    key = keys[0]
                    keys = keys[1:]
                    if key not in task.opt_by_key:
                        raise self._fail("unknown option -%s" % key)
                    opt = task.opt_by_key[key]
                    if opt.has_value:
                        if keys:
                            value = keys
                            keys = ''
                        else:
                            if not params:
                                raise self._fail("missing value for option -%s"
                                                 % key)
                            value = params.pop(0)
                    else:
                        value = True
                    if not opt.is_plural:
                        if opt.attr in attrs:
                            raise self._fail("duplicate option -%s" % key)
                        attrs[opt.attr] = value
                    else:
                        if opt.attr not in attrs:
                            attrs[opt.attr] = ()
                        attrs[opt.attr] += (value,)
            elif task is None:
                if param == '-' and not no_more_opts:
                    task = self.task_by_name[None]
                else:
                    name = self._to_name(param)
                    if name not in self.task_by_name:
                        raise self._fail("unknown task %s" % param)
                    task = self.task_by_name[name]
            else:
                if param == '-' and not no_more_opts:
                    param = None
                for arg in task.args:
                    if arg.attr not in attrs or arg.is_plural:
                        break
                else:
                    if task.name:
                        raise self._fail("too many arguments for task %s"
                                         % task.name)
                    else:
                        raise self._fail("too many arguments")
                if arg.is_plural:
                    if arg.attr not in attrs:
                        attrs[arg.attr] = ()
                    attrs[arg.attr] += (param,)
                else:
                    attrs[arg.attr] = param
        if task is None:
            task = self.task_by_name[None]
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
                        raise self._fail("invalid value for option --%s: %s"
                                         % (opt.name, exc))
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
                        raise self._fail("invalid value for argument <%s>: %s"
                                         % (arg.name, exc))
            else:
                if not arg.is_optional:
                    raise self._fail("missing argument <%s>" % arg.name)
                attrs[arg.attr] = arg.default
        return task, attrs, settings

    def _init_settings(self, *values_list):
        # Validate and initialize settings.
        values = {}
        for item in values_list:
            values.update(item)
        for name in sorted(self.setting_by_name):
            setting = self.setting_by_name[name]
            try:
                if name in values:
                    setting.code(values[name])
                else:
                    setting.code()
            except ValueError, exc:
                raise self._fail("invalid value for setting --%s: %s"
                                 % (name, exc))

    def _execute_task(self, task, attrs):
        try:
            instance = task.code(**attrs)
        except ValueError, exc:
            raise self._fail(str(exc))
        return instance()

    def _debug(self, *msgs, **opts):
        from .logutils import LogUtils
        log_utils = LogUtils(self)
        return log_utils.debug(*msgs, **opts)

    def _log(self, *msgs, **opts):
        from .logutils import LogUtils
        log_utils = LogUtils(self)
        return log_utils.log(*msgs, **opts)

    def _warn(self, *msgs, **opts):
        from .logutils import LogUtils
        log_utils = LogUtils(self)
        return log_utils.warn(*msgs, **opts)

    def _fail(self, *msgs, **opts):
        from .logutils import LogUtils
        log_utils = LogUtils(self)
        return log_utils.fail(*msgs, **opts)


