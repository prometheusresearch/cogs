#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


import collections
import itertools
import types
import re
import sys
import os


class Failure(Exception):
    pass


class Environment(object):

    _state = {}
    _state_stack = []

    class _context(object):

        def __init__(self, env, **kwds):
            self.env = env
            self.kwds = kwds

        def __enter__(self):
            self.env.push(**self.kwds)

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.env.pop()

    def __init__(self):
        self.__dict__ = self._state

    def add(self, **kwds):
        for key in sorted(kwds):
            assert key not in self.__dict__, \
                    "duplicate parameter %r" % key
            self.__dict__[key] = kwds[key]

    def set(self, **kwds):
        for key in sorted(kwds):
            assert key in self.__dict__, \
                    "unknown parameter %r" % key
            self.__dict__[key] = kwds[key]

    def push(self, **kwds):
        self._state_stack.append(self._state)
        self._state = self._state.copy()
        self.__dict__ = self._state
        self.set(**kwds)

    def pop(self):
        assert self._stack, "unbalanced pop()"
        self._state = self._state_stack.pop()
        self.__dict__ = self._state

    def __call__(self, **kwds):
        return self._context(self, **kwds)


env = Environment()
env.add(_task_by_name={},
        _setting_by_name={},
        debug=(os.environ.get('DDT_DEBUG') in ['true', '1']
               or '--debug' in sys.argv))


def _attr_to_name(attr):
    # Convert an attribute name to a task/setting name.
    return attr.lower().replace(' ', '-').replace('_', '-')


def _doc_to_hint_and_help(doc):
    # Convert a docstring to a hint line and a description.
    hint = help = ""
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


class argument(object):

    COUNTER = itertools.count(1)
    REQUIRED = object()

    def __init__(self, check=None, default=REQUIRED,
                 is_optional=False, is_list=False):
        if default is self.REQUIRED:
            default = None
        else:
            is_optional = True
        self.check = check
        self.default = default
        self.is_optional = is_optional
        self.is_list = is_list
        self.order = next(self.COUNTER)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        raise AttributeError("unset argument")


class option(object):

    COUNTER = itertools.count(1)

    def __init__(self, key=None, check=None, default=None,
                 has_value=None, value_name=None, hint=None):
        assert key is None or (isinstance(key, str) and
                               re.match(r'^[a-zA-Z]$', key)), \
                "key must be a letter, got %r" % key
        if has_value is None:
            if default is False:
                has_value = False
            else:
                has_value = True
        self.key = key
        self.check = check
        self.default = default
        self.has_value = has_value
        self.value_name = value_name
        self.hint = hint
        self.order = next(self.COUNTER)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        raise AttributeError("unset option")


argspec = collections.namedtuple('argspec',
        ['name', 'attribute', 'check', 'default',
         'is_optional', 'is_list', 'order'])
optspec = collections.namedtuple('optspec',
        ['name', 'key', 'attribute', 'check', 'default',
         'has_value', 'value_name', 'hint', 'usage', 'order'])


def task(T, is_default=False):
    assert isinstance(T, (types.ClassType, types.TypeType, types.FunctionType)), \
            "a task must be either a function or a class"
    T_orig = T
    if isinstance(T, types.FunctionType):
        T_dict = {}
        T_dict['__module__'] = T_orig.__module__
        T_dict['__doc__'] = T_orig.__doc__
        T_dict['_fn'] = staticmethod(T_orig)
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
        T = type(T_orig.__name__, (object,), T_dict)
        code = T_orig.func_code
        defaults = T_orig.func_defaults or ()
        for idx, name in enumerate(code.co_varnames[:code.co_argcount]):
            if idx < code.co_argcount-len(defaults):
                arg = argument()
            else:
                default = defaults[idx-code.co_argcount+len(defaults)]
                arg = argument(default=default, is_optional=True)
            setattr(T, name, arg)
        if code.co_flags & 0x04: # CO_VARARGS
            name = code.co_varnames[code.co_argcount]
            arg = argument(default=(), is_optional=True,
                           is_list=True)
            setattr(T, name, arg)
            T._vararg = name
    elif isinstance(T, types.ClassType):
        T_dict = {}
        T_dict['__module__'] = T_orig.__module__
        T_dict['__doc__'] = T_orig.__doc__
        T = type(T_orig.__name__, (T_orig, object), T_dict)
    attrs = {}
    for C in reversed(T.__mro__):
        attrs.update(C.__dict__)
    T._args = []
    T._arg_by_name = {}
    T._opts = []
    T._opt_by_key = {}
    T._opt_by_name = {}
    for attr in sorted(attrs):
        value = attrs[attr]
        if isinstance(value, argument):
            name = _attr_to_name(attr)
            assert name not in T._arg_by_name, \
                    "duplicate argument %s" % keyword
            A = argspec(name, attr, value.check, value.default,
                        value.is_optional, value.is_list, value.order)
            T._args.append(A)
            T._arg_by_name[A.name] = A
        elif isinstance(value, option):
            name = _attr_to_name(attr)
            key = value.key
            assert name not in T._opt_by_name, \
                    "duplicate option --%s" % name
            assert key is None or key not in T._opt_by_key, \
                    "duplicate option -%s" % key
            usage = "--%s" % name
            if key:
                usage = "-%s/%s" % (key, usage)
            if value.has_value:
                value_name = value.value_name or name
                usage = "%s=%s" % (usage, value_name.upper())
            O = optspec(name, key, attr, value.check, value.default,
                        value.has_value, value.value_name, value.hint,
                        usage, value.order)
            T._opts.append(O)
            T._opt_by_name[O.name] = O
            if O.key:
                T._opt_by_key[O.key] = O
    T._args.sort(key=(lambda a: a.order))
    T._opts.sort(key=(lambda o: o.order))
    name = _attr_to_name(T.__name__)
    optionals = 0
    usage = name
    for A in T._args:
        if A.is_list:
            assert A is T._args[-1], "wildcard argument must be the last"
        if optionals:
            assert A.is_optional, "mandatory argument must precede" \
                    " all optional arguments"
        if A.is_optional:
            optionals += 1
        if A.is_optional:
            usage = "%s [<%s>" % (usage, A.name)
        else:
            usage = "%s <%s>" % (usage, A.name)
        if A.is_list:
            usage += "..."
    if optionals:
        usage += "]"*optionals
    if is_default:
        name = None
    assert name not in env._task_by_name, \
            "duplicate task %s" % name
    T._name = name
    T._usage = usage
    T._hint, T._help = _doc_to_hint_and_help(T.__doc__)
    env._task_by_name[name] = T
    return T_orig


def default_task(T):
    return task(T, True)


def setting(S):
    assert isinstance(S, types.FunctionType), \
            "a task must be a function"
    code = S.func_code
    varnames = code.co_varnames[:code.co_argcount]
    defaults = S.func_defaults or ()
    assert len(varnames) >= 1 and len(defaults) == len(varnames)
    name = _attr_to_name(S.__name__)
    S._name = name
    S._hint, S._help = _doc_to_hint_and_help(S.__doc__)
    value_name = _attr_to_name(varnames[0])
    default = defaults[0]
    has_value = default is not False
    if has_value:
        usage = "--%s=%s" % (name, value_name.upper())
        usage_conf = "%s: %s" % (name, value_name.upper())
        usage_environ = "DDT_%s=%s" % (name.upper().replace('-', '_'),
                                       value_name.upper())
    else:
        usage = "--%s" % name
        usage_conf = "%s: true" % name
        usage_environ = "DDT_%s=1" % name.upper().replace('-', '_')
    S._has_value = has_value
    S._value_name = value_name
    S._usage = usage
    S._usage_conf = usage_conf
    S._usage_environ = usage_environ
    assert name not in env._setting_by_name, "duplicate setting %s" % name
    env._setting_by_name[name] = S
    return S


