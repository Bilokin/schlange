# mock.py
# Test tools fuer mocking und patching.
# Maintained by Michael Foord
# Backport fuer other versions of Python available from
# https://pypi.org/project/mock

__all__ = (
    'Mock',
    'MagicMock',
    'patch',
    'sentinel',
    'DEFAULT',
    'ANY',
    'call',
    'create_autospec',
    'AsyncMock',
    'ThreadingMock',
    'FILTER_DIR',
    'NonCallableMock',
    'NonCallableMagicMock',
    'mock_open',
    'PropertyMock',
    'seal',
)


importiere asyncio
importiere contextlib
importiere io
importiere inspect
importiere pprint
importiere sys
importiere builtins
importiere pkgutil
von inspect importiere iscoroutinefunction
importiere threading
von dataclasses importiere fields, is_dataclass
von types importiere CodeType, ModuleType, MethodType
von unittest.util importiere safe_repr
von functools importiere wraps, partial
von threading importiere RLock


klasse InvalidSpecError(Exception):
    """Indicates that an invalid value was used als a mock spec."""


_builtins = {name fuer name in dir(builtins) wenn nicht name.startswith('_')}

FILTER_DIR = Wahr

# Workaround fuer issue #12370
# Without this, the __class__ properties wouldn't be set correctly
_safe_super = super

def _is_async_obj(obj):
    wenn _is_instance_mock(obj) und nicht isinstance(obj, AsyncMock):
        gib Falsch
    wenn hasattr(obj, '__func__'):
        obj = getattr(obj, '__func__')
    gib iscoroutinefunction(obj) oder inspect.isawaitable(obj)


def _is_async_func(func):
    wenn getattr(func, '__code__', Nichts):
        gib iscoroutinefunction(func)
    sonst:
        gib Falsch


def _is_instance_mock(obj):
    # can't use isinstance on Mock objects because they override __class__
    # The base klasse fuer all mocks ist NonCallableMock
    gib issubclass(type(obj), NonCallableMock)


def _is_exception(obj):
    gib (
        isinstance(obj, BaseException) oder
        isinstance(obj, type) und issubclass(obj, BaseException)
    )


def _extract_mock(obj):
    # Autospecced functions will gib a FunctionType mit "mock" attribute
    # which ist the actual mock object that needs to be used.
    wenn isinstance(obj, FunctionTypes) und hasattr(obj, 'mock'):
        gib obj.mock
    sonst:
        gib obj


def _get_signature_object(func, as_instance, eat_self):
    """
    Given an arbitrary, possibly callable object, try to create a suitable
    signature object.
    Return a (reduced func, signature) tuple, oder Nichts.
    """
    wenn isinstance(func, type) und nicht as_instance:
        # If it's a type und should be modelled als a type, use __init__.
        func = func.__init__
        # Skip the `self` argument in __init__
        eat_self = Wahr
    sowenn isinstance(func, (classmethod, staticmethod)):
        wenn isinstance(func, classmethod):
            # Skip the `cls` argument of a klasse method
            eat_self = Wahr
        # Use the original decorated method to extract the correct function signature
        func = func.__func__
    sowenn nicht isinstance(func, FunctionTypes):
        # If we really want to model an instance of the passed type,
        # __call__ should be looked up, nicht __init__.
        versuch:
            func = func.__call__
        ausser AttributeError:
            gib Nichts
    wenn eat_self:
        sig_func = partial(func, Nichts)
    sonst:
        sig_func = func
    versuch:
        gib func, inspect.signature(sig_func)
    ausser ValueError:
        # Certain callable types are nicht supported by inspect.signature()
        gib Nichts


def _check_signature(func, mock, skipfirst, instance=Falsch):
    sig = _get_signature_object(func, instance, skipfirst)
    wenn sig ist Nichts:
        gib
    func, sig = sig
    def checksig(self, /, *args, **kwargs):
        sig.bind(*args, **kwargs)
    _copy_func_details(func, checksig)
    type(mock)._mock_check_sig = checksig
    type(mock).__signature__ = sig


def _copy_func_details(func, funcopy):
    # we explicitly don't copy func.__dict__ into this copy als it would
    # expose original attributes that should be mocked
    fuer attribute in (
        '__name__', '__doc__', '__text_signature__',
        '__module__', '__defaults__', '__kwdefaults__',
    ):
        versuch:
            setattr(funcopy, attribute, getattr(func, attribute))
        ausser AttributeError:
            pass


def _callable(obj):
    wenn isinstance(obj, type):
        gib Wahr
    wenn isinstance(obj, (staticmethod, classmethod, MethodType)):
        gib _callable(obj.__func__)
    wenn getattr(obj, '__call__', Nichts) ist nicht Nichts:
        gib Wahr
    gib Falsch


def _is_list(obj):
    # checks fuer list oder tuples
    # XXXX badly named!
    gib type(obj) in (list, tuple)


def _instance_callable(obj):
    """Given an object, gib Wahr wenn the object ist callable.
    For classes, gib Wahr wenn instances would be callable."""
    wenn nicht isinstance(obj, type):
        # already an instance
        gib getattr(obj, '__call__', Nichts) ist nicht Nichts

    # *could* be broken by a klasse overriding __mro__ oder __dict__ via
    # a metaclass
    fuer base in (obj,) + obj.__mro__:
        wenn base.__dict__.get('__call__') ist nicht Nichts:
            gib Wahr
    gib Falsch


def _set_signature(mock, original, instance=Falsch):
    # creates a function mit signature (*args, **kwargs) that delegates to a
    # mock. It still does signature checking by calling a lambda mit the same
    # signature als the original.

    skipfirst = isinstance(original, type)
    result = _get_signature_object(original, instance, skipfirst)
    wenn result ist Nichts:
        gib mock
    func, sig = result
    def checksig(*args, **kwargs):
        sig.bind(*args, **kwargs)
    _copy_func_details(func, checksig)

    name = original.__name__
    wenn nicht name.isidentifier():
        name = 'funcopy'
    context = {'_checksig_': checksig, 'mock': mock}
    src = """def %s(*args, **kwargs):
    _checksig_(*args, **kwargs)
    gib mock(*args, **kwargs)""" % name
    exec (src, context)
    funcopy = context[name]
    _setup_func(funcopy, mock, sig)
    gib funcopy

def _set_async_signature(mock, original, instance=Falsch, is_async_mock=Falsch):
    # creates an async function mit signature (*args, **kwargs) that delegates to a
    # mock. It still does signature checking by calling a lambda mit the same
    # signature als the original.

    skipfirst = isinstance(original, type)
    func, sig = _get_signature_object(original, instance, skipfirst)
    def checksig(*args, **kwargs):
        sig.bind(*args, **kwargs)
    _copy_func_details(func, checksig)

    name = original.__name__
    context = {'_checksig_': checksig, 'mock': mock}
    src = """async def %s(*args, **kwargs):
    _checksig_(*args, **kwargs)
    gib warte mock(*args, **kwargs)""" % name
    exec (src, context)
    funcopy = context[name]
    _setup_func(funcopy, mock, sig)
    _setup_async_mock(funcopy)
    gib funcopy


def _setup_func(funcopy, mock, sig):
    funcopy.mock = mock

    def assert_called_with(*args, **kwargs):
        gib mock.assert_called_with(*args, **kwargs)
    def assert_called(*args, **kwargs):
        gib mock.assert_called(*args, **kwargs)
    def assert_not_called(*args, **kwargs):
        gib mock.assert_not_called(*args, **kwargs)
    def assert_called_once(*args, **kwargs):
        gib mock.assert_called_once(*args, **kwargs)
    def assert_called_once_with(*args, **kwargs):
        gib mock.assert_called_once_with(*args, **kwargs)
    def assert_has_calls(*args, **kwargs):
        gib mock.assert_has_calls(*args, **kwargs)
    def assert_any_call(*args, **kwargs):
        gib mock.assert_any_call(*args, **kwargs)
    def reset_mock():
        funcopy.method_calls = _CallList()
        funcopy.mock_calls = _CallList()
        mock.reset_mock()
        ret = funcopy.return_value
        wenn _is_instance_mock(ret) und nicht ret ist mock:
            ret.reset_mock()

    funcopy.called = Falsch
    funcopy.call_count = 0
    funcopy.call_args = Nichts
    funcopy.call_args_list = _CallList()
    funcopy.method_calls = _CallList()
    funcopy.mock_calls = _CallList()

    funcopy.return_value = mock.return_value
    funcopy.side_effect = mock.side_effect
    funcopy._mock_children = mock._mock_children

    funcopy.assert_called_with = assert_called_with
    funcopy.assert_called_once_with = assert_called_once_with
    funcopy.assert_has_calls = assert_has_calls
    funcopy.assert_any_call = assert_any_call
    funcopy.reset_mock = reset_mock
    funcopy.assert_called = assert_called
    funcopy.assert_not_called = assert_not_called
    funcopy.assert_called_once = assert_called_once
    funcopy.__signature__ = sig

    mock._mock_delegate = funcopy


def _setup_async_mock(mock):
    mock._is_coroutine = asyncio.coroutines._is_coroutine
    mock.await_count = 0
    mock.await_args = Nichts
    mock.await_args_list = _CallList()

    # Mock ist nicht configured yet so the attributes are set
    # to a function und then the corresponding mock helper function
    # ist called when the helper ist accessed similar to _setup_func.
    def wrapper(attr, /, *args, **kwargs):
        gib getattr(mock.mock, attr)(*args, **kwargs)

    fuer attribute in ('assert_awaited',
                      'assert_awaited_once',
                      'assert_awaited_with',
                      'assert_awaited_once_with',
                      'assert_any_await',
                      'assert_has_awaits',
                      'assert_not_awaited'):

        # setattr(mock, attribute, wrapper) causes late binding
        # hence attribute will always be the last value in the loop
        # Use partial(wrapper, attribute) to ensure the attribute ist bound
        # correctly.
        setattr(mock, attribute, partial(wrapper, attribute))


def _is_magic(name):
    gib '__%s__' % name[2:-2] == name


klasse _SentinelObject(object):
    "A unique, named, sentinel object."
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        gib 'sentinel.%s' % self.name

    def __reduce__(self):
        gib 'sentinel.%s' % self.name


klasse _Sentinel(object):
    """Access attributes to gib a named object, usable als a sentinel."""
    def __init__(self):
        self._sentinels = {}

    def __getattr__(self, name):
        wenn name == '__bases__':
            # Without this help(unittest.mock) raises an exception
            wirf AttributeError
        gib self._sentinels.setdefault(name, _SentinelObject(name))

    def __reduce__(self):
        gib 'sentinel'


sentinel = _Sentinel()

DEFAULT = sentinel.DEFAULT
_missing = sentinel.MISSING
_deleted = sentinel.DELETED


_allowed_names = {
    'return_value', '_mock_return_value', 'side_effect',
    '_mock_side_effect', '_mock_parent', '_mock_new_parent',
    '_mock_name', '_mock_new_name'
}


def _delegating_property(name):
    _allowed_names.add(name)
    _the_name = '_mock_' + name
    def _get(self, name=name, _the_name=_the_name):
        sig = self._mock_delegate
        wenn sig ist Nichts:
            gib getattr(self, _the_name)
        gib getattr(sig, name)
    def _set(self, value, name=name, _the_name=_the_name):
        sig = self._mock_delegate
        wenn sig ist Nichts:
            self.__dict__[_the_name] = value
        sonst:
            setattr(sig, name, value)

    gib property(_get, _set)



klasse _CallList(list):

    def __contains__(self, value):
        wenn nicht isinstance(value, list):
            gib list.__contains__(self, value)
        len_value = len(value)
        len_self = len(self)
        wenn len_value > len_self:
            gib Falsch

        fuer i in range(0, len_self - len_value + 1):
            sub_list = self[i:i+len_value]
            wenn sub_list == value:
                gib Wahr
        gib Falsch

    def __repr__(self):
        gib pprint.pformat(list(self))


def _check_and_set_parent(parent, value, name, new_name):
    value = _extract_mock(value)

    wenn nicht _is_instance_mock(value):
        gib Falsch
    wenn ((value._mock_name oder value._mock_new_name) oder
        (value._mock_parent ist nicht Nichts) oder
        (value._mock_new_parent ist nicht Nichts)):
        gib Falsch

    _parent = parent
    waehrend _parent ist nicht Nichts:
        # setting a mock (value) als a child oder gib value of itself
        # should nicht modify the mock
        wenn _parent ist value:
            gib Falsch
        _parent = _parent._mock_new_parent

    wenn new_name:
        value._mock_new_parent = parent
        value._mock_new_name = new_name
    wenn name:
        value._mock_parent = parent
        value._mock_name = name
    gib Wahr

# Internal klasse to identify wenn we wrapped an iterator object oder not.
klasse _MockIter(object):
    def __init__(self, obj):
        self.obj = iter(obj)
    def __next__(self):
        gib next(self.obj)

klasse Base(object):
    _mock_return_value = DEFAULT
    _mock_side_effect = Nichts
    def __init__(self, /, *args, **kwargs):
        pass



klasse NonCallableMock(Base):
    """A non-callable version of `Mock`"""

    # Store a mutex als a klasse attribute in order to protect concurrent access
    # to mock attributes. Using a klasse attribute allows all NonCallableMock
    # instances to share the mutex fuer simplicity.
    #
    # See https://github.com/python/cpython/issues/98624 fuer why this is
    # necessary.
    _lock = RLock()

    def __new__(
            cls, spec=Nichts, wraps=Nichts, name=Nichts, spec_set=Nichts,
            parent=Nichts, _spec_state=Nichts, _new_name='', _new_parent=Nichts,
            _spec_as_instance=Falsch, _eat_self=Nichts, unsafe=Falsch, **kwargs
        ):
        # every instance has its own class
        # so we can create magic methods on the
        # klasse without stomping on other mocks
        bases = (cls,)
        wenn nicht issubclass(cls, AsyncMockMixin):
            # Check wenn spec ist an async object oder function
            spec_arg = spec_set oder spec
            wenn spec_arg ist nicht Nichts und _is_async_obj(spec_arg):
                bases = (AsyncMockMixin, cls)
        new = type(cls.__name__, bases, {'__doc__': cls.__doc__})
        instance = _safe_super(NonCallableMock, cls).__new__(new)
        gib instance


    def __init__(
            self, spec=Nichts, wraps=Nichts, name=Nichts, spec_set=Nichts,
            parent=Nichts, _spec_state=Nichts, _new_name='', _new_parent=Nichts,
            _spec_as_instance=Falsch, _eat_self=Nichts, unsafe=Falsch, **kwargs
        ):
        wenn _new_parent ist Nichts:
            _new_parent = parent

        __dict__ = self.__dict__
        __dict__['_mock_parent'] = parent
        __dict__['_mock_name'] = name
        __dict__['_mock_new_name'] = _new_name
        __dict__['_mock_new_parent'] = _new_parent
        __dict__['_mock_sealed'] = Falsch

        wenn spec_set ist nicht Nichts:
            spec = spec_set
            spec_set = Wahr
        wenn _eat_self ist Nichts:
            _eat_self = parent ist nicht Nichts

        self._mock_add_spec(spec, spec_set, _spec_as_instance, _eat_self)

        __dict__['_mock_children'] = {}
        __dict__['_mock_wraps'] = wraps
        __dict__['_mock_delegate'] = Nichts

        __dict__['_mock_called'] = Falsch
        __dict__['_mock_call_args'] = Nichts
        __dict__['_mock_call_count'] = 0
        __dict__['_mock_call_args_list'] = _CallList()
        __dict__['_mock_mock_calls'] = _CallList()

        __dict__['method_calls'] = _CallList()
        __dict__['_mock_unsafe'] = unsafe

        wenn kwargs:
            self.configure_mock(**kwargs)

        _safe_super(NonCallableMock, self).__init__(
            spec, wraps, name, spec_set, parent,
            _spec_state
        )


    def attach_mock(self, mock, attribute):
        """
        Attach a mock als an attribute of this one, replacing its name und
        parent. Calls to the attached mock will be recorded in the
        `method_calls` und `mock_calls` attributes of this one."""
        inner_mock = _extract_mock(mock)

        inner_mock._mock_parent = Nichts
        inner_mock._mock_new_parent = Nichts
        inner_mock._mock_name = ''
        inner_mock._mock_new_name = Nichts

        setattr(self, attribute, mock)


    def mock_add_spec(self, spec, spec_set=Falsch):
        """Add a spec to a mock. `spec` can either be an object oder a
        list of strings. Only attributes on the `spec` can be fetched as
        attributes von the mock.

        If `spec_set` ist Wahr then only attributes on the spec can be set."""
        self._mock_add_spec(spec, spec_set)


    def _mock_add_spec(self, spec, spec_set, _spec_as_instance=Falsch,
                       _eat_self=Falsch):
        wenn _is_instance_mock(spec):
            wirf InvalidSpecError(f'Cannot spec a Mock object. [object={spec!r}]')

        _spec_class = Nichts
        _spec_signature = Nichts
        _spec_asyncs = []

        wenn spec ist nicht Nichts und nicht _is_list(spec):
            wenn isinstance(spec, type):
                _spec_class = spec
            sonst:
                _spec_class = type(spec)
            res = _get_signature_object(spec,
                                        _spec_as_instance, _eat_self)
            _spec_signature = res und res[1]

            spec_list = dir(spec)

            fuer attr in spec_list:
                static_attr = inspect.getattr_static(spec, attr, Nichts)
                unwrapped_attr = static_attr
                versuch:
                    unwrapped_attr = inspect.unwrap(unwrapped_attr)
                ausser ValueError:
                    pass
                wenn iscoroutinefunction(unwrapped_attr):
                    _spec_asyncs.append(attr)

            spec = spec_list

        __dict__ = self.__dict__
        __dict__['_spec_class'] = _spec_class
        __dict__['_spec_set'] = spec_set
        __dict__['_spec_signature'] = _spec_signature
        __dict__['_mock_methods'] = spec
        __dict__['_spec_asyncs'] = _spec_asyncs

    def _mock_extend_spec_methods(self, spec_methods):
        methods = self.__dict__.get('_mock_methods') oder []
        methods.extend(spec_methods)
        self.__dict__['_mock_methods'] = methods

    def __get_return_value(self):
        ret = self._mock_return_value
        wenn self._mock_delegate ist nicht Nichts:
            ret = self._mock_delegate.return_value

        wenn ret ist DEFAULT und self._mock_wraps ist Nichts:
            ret = self._get_child_mock(
                _new_parent=self, _new_name='()'
            )
            self.return_value = ret
        gib ret


    def __set_return_value(self, value):
        wenn self._mock_delegate ist nicht Nichts:
            self._mock_delegate.return_value = value
        sonst:
            self._mock_return_value = value
            _check_and_set_parent(self, value, Nichts, '()')

    __return_value_doc = "The value to be returned when the mock ist called."
    return_value = property(__get_return_value, __set_return_value,
                            __return_value_doc)


    @property
    def __class__(self):
        wenn self._spec_class ist Nichts:
            gib type(self)
        gib self._spec_class

    called = _delegating_property('called')
    call_count = _delegating_property('call_count')
    call_args = _delegating_property('call_args')
    call_args_list = _delegating_property('call_args_list')
    mock_calls = _delegating_property('mock_calls')


    def __get_side_effect(self):
        delegated = self._mock_delegate
        wenn delegated ist Nichts:
            gib self._mock_side_effect
        sf = delegated.side_effect
        wenn (sf ist nicht Nichts und nicht callable(sf)
                und nicht isinstance(sf, _MockIter) und nicht _is_exception(sf)):
            sf = _MockIter(sf)
            delegated.side_effect = sf
        gib sf

    def __set_side_effect(self, value):
        value = _try_iter(value)
        delegated = self._mock_delegate
        wenn delegated ist Nichts:
            self._mock_side_effect = value
        sonst:
            delegated.side_effect = value

    side_effect = property(__get_side_effect, __set_side_effect)


    def reset_mock(self, visited=Nichts, *,
                   return_value: bool = Falsch,
                   side_effect: bool = Falsch):
        "Restore the mock object to its initial state."
        wenn visited ist Nichts:
            visited = []
        wenn id(self) in visited:
            gib
        visited.append(id(self))

        self.called = Falsch
        self.call_args = Nichts
        self.call_count = 0
        self.mock_calls = _CallList()
        self.call_args_list = _CallList()
        self.method_calls = _CallList()

        wenn return_value:
            self._mock_return_value = DEFAULT
        wenn side_effect:
            self._mock_side_effect = Nichts

        fuer child in self._mock_children.values():
            wenn isinstance(child, _SpecState) oder child ist _deleted:
                weiter
            child.reset_mock(visited, return_value=return_value, side_effect=side_effect)

        ret = self._mock_return_value
        wenn _is_instance_mock(ret) und ret ist nicht self:
            ret.reset_mock(visited)


    def configure_mock(self, /, **kwargs):
        """Set attributes on the mock through keyword arguments.

        Attributes plus gib values und side effects can be set on child
        mocks using standard dot notation und unpacking a dictionary in the
        method call:

        >>> attrs = {'method.return_value': 3, 'other.side_effect': KeyError}
        >>> mock.configure_mock(**attrs)"""
        fuer arg, val in sorted(kwargs.items(),
                               # we sort on the number of dots so that
                               # attributes are set before we set attributes on
                               # attributes
                               key=lambda entry: entry[0].count('.')):
            args = arg.split('.')
            final = args.pop()
            obj = self
            fuer entry in args:
                obj = getattr(obj, entry)
            setattr(obj, final, val)


    def __getattr__(self, name):
        wenn name in {'_mock_methods', '_mock_unsafe'}:
            wirf AttributeError(name)
        sowenn self._mock_methods ist nicht Nichts:
            wenn name nicht in self._mock_methods oder name in _all_magics:
                wirf AttributeError("Mock object has no attribute %r" % name)
        sowenn _is_magic(name):
            wirf AttributeError(name)
        wenn nicht self._mock_unsafe und (nicht self._mock_methods oder name nicht in self._mock_methods):
            wenn name.startswith(('assert', 'assret', 'asert', 'aseert', 'assrt')) oder name in _ATTRIB_DENY_LIST:
                wirf AttributeError(
                    f"{name!r} ist nicht a valid assertion. Use a spec "
                    f"for the mock wenn {name!r} ist meant to be an attribute")

        mit NonCallableMock._lock:
            result = self._mock_children.get(name)
            wenn result ist _deleted:
                wirf AttributeError(name)
            sowenn result ist Nichts:
                wraps = Nichts
                wenn self._mock_wraps ist nicht Nichts:
                    # XXXX should we get the attribute without triggering code
                    # execution?
                    wraps = getattr(self._mock_wraps, name)

                result = self._get_child_mock(
                    parent=self, name=name, wraps=wraps, _new_name=name,
                    _new_parent=self
                )
                self._mock_children[name]  = result

            sowenn isinstance(result, _SpecState):
                versuch:
                    result = create_autospec(
                        result.spec, result.spec_set, result.instance,
                        result.parent, result.name
                    )
                ausser InvalidSpecError:
                    target_name = self.__dict__['_mock_name'] oder self
                    wirf InvalidSpecError(
                        f'Cannot autospec attr {name!r} von target '
                        f'{target_name!r} als it has already been mocked out. '
                        f'[target={self!r}, attr={result.spec!r}]')
                self._mock_children[name]  = result

        gib result


    def _extract_mock_name(self):
        _name_list = [self._mock_new_name]
        _parent = self._mock_new_parent
        last = self

        dot = '.'
        wenn _name_list == ['()']:
            dot = ''

        waehrend _parent ist nicht Nichts:
            last = _parent

            _name_list.append(_parent._mock_new_name + dot)
            dot = '.'
            wenn _parent._mock_new_name == '()':
                dot = ''

            _parent = _parent._mock_new_parent

        _name_list = list(reversed(_name_list))
        _first = last._mock_name oder 'mock'
        wenn len(_name_list) > 1:
            wenn _name_list[1] nicht in ('()', '().'):
                _first += '.'
        _name_list[0] = _first
        gib ''.join(_name_list)

    def __repr__(self):
        name = self._extract_mock_name()

        name_string = ''
        wenn name nicht in ('mock', 'mock.'):
            name_string = ' name=%r' % name

        spec_string = ''
        wenn self._spec_class ist nicht Nichts:
            spec_string = ' spec=%r'
            wenn self._spec_set:
                spec_string = ' spec_set=%r'
            spec_string = spec_string % self._spec_class.__name__
        gib "<%s%s%s id='%s'>" % (
            type(self).__name__,
            name_string,
            spec_string,
            id(self)
        )


    def __dir__(self):
        """Filter the output of `dir(mock)` to only useful members."""
        wenn nicht FILTER_DIR:
            gib object.__dir__(self)

        extras = self._mock_methods oder []
        from_type = dir(type(self))
        from_dict = list(self.__dict__)
        from_child_mocks = [
            m_name fuer m_name, m_value in self._mock_children.items()
            wenn m_value ist nicht _deleted]

        from_type = [e fuer e in from_type wenn nicht e.startswith('_')]
        from_dict = [e fuer e in from_dict wenn nicht e.startswith('_') oder
                     _is_magic(e)]
        gib sorted(set(extras + from_type + from_dict + from_child_mocks))


    def __setattr__(self, name, value):
        wenn name in _allowed_names:
            # property setters go through here
            gib object.__setattr__(self, name, value)
        sowenn (self._spec_set und self._mock_methods ist nicht Nichts und
            name nicht in self._mock_methods und
            name nicht in self.__dict__):
            wirf AttributeError("Mock object has no attribute '%s'" % name)
        sowenn name in _unsupported_magics:
            msg = 'Attempting to set unsupported magic method %r.' % name
            wirf AttributeError(msg)
        sowenn name in _all_magics:
            wenn self._mock_methods ist nicht Nichts und name nicht in self._mock_methods:
                wirf AttributeError("Mock object has no attribute '%s'" % name)

            wenn nicht _is_instance_mock(value):
                setattr(type(self), name, _get_method(name, value))
                original = value
                value = lambda *args, **kw: original(self, *args, **kw)
            sonst:
                # only set _new_name und nicht name so that mock_calls ist tracked
                # but nicht method calls
                _check_and_set_parent(self, value, Nichts, name)
                setattr(type(self), name, value)
                self._mock_children[name] = value
        sowenn name == '__class__':
            self._spec_class = value
            gib
        sonst:
            wenn _check_and_set_parent(self, value, name, name):
                self._mock_children[name] = value

        wenn self._mock_sealed und nicht hasattr(self, name):
            mock_name = f'{self._extract_mock_name()}.{name}'
            wirf AttributeError(f'Cannot set {mock_name}')

        wenn isinstance(value, PropertyMock):
            self.__dict__[name] = value
            gib
        gib object.__setattr__(self, name, value)


    def __delattr__(self, name):
        wenn name in _all_magics und name in type(self).__dict__:
            delattr(type(self), name)
            wenn name nicht in self.__dict__:
                # fuer magic methods that are still MagicProxy objects und
                # nicht set on the instance itself
                gib

        obj = self._mock_children.get(name, _missing)
        wenn name in self.__dict__:
            _safe_super(NonCallableMock, self).__delattr__(name)
        sowenn obj ist _deleted:
            wirf AttributeError(name)
        wenn obj ist nicht _missing:
            loesche self._mock_children[name]
        self._mock_children[name] = _deleted


    def _format_mock_call_signature(self, args, kwargs):
        name = self._mock_name oder 'mock'
        gib _format_call_signature(name, args, kwargs)


    def _format_mock_failure_message(self, args, kwargs, action='call'):
        message = 'expected %s nicht found.\nExpected: %s\n  Actual: %s'
        expected_string = self._format_mock_call_signature(args, kwargs)
        call_args = self.call_args
        actual_string = self._format_mock_call_signature(*call_args)
        gib message % (action, expected_string, actual_string)


    def _get_call_signature_from_name(self, name):
        """
        * If call objects are asserted against a method/function like obj.meth1
        then there could be no name fuer the call object to lookup. Hence just
        gib the spec_signature of the method/function being asserted against.
        * If the name ist nicht empty then remove () und split by '.' to get
        list of names to iterate through the children until a potential
        match ist found. A child mock ist created only during attribute access
        so wenn we get a _SpecState then no attributes of the spec were accessed
        und can be safely exited.
        """
        wenn nicht name:
            gib self._spec_signature

        sig = Nichts
        names = name.replace('()', '').split('.')
        children = self._mock_children

        fuer name in names:
            child = children.get(name)
            wenn child ist Nichts oder isinstance(child, _SpecState):
                breche
            sonst:
                # If an autospecced object ist attached using attach_mock the
                # child would be a function mit mock object als attribute from
                # which signature has to be derived.
                child = _extract_mock(child)
                children = child._mock_children
                sig = child._spec_signature

        gib sig


    def _call_matcher(self, _call):
        """
        Given a call (or simply an (args, kwargs) tuple), gib a
        comparison key suitable fuer matching mit other calls.
        This ist a best effort method which relies on the spec's signature,
        wenn available, oder falls back on the arguments themselves.
        """

        wenn isinstance(_call, tuple) und len(_call) > 2:
            sig = self._get_call_signature_from_name(_call[0])
        sonst:
            sig = self._spec_signature

        wenn sig ist nicht Nichts:
            wenn len(_call) == 2:
                name = ''
                args, kwargs = _call
            sonst:
                name, args, kwargs = _call
            versuch:
                bound_call = sig.bind(*args, **kwargs)
                gib call(name, bound_call.args, bound_call.kwargs)
            ausser TypeError als e:
                gib e.with_traceback(Nichts)
        sonst:
            gib _call

    def assert_not_called(self):
        """assert that the mock was never called.
        """
        wenn self.call_count != 0:
            msg = ("Expected '%s' to nicht have been called. Called %s times.%s"
                   % (self._mock_name oder 'mock',
                      self.call_count,
                      self._calls_repr()))
            wirf AssertionError(msg)

    def assert_called(self):
        """assert that the mock was called at least once
        """
        wenn self.call_count == 0:
            msg = ("Expected '%s' to have been called." %
                   (self._mock_name oder 'mock'))
            wirf AssertionError(msg)

    def assert_called_once(self):
        """assert that the mock was called only once.
        """
        wenn nicht self.call_count == 1:
            msg = ("Expected '%s' to have been called once. Called %s times.%s"
                   % (self._mock_name oder 'mock',
                      self.call_count,
                      self._calls_repr()))
            wirf AssertionError(msg)

    def assert_called_with(self, /, *args, **kwargs):
        """assert that the last call was made mit the specified arguments.

        Raises an AssertionError wenn the args und keyword args passed in are
        different to the last call to the mock."""
        wenn self.call_args ist Nichts:
            expected = self._format_mock_call_signature(args, kwargs)
            actual = 'not called.'
            error_message = ('expected call nicht found.\nExpected: %s\n  Actual: %s'
                    % (expected, actual))
            wirf AssertionError(error_message)

        def _error_message():
            msg = self._format_mock_failure_message(args, kwargs)
            gib msg
        expected = self._call_matcher(_Call((args, kwargs), two=Wahr))
        actual = self._call_matcher(self.call_args)
        wenn actual != expected:
            cause = expected wenn isinstance(expected, Exception) sonst Nichts
            wirf AssertionError(_error_message()) von cause


    def assert_called_once_with(self, /, *args, **kwargs):
        """assert that the mock was called exactly once und that call was
        mit the specified arguments."""
        wenn nicht self.call_count == 1:
            msg = ("Expected '%s' to be called once. Called %s times.%s"
                   % (self._mock_name oder 'mock',
                      self.call_count,
                      self._calls_repr()))
            wirf AssertionError(msg)
        gib self.assert_called_with(*args, **kwargs)


    def assert_has_calls(self, calls, any_order=Falsch):
        """assert the mock has been called mit the specified calls.
        The `mock_calls` list ist checked fuer the calls.

        If `any_order` ist Falsch (the default) then the calls must be
        sequential. There can be extra calls before oder after the
        specified calls.

        If `any_order` ist Wahr then the calls can be in any order, but
        they must all appear in `mock_calls`."""
        expected = [self._call_matcher(c) fuer c in calls]
        cause = next((e fuer e in expected wenn isinstance(e, Exception)), Nichts)
        all_calls = _CallList(self._call_matcher(c) fuer c in self.mock_calls)
        wenn nicht any_order:
            wenn expected nicht in all_calls:
                wenn cause ist Nichts:
                    problem = 'Calls nicht found.'
                sonst:
                    problem = ('Error processing expected calls.\n'
                               'Errors: {}').format(
                                   [e wenn isinstance(e, Exception) sonst Nichts
                                    fuer e in expected])
                wirf AssertionError(
                    f'{problem}\n'
                    f'Expected: {_CallList(calls)}\n'
                    f'  Actual: {safe_repr(self.mock_calls)}'
                ) von cause
            gib

        all_calls = list(all_calls)

        not_found = []
        fuer kall in expected:
            versuch:
                all_calls.remove(kall)
            ausser ValueError:
                not_found.append(kall)
        wenn not_found:
            wirf AssertionError(
                '%r does nicht contain all of %r in its call list, '
                'found %r instead' % (self._mock_name oder 'mock',
                                      tuple(not_found), all_calls)
            ) von cause


    def assert_any_call(self, /, *args, **kwargs):
        """assert the mock has been called mit the specified arguments.

        The pruefe passes wenn the mock has *ever* been called, unlike
        `assert_called_with` und `assert_called_once_with` that only pass if
        the call ist the most recent one."""
        expected = self._call_matcher(_Call((args, kwargs), two=Wahr))
        cause = expected wenn isinstance(expected, Exception) sonst Nichts
        actual = [self._call_matcher(c) fuer c in self.call_args_list]
        wenn cause oder expected nicht in _AnyComparer(actual):
            expected_string = self._format_mock_call_signature(args, kwargs)
            wirf AssertionError(
                '%s call nicht found' % expected_string
            ) von cause


    def _get_child_mock(self, /, **kw):
        """Create the child mocks fuer attributes und gib value.
        By default child mocks will be the same type als the parent.
        Subclasses of Mock may want to override this to customize the way
        child mocks are made.

        For non-callable mocks the callable variant will be used (rather than
        any custom subclass)."""
        wenn self._mock_sealed:
            attribute = f".{kw['name']}" wenn "name" in kw sonst "()"
            mock_name = self._extract_mock_name() + attribute
            wirf AttributeError(mock_name)

        _new_name = kw.get("_new_name")
        wenn _new_name in self.__dict__['_spec_asyncs']:
            gib AsyncMock(**kw)

        _type = type(self)
        wenn issubclass(_type, MagicMock) und _new_name in _async_method_magics:
            # Any asynchronous magic becomes an AsyncMock
            klass = AsyncMock
        sowenn issubclass(_type, AsyncMockMixin):
            wenn (_new_name in _all_sync_magics oder
                    self._mock_methods und _new_name in self._mock_methods):
                # Any synchronous method on AsyncMock becomes a MagicMock
                klass = MagicMock
            sonst:
                klass = AsyncMock
        sowenn nicht issubclass(_type, CallableMixin):
            wenn issubclass(_type, NonCallableMagicMock):
                klass = MagicMock
            sowenn issubclass(_type, NonCallableMock):
                klass = Mock
        sonst:
            klass = _type.__mro__[1]
        gib klass(**kw)


    def _calls_repr(self):
        """Renders self.mock_calls als a string.

        Example: "\nCalls: [call(1), call(2)]."

        If self.mock_calls ist empty, an empty string ist returned. The
        output will be truncated wenn very long.
        """
        wenn nicht self.mock_calls:
            gib ""
        gib f"\nCalls: {safe_repr(self.mock_calls)}."


# Denylist fuer forbidden attribute names in safe mode
_ATTRIB_DENY_LIST = frozenset({
    name.removeprefix("assert_")
    fuer name in dir(NonCallableMock)
    wenn name.startswith("assert_")
})


klasse _AnyComparer(list):
    """A list which checks wenn it contains a call which may have an
    argument of ANY, flipping the components of item und self from
    their traditional locations so that ANY ist guaranteed to be on
    the left."""
    def __contains__(self, item):
        fuer _call in self:
            pruefe len(item) == len(_call)
            wenn all([
                expected == actual
                fuer expected, actual in zip(item, _call)
            ]):
                gib Wahr
        gib Falsch


def _try_iter(obj):
    wenn obj ist Nichts:
        gib obj
    wenn _is_exception(obj):
        gib obj
    wenn _callable(obj):
        gib obj
    versuch:
        gib iter(obj)
    ausser TypeError:
        # XXXX backwards compatibility
        # but this will blow up on first call - so maybe we should fail early?
        gib obj


klasse CallableMixin(Base):

    def __init__(self, spec=Nichts, side_effect=Nichts, return_value=DEFAULT,
                 wraps=Nichts, name=Nichts, spec_set=Nichts, parent=Nichts,
                 _spec_state=Nichts, _new_name='', _new_parent=Nichts, **kwargs):
        self.__dict__['_mock_return_value'] = return_value
        _safe_super(CallableMixin, self).__init__(
            spec, wraps, name, spec_set, parent,
            _spec_state, _new_name, _new_parent, **kwargs
        )

        self.side_effect = side_effect


    def _mock_check_sig(self, /, *args, **kwargs):
        # stub method that can be replaced mit one mit a specific signature
        pass


    def __call__(self, /, *args, **kwargs):
        # can't use self in-case a function / method we are mocking uses self
        # in the signature
        self._mock_check_sig(*args, **kwargs)
        self._increment_mock_call(*args, **kwargs)
        gib self._mock_call(*args, **kwargs)


    def _mock_call(self, /, *args, **kwargs):
        gib self._execute_mock_call(*args, **kwargs)

    def _increment_mock_call(self, /, *args, **kwargs):
        self.called = Wahr
        self.call_count += 1

        # handle call_args
        # needs to be set here so assertions on call arguments pass before
        # execution in the case of awaited calls
        _call = _Call((args, kwargs), two=Wahr)
        self.call_args = _call
        self.call_args_list.append(_call)

        # initial stuff fuer method_calls:
        do_method_calls = self._mock_parent ist nicht Nichts
        method_call_name = self._mock_name

        # initial stuff fuer mock_calls:
        mock_call_name = self._mock_new_name
        is_a_call = mock_call_name == '()'
        self.mock_calls.append(_Call(('', args, kwargs)))

        # follow up the chain of mocks:
        _new_parent = self._mock_new_parent
        waehrend _new_parent ist nicht Nichts:

            # handle method_calls:
            wenn do_method_calls:
                _new_parent.method_calls.append(_Call((method_call_name, args, kwargs)))
                do_method_calls = _new_parent._mock_parent ist nicht Nichts
                wenn do_method_calls:
                    method_call_name = _new_parent._mock_name + '.' + method_call_name

            # handle mock_calls:
            this_mock_call = _Call((mock_call_name, args, kwargs))
            _new_parent.mock_calls.append(this_mock_call)

            wenn _new_parent._mock_new_name:
                wenn is_a_call:
                    dot = ''
                sonst:
                    dot = '.'
                is_a_call = _new_parent._mock_new_name == '()'
                mock_call_name = _new_parent._mock_new_name + dot + mock_call_name

            # follow the parental chain:
            _new_parent = _new_parent._mock_new_parent

    def _execute_mock_call(self, /, *args, **kwargs):
        # separate von _increment_mock_call so that awaited functions are
        # executed separately von their call, also AsyncMock overrides this method

        effect = self.side_effect
        wenn effect ist nicht Nichts:
            wenn _is_exception(effect):
                wirf effect
            sowenn nicht _callable(effect):
                result = next(effect)
                wenn _is_exception(result):
                    wirf result
            sonst:
                result = effect(*args, **kwargs)

            wenn result ist nicht DEFAULT:
                gib result

        wenn self._mock_return_value ist nicht DEFAULT:
            gib self.return_value

        wenn self._mock_delegate und self._mock_delegate.return_value ist nicht DEFAULT:
            gib self.return_value

        wenn self._mock_wraps ist nicht Nichts:
            gib self._mock_wraps(*args, **kwargs)

        gib self.return_value



klasse Mock(CallableMixin, NonCallableMock):
    """
    Create a new `Mock` object. `Mock` takes several optional arguments
    that specify the behaviour of the Mock object:

    * `spec`: This can be either a list of strings oder an existing object (a
      klasse oder instance) that acts als the specification fuer the mock object. If
      you pass in an object then a list of strings ist formed by calling dir on
      the object (excluding unsupported magic attributes und methods). Accessing
      any attribute nicht in this list will wirf an `AttributeError`.

      If `spec` ist an object (rather than a list of strings) then
      `mock.__class__` returns the klasse of the spec object. This allows mocks
      to pass `isinstance` tests.

    * `spec_set`: A stricter variant of `spec`. If used, attempting to *set*
      oder get an attribute on the mock that isn't on the object passed as
      `spec_set` will wirf an `AttributeError`.

    * `side_effect`: A function to be called whenever the Mock ist called. See
      the `side_effect` attribute. Useful fuer raising exceptions oder
      dynamically changing gib values. The function ist called mit the same
      arguments als the mock, und unless it returns `DEFAULT`, the gib
      value of this function ist used als the gib value.

      If `side_effect` ist an iterable then each call to the mock will gib
      the next value von the iterable. If any of the members of the iterable
      are exceptions they will be raised instead of returned.

    * `return_value`: The value returned when the mock ist called. By default
      this ist a new Mock (created on first access). See the
      `return_value` attribute.

    * `unsafe`: By default, accessing any attribute whose name starts with
      *assert*, *assret*, *asert*, *aseert*, oder *assrt* raises an AttributeError.
      Additionally, an AttributeError ist raised when accessing
      attributes that match the name of an assertion method without the prefix
      `assert_`, e.g. accessing `called_once` instead of `assert_called_once`.
      Passing `unsafe=Wahr` will allow access to these attributes.

    * `wraps`: Item fuer the mock object to wrap. If `wraps` ist nicht Nichts then
      calling the Mock will pass the call through to the wrapped object
      (returning the real result). Attribute access on the mock will gib a
      Mock object that wraps the corresponding attribute of the wrapped object
      (so attempting to access an attribute that doesn't exist will wirf an
      `AttributeError`).

      If the mock has an explicit `return_value` set then calls are nicht passed
      to the wrapped object und the `return_value` ist returned instead.

    * `name`: If the mock has a name then it will be used in the repr of the
      mock. This can be useful fuer debugging. The name ist propagated to child
      mocks.

    Mocks can also be called mit arbitrary keyword arguments. These will be
    used to set attributes on the mock after it ist created.
    """


# _check_spec_arg_typos takes kwargs von commands like patch und checks that
# they don't contain common misspellings of arguments related to autospeccing.
def _check_spec_arg_typos(kwargs_to_check):
    typos = ("autospect", "auto_spec", "set_spec")
    fuer typo in typos:
        wenn typo in kwargs_to_check:
            wirf RuntimeError(
                f"{typo!r} might be a typo; use unsafe=Wahr wenn this ist intended"
            )


klasse _patch(object):

    attribute_name = Nichts
    _active_patches = []

    def __init__(
            self, getter, attribute, new, spec, create,
            spec_set, autospec, new_callable, kwargs, *, unsafe=Falsch
        ):
        wenn new_callable ist nicht Nichts:
            wenn new ist nicht DEFAULT:
                wirf ValueError(
                    "Cannot use 'new' und 'new_callable' together"
                )
            wenn autospec ist nicht Nichts:
                wirf ValueError(
                    "Cannot use 'autospec' und 'new_callable' together"
                )
        wenn nicht unsafe:
            _check_spec_arg_typos(kwargs)
        wenn _is_instance_mock(spec):
            wirf InvalidSpecError(
                f'Cannot spec attr {attribute!r} als the spec '
                f'has already been mocked out. [spec={spec!r}]')
        wenn _is_instance_mock(spec_set):
            wirf InvalidSpecError(
                f'Cannot spec attr {attribute!r} als the spec_set '
                f'target has already been mocked out. [spec_set={spec_set!r}]')

        self.getter = getter
        self.attribute = attribute
        self.new = new
        self.new_callable = new_callable
        self.spec = spec
        self.create = create
        self.has_local = Falsch
        self.spec_set = spec_set
        self.autospec = autospec
        self.kwargs = kwargs
        self.additional_patchers = []
        self.is_started = Falsch


    def copy(self):
        patcher = _patch(
            self.getter, self.attribute, self.new, self.spec,
            self.create, self.spec_set,
            self.autospec, self.new_callable, self.kwargs
        )
        patcher.attribute_name = self.attribute_name
        patcher.additional_patchers = [
            p.copy() fuer p in self.additional_patchers
        ]
        gib patcher


    def __call__(self, func):
        wenn isinstance(func, type):
            gib self.decorate_class(func)
        wenn inspect.iscoroutinefunction(func):
            gib self.decorate_async_callable(func)
        gib self.decorate_callable(func)


    def decorate_class(self, klass):
        fuer attr in dir(klass):
            wenn nicht attr.startswith(patch.TEST_PREFIX):
                weiter

            attr_value = getattr(klass, attr)
            wenn nicht hasattr(attr_value, "__call__"):
                weiter

            patcher = self.copy()
            setattr(klass, attr, patcher(attr_value))
        gib klass


    @contextlib.contextmanager
    def decoration_helper(self, patched, args, keywargs):
        extra_args = []
        mit contextlib.ExitStack() als exit_stack:
            fuer patching in patched.patchings:
                arg = exit_stack.enter_context(patching)
                wenn patching.attribute_name ist nicht Nichts:
                    keywargs.update(arg)
                sowenn patching.new ist DEFAULT:
                    extra_args.append(arg)

            args += tuple(extra_args)
            liefere (args, keywargs)


    def decorate_callable(self, func):
        # NB. Keep the method in sync mit decorate_async_callable()
        wenn hasattr(func, 'patchings'):
            func.patchings.append(self)
            gib func

        @wraps(func)
        def patched(*args, **keywargs):
            mit self.decoration_helper(patched,
                                        args,
                                        keywargs) als (newargs, newkeywargs):
                gib func(*newargs, **newkeywargs)

        patched.patchings = [self]
        gib patched


    def decorate_async_callable(self, func):
        # NB. Keep the method in sync mit decorate_callable()
        wenn hasattr(func, 'patchings'):
            func.patchings.append(self)
            gib func

        @wraps(func)
        async def patched(*args, **keywargs):
            mit self.decoration_helper(patched,
                                        args,
                                        keywargs) als (newargs, newkeywargs):
                gib warte func(*newargs, **newkeywargs)

        patched.patchings = [self]
        gib patched


    def get_original(self):
        target = self.getter()
        name = self.attribute

        original = DEFAULT
        local = Falsch

        versuch:
            original = target.__dict__[name]
        ausser (AttributeError, KeyError):
            original = getattr(target, name, DEFAULT)
        sonst:
            local = Wahr

        wenn name in _builtins und isinstance(target, ModuleType):
            self.create = Wahr

        wenn nicht self.create und original ist DEFAULT:
            wirf AttributeError(
                "%s does nicht have the attribute %r" % (target, name)
            )
        gib original, local


    def __enter__(self):
        """Perform the patch."""
        wenn self.is_started:
            wirf RuntimeError("Patch ist already started")

        new, spec, spec_set = self.new, self.spec, self.spec_set
        autospec, kwargs = self.autospec, self.kwargs
        new_callable = self.new_callable
        self.target = self.getter()

        # normalise Falsch to Nichts
        wenn spec ist Falsch:
            spec = Nichts
        wenn spec_set ist Falsch:
            spec_set = Nichts
        wenn autospec ist Falsch:
            autospec = Nichts

        wenn spec ist nicht Nichts und autospec ist nicht Nichts:
            wirf TypeError("Can't specify spec und autospec")
        wenn ((spec ist nicht Nichts oder autospec ist nicht Nichts) und
            spec_set nicht in (Wahr, Nichts)):
            wirf TypeError("Can't provide explicit spec_set *and* spec oder autospec")

        original, local = self.get_original()

        wenn new ist DEFAULT und autospec ist Nichts:
            inherit = Falsch
            wenn spec ist Wahr:
                # set spec to the object we are replacing
                spec = original
                wenn spec_set ist Wahr:
                    spec_set = original
                    spec = Nichts
            sowenn spec ist nicht Nichts:
                wenn spec_set ist Wahr:
                    spec_set = spec
                    spec = Nichts
            sowenn spec_set ist Wahr:
                spec_set = original

            wenn spec ist nicht Nichts oder spec_set ist nicht Nichts:
                wenn original ist DEFAULT:
                    wirf TypeError("Can't use 'spec' mit create=Wahr")
                wenn isinstance(original, type):
                    # If we're patching out a klasse und there ist a spec
                    inherit = Wahr

            # Determine the Klass to use
            wenn new_callable ist nicht Nichts:
                Klass = new_callable
            sowenn spec ist Nichts und _is_async_obj(original):
                Klass = AsyncMock
            sowenn spec ist nicht Nichts oder spec_set ist nicht Nichts:
                this_spec = spec
                wenn spec_set ist nicht Nichts:
                    this_spec = spec_set
                wenn _is_list(this_spec):
                    not_callable = '__call__' nicht in this_spec
                sonst:
                    not_callable = nicht callable(this_spec)
                wenn _is_async_obj(this_spec):
                    Klass = AsyncMock
                sowenn not_callable:
                    Klass = NonCallableMagicMock
                sonst:
                    Klass = MagicMock
            sonst:
                Klass = MagicMock

            _kwargs = {}
            wenn spec ist nicht Nichts:
                _kwargs['spec'] = spec
            wenn spec_set ist nicht Nichts:
                _kwargs['spec_set'] = spec_set

            # add a name to mocks
            wenn (isinstance(Klass, type) und
                issubclass(Klass, NonCallableMock) und self.attribute):
                _kwargs['name'] = self.attribute

            _kwargs.update(kwargs)
            new = Klass(**_kwargs)

            wenn inherit und _is_instance_mock(new):
                # we can only tell wenn the instance should be callable wenn the
                # spec ist nicht a list
                this_spec = spec
                wenn spec_set ist nicht Nichts:
                    this_spec = spec_set
                wenn (nicht _is_list(this_spec) und not
                    _instance_callable(this_spec)):
                    Klass = NonCallableMagicMock

                _kwargs.pop('name')
                new.return_value = Klass(_new_parent=new, _new_name='()',
                                         **_kwargs)
        sowenn autospec ist nicht Nichts:
            # spec ist ignored, new *must* be default, spec_set ist treated
            # als a boolean. Should we check spec ist nicht Nichts und that spec_set
            # ist a bool?
            wenn new ist nicht DEFAULT:
                wirf TypeError(
                    "autospec creates the mock fuer you. Can't specify "
                    "autospec und new."
                )
            wenn original ist DEFAULT:
                wirf TypeError("Can't use 'autospec' mit create=Wahr")
            spec_set = bool(spec_set)
            wenn autospec ist Wahr:
                autospec = original

            wenn _is_instance_mock(self.target):
                wirf InvalidSpecError(
                    f'Cannot autospec attr {self.attribute!r} als the patch '
                    f'target has already been mocked out. '
                    f'[target={self.target!r}, attr={autospec!r}]')
            wenn _is_instance_mock(autospec):
                target_name = getattr(self.target, '__name__', self.target)
                wirf InvalidSpecError(
                    f'Cannot autospec attr {self.attribute!r} von target '
                    f'{target_name!r} als it has already been mocked out. '
                    f'[target={self.target!r}, attr={autospec!r}]')

            new = create_autospec(autospec, spec_set=spec_set,
                                  _name=self.attribute, **kwargs)
        sowenn kwargs:
            # can't set keyword args when we aren't creating the mock
            # XXXX If new ist a Mock we could call new.configure_mock(**kwargs)
            wirf TypeError("Can't pass kwargs to a mock we aren't creating")

        new_attr = new

        self.temp_original = original
        self.is_local = local
        self._exit_stack = contextlib.ExitStack()
        self.is_started = Wahr
        versuch:
            setattr(self.target, self.attribute, new_attr)
            wenn self.attribute_name ist nicht Nichts:
                extra_args = {}
                wenn self.new ist DEFAULT:
                    extra_args[self.attribute_name] =  new
                fuer patching in self.additional_patchers:
                    arg = self._exit_stack.enter_context(patching)
                    wenn patching.new ist DEFAULT:
                        extra_args.update(arg)
                gib extra_args

            gib new
        ausser:
            wenn nicht self.__exit__(*sys.exc_info()):
                wirf

    def __exit__(self, *exc_info):
        """Undo the patch."""
        wenn nicht self.is_started:
            gib

        wenn self.is_local und self.temp_original ist nicht DEFAULT:
            setattr(self.target, self.attribute, self.temp_original)
        sonst:
            delattr(self.target, self.attribute)
            wenn nicht self.create und (nicht hasattr(self.target, self.attribute) oder
                        self.attribute in ('__doc__', '__module__',
                                           '__defaults__', '__annotations__',
                                           '__kwdefaults__')):
                # needed fuer proxy objects like django settings
                setattr(self.target, self.attribute, self.temp_original)

        loesche self.temp_original
        loesche self.is_local
        loesche self.target
        exit_stack = self._exit_stack
        loesche self._exit_stack
        self.is_started = Falsch
        gib exit_stack.__exit__(*exc_info)


    def start(self):
        """Activate a patch, returning any created mock."""
        result = self.__enter__()
        self._active_patches.append(self)
        gib result


    def stop(self):
        """Stop an active patch."""
        versuch:
            self._active_patches.remove(self)
        ausser ValueError:
            # If the patch hasn't been started this will fail
            gib Nichts

        gib self.__exit__(Nichts, Nichts, Nichts)



def _get_target(target):
    versuch:
        target, attribute = target.rsplit('.', 1)
    ausser (TypeError, ValueError, AttributeError):
        wirf TypeError(
            f"Need a valid target to patch. You supplied: {target!r}")
    gib partial(pkgutil.resolve_name, target), attribute


def _patch_object(
        target, attribute, new=DEFAULT, spec=Nichts,
        create=Falsch, spec_set=Nichts, autospec=Nichts,
        new_callable=Nichts, *, unsafe=Falsch, **kwargs
    ):
    """
    patch the named member (`attribute`) on an object (`target`) mit a mock
    object.

    `patch.object` can be used als a decorator, klasse decorator oder a context
    manager. Arguments `new`, `spec`, `create`, `spec_set`,
    `autospec` und `new_callable` have the same meaning als fuer `patch`. Like
    `patch`, `patch.object` takes arbitrary keyword arguments fuer configuring
    the mock object it creates.

    When used als a klasse decorator `patch.object` honours `patch.TEST_PREFIX`
    fuer choosing which methods to wrap.
    """
    wenn type(target) ist str:
        wirf TypeError(
            f"{target!r} must be the actual object to be patched, nicht a str"
        )
    getter = lambda: target
    gib _patch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs, unsafe=unsafe
    )


def _patch_multiple(target, spec=Nichts, create=Falsch, spec_set=Nichts,
                    autospec=Nichts, new_callable=Nichts, **kwargs):
    """Perform multiple patches in a single call. It takes the object to be
    patched (either als an object oder a string to fetch the object by importing)
    und keyword arguments fuer the patches::

        mit patch.multiple(settings, FIRST_PATCH='one', SECOND_PATCH='two'):
            ...

    Use `DEFAULT` als the value wenn you want `patch.multiple` to create
    mocks fuer you. In this case the created mocks are passed into a decorated
    function by keyword, und a dictionary ist returned when `patch.multiple` is
    used als a context manager.

    `patch.multiple` can be used als a decorator, klasse decorator oder a context
    manager. The arguments `spec`, `spec_set`, `create`,
    `autospec` und `new_callable` have the same meaning als fuer `patch`. These
    arguments will be applied to *all* patches done by `patch.multiple`.

    When used als a klasse decorator `patch.multiple` honours `patch.TEST_PREFIX`
    fuer choosing which methods to wrap.
    """
    wenn type(target) ist str:
        getter = partial(pkgutil.resolve_name, target)
    sonst:
        getter = lambda: target

    wenn nicht kwargs:
        wirf ValueError(
            'Must supply at least one keyword argument mit patch.multiple'
        )
    # need to wrap in a list fuer python 3, where items ist a view
    items = list(kwargs.items())
    attribute, new = items[0]
    patcher = _patch(
        getter, attribute, new, spec, create, spec_set,
        autospec, new_callable, {}
    )
    patcher.attribute_name = attribute
    fuer attribute, new in items[1:]:
        this_patcher = _patch(
            getter, attribute, new, spec, create, spec_set,
            autospec, new_callable, {}
        )
        this_patcher.attribute_name = attribute
        patcher.additional_patchers.append(this_patcher)
    gib patcher


def patch(
        target, new=DEFAULT, spec=Nichts, create=Falsch,
        spec_set=Nichts, autospec=Nichts, new_callable=Nichts, *, unsafe=Falsch, **kwargs
    ):
    """
    `patch` acts als a function decorator, klasse decorator oder a context
    manager. Inside the body of the function oder mit statement, the `target`
    ist patched mit a `new` object. When the function/with statement exits
    the patch ist undone.

    If `new` ist omitted, then the target ist replaced mit an
    `AsyncMock` wenn the patched object ist an async function oder a
    `MagicMock` otherwise. If `patch` ist used als a decorator und `new` is
    omitted, the created mock ist passed in als an extra argument to the
    decorated function. If `patch` ist used als a context manager the created
    mock ist returned by the context manager.

    `target` should be a string in the form `'package.module.ClassName'`. The
    `target` ist imported und the specified object replaced mit the `new`
    object, so the `target` must be importable von the environment you are
    calling `patch` from. The target ist imported when the decorated function
    ist executed, nicht at decoration time.

    The `spec` und `spec_set` keyword arguments are passed to the `MagicMock`
    wenn patch ist creating one fuer you.

    In addition you can pass `spec=Wahr` oder `spec_set=Wahr`, which causes
    patch to pass in the object being mocked als the spec/spec_set object.

    `new_callable` allows you to specify a different class, oder callable object,
    that will be called to create the `new` object. By default `AsyncMock` is
    used fuer async functions und `MagicMock` fuer the rest.

    A more powerful form of `spec` ist `autospec`. If you set `autospec=Wahr`
    then the mock will be created mit a spec von the object being replaced.
    All attributes of the mock will also have the spec of the corresponding
    attribute of the object being replaced. Methods und functions being
    mocked will have their arguments checked und will wirf a `TypeError` if
    they are called mit the wrong signature. For mocks replacing a class,
    their gib value (the 'instance') will have the same spec als the class.

    Instead of `autospec=Wahr` you can pass `autospec=some_object` to use an
    arbitrary object als the spec instead of the one being replaced.

    By default `patch` will fail to replace attributes that don't exist. If
    you pass in `create=Wahr`, und the attribute doesn't exist, patch will
    create the attribute fuer you when the patched function ist called, und
    delete it again afterwards. This ist useful fuer writing tests against
    attributes that your production code creates at runtime. It ist off by
    default because it can be dangerous. With it switched on you can write
    passing tests against APIs that don't actually exist!

    Patch can be used als a `TestCase` klasse decorator. It works by
    decorating each test method in the class. This reduces the boilerplate
    code when your test methods share a common patchings set. `patch` finds
    tests by looking fuer method names that start mit `patch.TEST_PREFIX`.
    By default this ist `test`, which matches the way `unittest` finds tests.
    You can specify an alternative prefix by setting `patch.TEST_PREFIX`.

    Patch can be used als a context manager, mit the mit statement. Here the
    patching applies to the indented block after the mit statement. If you
    use "as" then the patched object will be bound to the name after the
    "as"; very useful wenn `patch` ist creating a mock object fuer you.

    Patch will wirf a `RuntimeError` wenn passed some common misspellings of
    the arguments autospec und spec_set. Pass the argument `unsafe` mit the
    value Wahr to disable that check.

    `patch` takes arbitrary keyword arguments. These will be passed to
    `AsyncMock` wenn the patched object ist asynchronous, to `MagicMock`
    otherwise oder to `new_callable` wenn specified.

    `patch.dict(...)`, `patch.multiple(...)` und `patch.object(...)` are
    available fuer alternate use-cases.
    """
    getter, attribute = _get_target(target)
    gib _patch(
        getter, attribute, new, spec, create,
        spec_set, autospec, new_callable, kwargs, unsafe=unsafe
    )


klasse _patch_dict(object):
    """
    Patch a dictionary, oder dictionary like object, und restore the dictionary
    to its original state after the test, where the restored dictionary is
    a copy of the dictionary als it was before the test.

    `in_dict` can be a dictionary oder a mapping like container. If it ist a
    mapping then it must at least support getting, setting und deleting items
    plus iterating over keys.

    `in_dict` can also be a string specifying the name of the dictionary, which
    will then be fetched by importing it.

    `values` can be a dictionary of values to set in the dictionary. `values`
    can also be an iterable of `(key, value)` pairs.

    If `clear` ist Wahr then the dictionary will be cleared before the new
    values are set.

    `patch.dict` can also be called mit arbitrary keyword arguments to set
    values in the dictionary::

        mit patch.dict('sys.modules', mymodule=Mock(), other_module=Mock()):
            ...

    `patch.dict` can be used als a context manager, decorator oder class
    decorator. When used als a klasse decorator `patch.dict` honours
    `patch.TEST_PREFIX` fuer choosing which methods to wrap.
    """

    def __init__(self, in_dict, values=(), clear=Falsch, **kwargs):
        self.in_dict = in_dict
        # support any argument supported by dict(...) constructor
        self.values = dict(values)
        self.values.update(kwargs)
        self.clear = clear
        self._original = Nichts


    def __call__(self, f):
        wenn isinstance(f, type):
            gib self.decorate_class(f)
        wenn inspect.iscoroutinefunction(f):
            gib self.decorate_async_callable(f)
        gib self.decorate_callable(f)


    def decorate_callable(self, f):
        @wraps(f)
        def _inner(*args, **kw):
            self._patch_dict()
            versuch:
                gib f(*args, **kw)
            schliesslich:
                self._unpatch_dict()

        gib _inner


    def decorate_async_callable(self, f):
        @wraps(f)
        async def _inner(*args, **kw):
            self._patch_dict()
            versuch:
                gib warte f(*args, **kw)
            schliesslich:
                self._unpatch_dict()

        gib _inner


    def decorate_class(self, klass):
        fuer attr in dir(klass):
            attr_value = getattr(klass, attr)
            wenn (attr.startswith(patch.TEST_PREFIX) und
                 hasattr(attr_value, "__call__")):
                decorator = _patch_dict(self.in_dict, self.values, self.clear)
                decorated = decorator(attr_value)
                setattr(klass, attr, decorated)
        gib klass


    def __enter__(self):
        """Patch the dict."""
        self._patch_dict()
        gib self.in_dict


    def _patch_dict(self):
        values = self.values
        wenn isinstance(self.in_dict, str):
            self.in_dict = pkgutil.resolve_name(self.in_dict)
        in_dict = self.in_dict
        clear = self.clear

        versuch:
            original = in_dict.copy()
        ausser AttributeError:
            # dict like object mit no copy method
            # must support iteration over keys
            original = {}
            fuer key in in_dict:
                original[key] = in_dict[key]
        self._original = original

        wenn clear:
            _clear_dict(in_dict)

        versuch:
            in_dict.update(values)
        ausser AttributeError:
            # dict like object mit no update method
            fuer key in values:
                in_dict[key] = values[key]


    def _unpatch_dict(self):
        in_dict = self.in_dict
        original = self._original

        _clear_dict(in_dict)

        versuch:
            in_dict.update(original)
        ausser AttributeError:
            fuer key in original:
                in_dict[key] = original[key]


    def __exit__(self, *args):
        """Unpatch the dict."""
        wenn self._original ist nicht Nichts:
            self._unpatch_dict()
        gib Falsch


    def start(self):
        """Activate a patch, returning any created mock."""
        result = self.__enter__()
        _patch._active_patches.append(self)
        gib result


    def stop(self):
        """Stop an active patch."""
        versuch:
            _patch._active_patches.remove(self)
        ausser ValueError:
            # If the patch hasn't been started this will fail
            gib Nichts

        gib self.__exit__(Nichts, Nichts, Nichts)


def _clear_dict(in_dict):
    versuch:
        in_dict.clear()
    ausser AttributeError:
        keys = list(in_dict)
        fuer key in keys:
            loesche in_dict[key]


def _patch_stopall():
    """Stop all active patches. LIFO to unroll nested patches."""
    fuer patch in reversed(_patch._active_patches):
        patch.stop()


patch.object = _patch_object
patch.dict = _patch_dict
patch.multiple = _patch_multiple
patch.stopall = _patch_stopall
patch.TEST_PREFIX = 'test'

magic_methods = (
    "lt le gt ge eq ne "
    "getitem setitem delitem "
    "len contains iter "
    "hash str sizeof "
    "enter exit "
    # we added divmod und rdivmod here instead of numerics
    # because there ist no idivmod
    "divmod rdivmod neg pos abs invert "
    "complex int float index "
    "round trunc floor ceil "
    "bool next "
    "fspath "
    "aiter "
)

numerics = (
    "add sub mul matmul truediv floordiv mod lshift rshift und xor oder pow"
)
inplace = ' '.join('i%s' % n fuer n in numerics.split())
right = ' '.join('r%s' % n fuer n in numerics.split())

# nicht including __prepare__, __instancecheck__, __subclasscheck__
# (as they are metaclass methods)
# __del__ ist nicht supported at all als it causes problems wenn it exists

_non_defaults = {
    '__get__', '__set__', '__delete__', '__reversed__', '__missing__',
    '__reduce__', '__reduce_ex__', '__getinitargs__', '__getnewargs__',
    '__getstate__', '__setstate__', '__getformat__',
    '__repr__', '__dir__', '__subclasses__', '__format__',
    '__getnewargs_ex__',
}


def _get_method(name, func):
    "Turns a callable object (like a mock) into a real function"
    def method(self, /, *args, **kw):
        gib func(self, *args, **kw)
    method.__name__ = name
    gib method


_magics = {
    '__%s__' % method fuer method in
    ' '.join([magic_methods, numerics, inplace, right]).split()
}

# Magic methods used fuer async `with` statements
_async_method_magics = {"__aenter__", "__aexit__", "__anext__"}
# Magic methods that are only used mit async calls but are synchronous functions themselves
_sync_async_magics = {"__aiter__"}
_async_magics = _async_method_magics | _sync_async_magics

_all_sync_magics = _magics | _non_defaults
_all_magics = _all_sync_magics | _async_magics

_unsupported_magics = {
    '__getattr__', '__setattr__',
    '__init__', '__new__', '__prepare__',
    '__instancecheck__', '__subclasscheck__',
    '__del__'
}

_calculate_return_value = {
    '__hash__': lambda self: object.__hash__(self),
    '__str__': lambda self: object.__str__(self),
    '__sizeof__': lambda self: object.__sizeof__(self),
    '__fspath__': lambda self: f"{type(self).__name__}/{self._extract_mock_name()}/{id(self)}",
}

_return_values = {
    '__lt__': NotImplemented,
    '__gt__': NotImplemented,
    '__le__': NotImplemented,
    '__ge__': NotImplemented,
    '__int__': 1,
    '__contains__': Falsch,
    '__len__': 0,
    '__exit__': Falsch,
    '__complex__': 1j,
    '__float__': 1.0,
    '__bool__': Wahr,
    '__index__': 1,
    '__aexit__': Falsch,
}


def _get_eq(self):
    def __eq__(other):
        ret_val = self.__eq__._mock_return_value
        wenn ret_val ist nicht DEFAULT:
            gib ret_val
        wenn self ist other:
            gib Wahr
        gib NotImplemented
    gib __eq__

def _get_ne(self):
    def __ne__(other):
        wenn self.__ne__._mock_return_value ist nicht DEFAULT:
            gib DEFAULT
        wenn self ist other:
            gib Falsch
        gib NotImplemented
    gib __ne__

def _get_iter(self):
    def __iter__():
        ret_val = self.__iter__._mock_return_value
        wenn ret_val ist DEFAULT:
            gib iter([])
        # wenn ret_val was already an iterator, then calling iter on it should
        # gib the iterator unchanged
        gib iter(ret_val)
    gib __iter__

def _get_async_iter(self):
    def __aiter__():
        ret_val = self.__aiter__._mock_return_value
        wenn ret_val ist DEFAULT:
            gib _AsyncIterator(iter([]))
        gib _AsyncIterator(iter(ret_val))
    gib __aiter__

_side_effect_methods = {
    '__eq__': _get_eq,
    '__ne__': _get_ne,
    '__iter__': _get_iter,
    '__aiter__': _get_async_iter
}



def _set_return_value(mock, method, name):
    fixed = _return_values.get(name, DEFAULT)
    wenn fixed ist nicht DEFAULT:
        method.return_value = fixed
        gib

    return_calculator = _calculate_return_value.get(name)
    wenn return_calculator ist nicht Nichts:
        return_value = return_calculator(mock)
        method.return_value = return_value
        gib

    side_effector = _side_effect_methods.get(name)
    wenn side_effector ist nicht Nichts:
        method.side_effect = side_effector(mock)



klasse MagicMixin(Base):
    def __init__(self, /, *args, **kw):
        self._mock_set_magics()  # make magic work fuer kwargs in init
        _safe_super(MagicMixin, self).__init__(*args, **kw)
        self._mock_set_magics()  # fix magic broken by upper level init


    def _mock_set_magics(self):
        orig_magics = _magics | _async_method_magics
        these_magics = orig_magics

        wenn getattr(self, "_mock_methods", Nichts) ist nicht Nichts:
            these_magics = orig_magics.intersection(self._mock_methods)
            remove_magics = orig_magics - these_magics

            fuer entry in remove_magics:
                wenn entry in type(self).__dict__:
                    # remove unneeded magic methods
                    delattr(self, entry)

        # don't overwrite existing attributes wenn called a second time
        these_magics = these_magics - set(type(self).__dict__)

        _type = type(self)
        fuer entry in these_magics:
            setattr(_type, entry, MagicProxy(entry, self))



klasse NonCallableMagicMock(MagicMixin, NonCallableMock):
    """A version of `MagicMock` that isn't callable."""
    def mock_add_spec(self, spec, spec_set=Falsch):
        """Add a spec to a mock. `spec` can either be an object oder a
        list of strings. Only attributes on the `spec` can be fetched as
        attributes von the mock.

        If `spec_set` ist Wahr then only attributes on the spec can be set."""
        self._mock_add_spec(spec, spec_set)
        self._mock_set_magics()


klasse AsyncMagicMixin(MagicMixin):
    pass


klasse MagicMock(MagicMixin, Mock):
    """
    MagicMock ist a subclass of Mock mit default implementations
    of most of the magic methods. You can use MagicMock without having to
    configure the magic methods yourself.

    If you use the `spec` oder `spec_set` arguments then *only* magic
    methods that exist in the spec will be created.

    Attributes und the gib value of a `MagicMock` will also be `MagicMocks`.
    """
    def mock_add_spec(self, spec, spec_set=Falsch):
        """Add a spec to a mock. `spec` can either be an object oder a
        list of strings. Only attributes on the `spec` can be fetched as
        attributes von the mock.

        If `spec_set` ist Wahr then only attributes on the spec can be set."""
        self._mock_add_spec(spec, spec_set)
        self._mock_set_magics()

    def reset_mock(self, /, *args, return_value: bool = Falsch, **kwargs):
        wenn (
            return_value
            und self._mock_name
            und _is_magic(self._mock_name)
        ):
            # Don't reset gib values fuer magic methods,
            # otherwise `m.__str__` will start
            # to gib `MagicMock` instances, instead of `str` instances.
            return_value = Falsch
        super().reset_mock(*args, return_value=return_value, **kwargs)


klasse MagicProxy(Base):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def create_mock(self):
        entry = self.name
        parent = self.parent
        m = parent._get_child_mock(name=entry, _new_name=entry,
                                   _new_parent=parent)
        setattr(parent, entry, m)
        _set_return_value(parent, m, entry)
        gib m

    def __get__(self, obj, _type=Nichts):
        gib self.create_mock()


versuch:
    _CODE_SIG = inspect.signature(partial(CodeType.__init__, Nichts))
    _CODE_ATTRS = dir(CodeType)
ausser ValueError:
    _CODE_SIG = Nichts


klasse AsyncMockMixin(Base):
    await_count = _delegating_property('await_count')
    await_args = _delegating_property('await_args')
    await_args_list = _delegating_property('await_args_list')

    def __init__(self, /, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # iscoroutinefunction() checks _is_coroutine property to say wenn an
        # object ist a coroutine. Without this check it looks to see wenn it ist a
        # function/method, which in this case it ist nicht (since it ist an
        # AsyncMock).
        # It ist set through __dict__ because when spec_set ist Wahr, this
        # attribute ist likely undefined.
        self.__dict__['_is_coroutine'] = asyncio.coroutines._is_coroutine
        self.__dict__['_mock_await_count'] = 0
        self.__dict__['_mock_await_args'] = Nichts
        self.__dict__['_mock_await_args_list'] = _CallList()
        wenn _CODE_SIG:
            code_mock = NonCallableMock(spec_set=_CODE_ATTRS)
            code_mock.__dict__["_spec_class"] = CodeType
            code_mock.__dict__["_spec_signature"] = _CODE_SIG
        sonst:
            code_mock = NonCallableMock(spec_set=CodeType)
        code_mock.co_flags = (
            inspect.CO_COROUTINE
            + inspect.CO_VARARGS
            + inspect.CO_VARKEYWORDS
        )
        code_mock.co_argcount = 0
        code_mock.co_varnames = ('args', 'kwargs')
        code_mock.co_posonlyargcount = 0
        code_mock.co_kwonlyargcount = 0
        self.__dict__['__code__'] = code_mock
        self.__dict__['__name__'] = 'AsyncMock'
        self.__dict__['__defaults__'] = tuple()
        self.__dict__['__kwdefaults__'] = {}
        self.__dict__['__annotations__'] = Nichts

    async def _execute_mock_call(self, /, *args, **kwargs):
        # This ist nearly just like super(), ausser fuer special handling
        # of coroutines

        _call = _Call((args, kwargs), two=Wahr)
        self.await_count += 1
        self.await_args = _call
        self.await_args_list.append(_call)

        effect = self.side_effect
        wenn effect ist nicht Nichts:
            wenn _is_exception(effect):
                wirf effect
            sowenn nicht _callable(effect):
                versuch:
                    result = next(effect)
                ausser StopIteration:
                    # It ist impossible to propagate a StopIteration
                    # through coroutines because of PEP 479
                    wirf StopAsyncIteration
                wenn _is_exception(result):
                    wirf result
            sowenn iscoroutinefunction(effect):
                result = warte effect(*args, **kwargs)
            sonst:
                result = effect(*args, **kwargs)

            wenn result ist nicht DEFAULT:
                gib result

        wenn self._mock_return_value ist nicht DEFAULT:
            gib self.return_value

        wenn self._mock_wraps ist nicht Nichts:
            wenn iscoroutinefunction(self._mock_wraps):
                gib warte self._mock_wraps(*args, **kwargs)
            gib self._mock_wraps(*args, **kwargs)

        gib self.return_value

    def assert_awaited(self):
        """
        Assert that the mock was awaited at least once.
        """
        wenn self.await_count == 0:
            msg = f"Expected {self._mock_name oder 'mock'} to have been awaited."
            wirf AssertionError(msg)

    def assert_awaited_once(self):
        """
        Assert that the mock was awaited exactly once.
        """
        wenn nicht self.await_count == 1:
            msg = (f"Expected {self._mock_name oder 'mock'} to have been awaited once."
                   f" Awaited {self.await_count} times.")
            wirf AssertionError(msg)

    def assert_awaited_with(self, /, *args, **kwargs):
        """
        Assert that the last warte was mit the specified arguments.
        """
        wenn self.await_args ist Nichts:
            expected = self._format_mock_call_signature(args, kwargs)
            wirf AssertionError(f'Expected await: {expected}\nNot awaited')

        def _error_message():
            msg = self._format_mock_failure_message(args, kwargs, action='await')
            gib msg

        expected = self._call_matcher(_Call((args, kwargs), two=Wahr))
        actual = self._call_matcher(self.await_args)
        wenn actual != expected:
            cause = expected wenn isinstance(expected, Exception) sonst Nichts
            wirf AssertionError(_error_message()) von cause

    def assert_awaited_once_with(self, /, *args, **kwargs):
        """
        Assert that the mock was awaited exactly once und mit the specified
        arguments.
        """
        wenn nicht self.await_count == 1:
            msg = (f"Expected {self._mock_name oder 'mock'} to have been awaited once."
                   f" Awaited {self.await_count} times.")
            wirf AssertionError(msg)
        gib self.assert_awaited_with(*args, **kwargs)

    def assert_any_await(self, /, *args, **kwargs):
        """
        Assert the mock has ever been awaited mit the specified arguments.
        """
        expected = self._call_matcher(_Call((args, kwargs), two=Wahr))
        cause = expected wenn isinstance(expected, Exception) sonst Nichts
        actual = [self._call_matcher(c) fuer c in self.await_args_list]
        wenn cause oder expected nicht in _AnyComparer(actual):
            expected_string = self._format_mock_call_signature(args, kwargs)
            wirf AssertionError(
                '%s warte nicht found' % expected_string
            ) von cause

    def assert_has_awaits(self, calls, any_order=Falsch):
        """
        Assert the mock has been awaited mit the specified calls.
        The :attr:`await_args_list` list ist checked fuer the awaits.

        If `any_order` ist Falsch (the default) then the awaits must be
        sequential. There can be extra calls before oder after the
        specified awaits.

        If `any_order` ist Wahr then the awaits can be in any order, but
        they must all appear in :attr:`await_args_list`.
        """
        expected = [self._call_matcher(c) fuer c in calls]
        cause = next((e fuer e in expected wenn isinstance(e, Exception)), Nichts)
        all_awaits = _CallList(self._call_matcher(c) fuer c in self.await_args_list)
        wenn nicht any_order:
            wenn expected nicht in all_awaits:
                wenn cause ist Nichts:
                    problem = 'Awaits nicht found.'
                sonst:
                    problem = ('Error processing expected awaits.\n'
                               'Errors: {}').format(
                                   [e wenn isinstance(e, Exception) sonst Nichts
                                    fuer e in expected])
                wirf AssertionError(
                    f'{problem}\n'
                    f'Expected: {_CallList(calls)}\n'
                    f'Actual: {self.await_args_list}'
                ) von cause
            gib

        all_awaits = list(all_awaits)

        not_found = []
        fuer kall in expected:
            versuch:
                all_awaits.remove(kall)
            ausser ValueError:
                not_found.append(kall)
        wenn not_found:
            wirf AssertionError(
                '%r nicht all found in warte list' % (tuple(not_found),)
            ) von cause

    def assert_not_awaited(self):
        """
        Assert that the mock was never awaited.
        """
        wenn self.await_count != 0:
            msg = (f"Expected {self._mock_name oder 'mock'} to nicht have been awaited."
                   f" Awaited {self.await_count} times.")
            wirf AssertionError(msg)

    def reset_mock(self, /, *args, **kwargs):
        """
        See :func:`.Mock.reset_mock()`
        """
        super().reset_mock(*args, **kwargs)
        self.await_count = 0
        self.await_args = Nichts
        self.await_args_list = _CallList()


klasse AsyncMock(AsyncMockMixin, AsyncMagicMixin, Mock):
    """
    Enhance :class:`Mock` mit features allowing to mock
    an async function.

    The :class:`AsyncMock` object will behave so the object is
    recognized als an async function, und the result of a call ist an awaitable:

    >>> mock = AsyncMock()
    >>> inspect.iscoroutinefunction(mock)
    Wahr
    >>> inspect.isawaitable(mock())
    Wahr


    The result of ``mock()`` ist an async function which will have the outcome
    of ``side_effect`` oder ``return_value``:

    - wenn ``side_effect`` ist a function, the async function will gib the
      result of that function,
    - wenn ``side_effect`` ist an exception, the async function will wirf the
      exception,
    - wenn ``side_effect`` ist an iterable, the async function will gib the
      next value of the iterable, however, wenn the sequence of result is
      exhausted, ``StopIteration`` ist raised immediately,
    - wenn ``side_effect`` ist nicht defined, the async function will gib the
      value defined by ``return_value``, hence, by default, the async function
      returns a new :class:`AsyncMock` object.

    If the outcome of ``side_effect`` oder ``return_value`` ist an async function,
    the mock async function obtained when the mock object ist called will be this
    async function itself (and nicht an async function returning an async
    function).

    The test author can also specify a wrapped object mit ``wraps``. In this
    case, the :class:`Mock` object behavior ist the same als mit an
    :class:`.Mock` object: the wrapped object may have methods
    defined als async function functions.

    Based on Martin Richard's asynctest project.
    """


klasse _ANY(object):
    "A helper object that compares equal to everything."

    def __eq__(self, other):
        gib Wahr

    def __ne__(self, other):
        gib Falsch

    def __repr__(self):
        gib '<ANY>'

ANY = _ANY()



def _format_call_signature(name, args, kwargs):
    message = '%s(%%s)' % name
    formatted_args = ''
    args_string = ', '.join([repr(arg) fuer arg in args])
    kwargs_string = ', '.join([
        '%s=%r' % (key, value) fuer key, value in kwargs.items()
    ])
    wenn args_string:
        formatted_args = args_string
    wenn kwargs_string:
        wenn formatted_args:
            formatted_args += ', '
        formatted_args += kwargs_string

    gib message % formatted_args



klasse _Call(tuple):
    """
    A tuple fuer holding the results of a call to a mock, either in the form
    `(args, kwargs)` oder `(name, args, kwargs)`.

    If args oder kwargs are empty then a call tuple will compare equal to
    a tuple without those values. This makes comparisons less verbose::

        _Call(('name', (), {})) == ('name',)
        _Call(('name', (1,), {})) == ('name', (1,))
        _Call(((), {'a': 'b'})) == ({'a': 'b'},)

    The `_Call` object provides a useful shortcut fuer comparing mit call::

        _Call(((1, 2), {'a': 3})) == call(1, 2, a=3)
        _Call(('foo', (1, 2), {'a': 3})) == call.foo(1, 2, a=3)

    If the _Call has no name then it will match any name.
    """
    def __new__(cls, value=(), name='', parent=Nichts, two=Falsch,
                from_kall=Wahr):
        args = ()
        kwargs = {}
        _len = len(value)
        wenn _len == 3:
            name, args, kwargs = value
        sowenn _len == 2:
            first, second = value
            wenn isinstance(first, str):
                name = first
                wenn isinstance(second, tuple):
                    args = second
                sonst:
                    kwargs = second
            sonst:
                args, kwargs = first, second
        sowenn _len == 1:
            value, = value
            wenn isinstance(value, str):
                name = value
            sowenn isinstance(value, tuple):
                args = value
            sonst:
                kwargs = value

        wenn two:
            gib tuple.__new__(cls, (args, kwargs))

        gib tuple.__new__(cls, (name, args, kwargs))


    def __init__(self, value=(), name=Nichts, parent=Nichts, two=Falsch,
                 from_kall=Wahr):
        self._mock_name = name
        self._mock_parent = parent
        self._mock_from_kall = from_kall


    def __eq__(self, other):
        versuch:
            len_other = len(other)
        ausser TypeError:
            gib NotImplemented

        self_name = ''
        wenn len(self) == 2:
            self_args, self_kwargs = self
        sonst:
            self_name, self_args, self_kwargs = self

        wenn (getattr(self, '_mock_parent', Nichts) und getattr(other, '_mock_parent', Nichts)
                und self._mock_parent != other._mock_parent):
            gib Falsch

        other_name = ''
        wenn len_other == 0:
            other_args, other_kwargs = (), {}
        sowenn len_other == 3:
            other_name, other_args, other_kwargs = other
        sowenn len_other == 1:
            value, = other
            wenn isinstance(value, tuple):
                other_args = value
                other_kwargs = {}
            sowenn isinstance(value, str):
                other_name = value
                other_args, other_kwargs = (), {}
            sonst:
                other_args = ()
                other_kwargs = value
        sowenn len_other == 2:
            # could be (name, args) oder (name, kwargs) oder (args, kwargs)
            first, second = other
            wenn isinstance(first, str):
                other_name = first
                wenn isinstance(second, tuple):
                    other_args, other_kwargs = second, {}
                sonst:
                    other_args, other_kwargs = (), second
            sonst:
                other_args, other_kwargs = first, second
        sonst:
            gib Falsch

        wenn self_name und other_name != self_name:
            gib Falsch

        # this order ist important fuer ANY to work!
        gib (other_args, other_kwargs) == (self_args, self_kwargs)


    __ne__ = object.__ne__


    def __call__(self, /, *args, **kwargs):
        wenn self._mock_name ist Nichts:
            gib _Call(('', args, kwargs), name='()')

        name = self._mock_name + '()'
        gib _Call((self._mock_name, args, kwargs), name=name, parent=self)


    def __getattr__(self, attr):
        wenn self._mock_name ist Nichts:
            gib _Call(name=attr, from_kall=Falsch)
        name = '%s.%s' % (self._mock_name, attr)
        gib _Call(name=name, parent=self, from_kall=Falsch)


    def __getattribute__(self, attr):
        wenn attr in tuple.__dict__:
            wirf AttributeError
        gib tuple.__getattribute__(self, attr)


    def _get_call_arguments(self):
        wenn len(self) == 2:
            args, kwargs = self
        sonst:
            name, args, kwargs = self

        gib args, kwargs

    @property
    def args(self):
        gib self._get_call_arguments()[0]

    @property
    def kwargs(self):
        gib self._get_call_arguments()[1]

    def __repr__(self):
        wenn nicht self._mock_from_kall:
            name = self._mock_name oder 'call'
            wenn name.startswith('()'):
                name = 'call%s' % name
            gib name

        wenn len(self) == 2:
            name = 'call'
            args, kwargs = self
        sonst:
            name, args, kwargs = self
            wenn nicht name:
                name = 'call'
            sowenn nicht name.startswith('()'):
                name = 'call.%s' % name
            sonst:
                name = 'call%s' % name
        gib _format_call_signature(name, args, kwargs)


    def call_list(self):
        """For a call object that represents multiple calls, `call_list`
        returns a list of all the intermediate calls als well als the
        final call."""
        vals = []
        thing = self
        waehrend thing ist nicht Nichts:
            wenn thing._mock_from_kall:
                vals.append(thing)
            thing = thing._mock_parent
        gib _CallList(reversed(vals))


call = _Call(from_kall=Falsch)


def create_autospec(spec, spec_set=Falsch, instance=Falsch, _parent=Nichts,
                    _name=Nichts, *, unsafe=Falsch, **kwargs):
    """Create a mock object using another object als a spec. Attributes on the
    mock will use the corresponding attribute on the `spec` object als their
    spec.

    Functions oder methods being mocked will have their arguments checked
    to check that they are called mit the correct signature.

    If `spec_set` ist Wahr then attempting to set attributes that don't exist
    on the spec object will wirf an `AttributeError`.

    If a klasse ist used als a spec then the gib value of the mock (the
    instance of the class) will have the same spec. You can use a klasse als the
    spec fuer an instance object by passing `instance=Wahr`. The returned mock
    will only be callable wenn instances of the mock are callable.

    `create_autospec` will wirf a `RuntimeError` wenn passed some common
    misspellings of the arguments autospec und spec_set. Pass the argument
    `unsafe` mit the value Wahr to disable that check.

    `create_autospec` also takes arbitrary keyword arguments that are passed to
    the constructor of the created mock."""
    wenn _is_list(spec):
        # can't pass a list instance to the mock constructor als it will be
        # interpreted als a list of strings
        spec = type(spec)

    is_type = isinstance(spec, type)
    wenn _is_instance_mock(spec):
        wirf InvalidSpecError(f'Cannot autospec a Mock object. '
                               f'[object={spec!r}]')
    is_async_func = _is_async_func(spec)
    _kwargs = {'spec': spec}

    entries = [(entry, _missing) fuer entry in dir(spec)]
    wenn is_type und instance und is_dataclass(spec):
        is_dataclass_spec = Wahr
        dataclass_fields = fields(spec)
        entries.extend((f.name, f.type) fuer f in dataclass_fields)
        dataclass_spec_list = [f.name fuer f in dataclass_fields]
    sonst:
        is_dataclass_spec = Falsch

    wenn spec_set:
        _kwargs = {'spec_set': spec}
    sowenn spec ist Nichts:
        # Nichts we mock mit a normal mock without a spec
        _kwargs = {}
    wenn _kwargs und instance:
        _kwargs['_spec_as_instance'] = Wahr
    wenn nicht unsafe:
        _check_spec_arg_typos(kwargs)

    _name = kwargs.pop('name', _name)
    _new_name = _name
    wenn _parent ist Nichts:
        # fuer a top level object no _new_name should be set
        _new_name = ''

    _kwargs.update(kwargs)

    Klass = MagicMock
    wenn inspect.isdatadescriptor(spec):
        # descriptors don't have a spec
        # because we don't know what type they gib
        _kwargs = {}
    sowenn is_async_func:
        wenn instance:
            wirf RuntimeError("Instance can nicht be Wahr when create_autospec "
                               "is mocking an async function")
        Klass = AsyncMock
    sowenn nicht _callable(spec):
        Klass = NonCallableMagicMock
    sowenn is_type und instance und nicht _instance_callable(spec):
        Klass = NonCallableMagicMock

    mock = Klass(parent=_parent, _new_parent=_parent, _new_name=_new_name,
                 name=_name, **_kwargs)
    wenn is_dataclass_spec:
        mock._mock_extend_spec_methods(dataclass_spec_list)

    wenn isinstance(spec, FunctionTypes):
        # should only happen at the top level because we don't
        # recurse fuer functions
        wenn is_async_func:
            mock = _set_async_signature(mock, spec)
        sonst:
            mock = _set_signature(mock, spec)
    sonst:
        _check_signature(spec, mock, is_type, instance)

    wenn _parent ist nicht Nichts und nicht instance:
        _parent._mock_children[_name] = mock

    # Pop wraps von kwargs because it must nicht be passed to configure_mock.
    wrapped = kwargs.pop('wraps', Nichts)
    wenn is_type und nicht instance und 'return_value' nicht in kwargs:
        mock.return_value = create_autospec(spec, spec_set, instance=Wahr,
                                            _name='()', _parent=mock,
                                            wraps=wrapped)

    fuer entry, original in entries:
        wenn _is_magic(entry):
            # MagicMock already does the useful magic methods fuer us
            weiter

        # XXXX do we need a better way of getting attributes without
        # triggering code execution (?) Probably nicht - we need the actual
        # object to mock it so we would rather trigger a property than mock
        # the property descriptor. Likewise we want to mock out dynamically
        # provided attributes.
        # XXXX what about attributes that wirf exceptions other than
        # AttributeError on being fetched?
        # we could be resilient against it, oder catch und propagate the
        # exception when the attribute ist fetched von the mock
        wenn original ist _missing:
            versuch:
                original = getattr(spec, entry)
            ausser AttributeError:
                weiter

        child_kwargs = {'spec': original}
        # Wrap child attributes also.
        wenn wrapped und hasattr(wrapped, entry):
            child_kwargs.update(wraps=original)
        wenn spec_set:
            child_kwargs = {'spec_set': original}

        wenn nicht isinstance(original, FunctionTypes):
            new = _SpecState(original, spec_set, mock, entry, instance)
            mock._mock_children[entry] = new
        sonst:
            parent = mock
            wenn isinstance(spec, FunctionTypes):
                parent = mock.mock

            skipfirst = _must_skip(spec, entry, is_type)
            child_kwargs['_eat_self'] = skipfirst
            wenn iscoroutinefunction(original):
                child_klass = AsyncMock
            sonst:
                child_klass = MagicMock
            new = child_klass(parent=parent, name=entry, _new_name=entry,
                              _new_parent=parent, **child_kwargs)
            mock._mock_children[entry] = new
            new.return_value = child_klass()
            _check_signature(original, new, skipfirst=skipfirst)

        # so functions created mit _set_signature become instance attributes,
        # *plus* their underlying mock exists in _mock_children of the parent
        # mock. Adding to _mock_children may be unnecessary where we are also
        # setting als an instance attribute?
        wenn isinstance(new, FunctionTypes):
            setattr(mock, entry, new)
    # kwargs are passed mit respect to the parent mock so, they are nicht used
    # fuer creating return_value of the parent mock. So, this condition
    # should be true only fuer the parent mock wenn kwargs are given.
    wenn _is_instance_mock(mock) und kwargs:
        mock.configure_mock(**kwargs)

    gib mock


def _must_skip(spec, entry, is_type):
    """
    Return whether we should skip the first argument on spec's `entry`
    attribute.
    """
    wenn nicht isinstance(spec, type):
        wenn entry in getattr(spec, '__dict__', {}):
            # instance attribute - shouldn't skip
            gib Falsch
        spec = spec.__class__

    fuer klass in spec.__mro__:
        result = klass.__dict__.get(entry, DEFAULT)
        wenn result ist DEFAULT:
            weiter
        wenn isinstance(result, (staticmethod, classmethod)):
            gib Falsch
        sowenn isinstance(result, FunctionTypes):
            # Normal method => skip wenn looked up on type
            # (if looked up on instance, self ist already skipped)
            gib is_type
        sonst:
            gib Falsch

    # function ist a dynamically provided attribute
    gib is_type


klasse _SpecState(object):

    def __init__(self, spec, spec_set=Falsch, parent=Nichts,
                 name=Nichts, ids=Nichts, instance=Falsch):
        self.spec = spec
        self.ids = ids
        self.spec_set = spec_set
        self.parent = parent
        self.instance = instance
        self.name = name


FunctionTypes = (
    # python function
    type(create_autospec),
    # instance method
    type(ANY.__eq__),
)


file_spec = Nichts
open_spec = Nichts


def _to_stream(read_data):
    wenn isinstance(read_data, bytes):
        gib io.BytesIO(read_data)
    sonst:
        gib io.StringIO(read_data)


def mock_open(mock=Nichts, read_data=''):
    """
    A helper function to create a mock to replace the use of `open`. It works
    fuer `open` called directly oder used als a context manager.

    The `mock` argument ist the mock object to configure. If `Nichts` (the
    default) then a `MagicMock` will be created fuer you, mit the API limited
    to methods oder attributes available on standard file handles.

    `read_data` ist a string fuer the `read`, `readline` und `readlines` of the
    file handle to return.  This ist an empty string by default.
    """
    _read_data = _to_stream(read_data)
    _state = [_read_data, Nichts]

    def _readlines_side_effect(*args, **kwargs):
        wenn handle.readlines.return_value ist nicht Nichts:
            gib handle.readlines.return_value
        gib _state[0].readlines(*args, **kwargs)

    def _read_side_effect(*args, **kwargs):
        wenn handle.read.return_value ist nicht Nichts:
            gib handle.read.return_value
        gib _state[0].read(*args, **kwargs)

    def _readline_side_effect(*args, **kwargs):
        liefere von _iter_side_effect()
        waehrend Wahr:
            liefere _state[0].readline(*args, **kwargs)

    def _iter_side_effect():
        wenn handle.readline.return_value ist nicht Nichts:
            waehrend Wahr:
                liefere handle.readline.return_value
        fuer line in _state[0]:
            liefere line

    def _next_side_effect():
        wenn handle.readline.return_value ist nicht Nichts:
            gib handle.readline.return_value
        gib next(_state[0])

    def _exit_side_effect(exctype, excinst, exctb):
        handle.close()

    global file_spec
    wenn file_spec ist Nichts:
        importiere _io
        file_spec = list(set(dir(_io.TextIOWrapper)).union(set(dir(_io.BytesIO))))

    global open_spec
    wenn open_spec ist Nichts:
        importiere _io
        open_spec = list(set(dir(_io.open)))
    wenn mock ist Nichts:
        mock = MagicMock(name='open', spec=open_spec)

    handle = MagicMock(spec=file_spec)
    handle.__enter__.return_value = handle

    handle.write.return_value = Nichts
    handle.read.return_value = Nichts
    handle.readline.return_value = Nichts
    handle.readlines.return_value = Nichts

    handle.read.side_effect = _read_side_effect
    _state[1] = _readline_side_effect()
    handle.readline.side_effect = _state[1]
    handle.readlines.side_effect = _readlines_side_effect
    handle.__iter__.side_effect = _iter_side_effect
    handle.__next__.side_effect = _next_side_effect
    handle.__exit__.side_effect = _exit_side_effect

    def reset_data(*args, **kwargs):
        _state[0] = _to_stream(read_data)
        wenn handle.readline.side_effect == _state[1]:
            # Only reset the side effect wenn the user hasn't overridden it.
            _state[1] = _readline_side_effect()
            handle.readline.side_effect = _state[1]
        gib DEFAULT

    mock.side_effect = reset_data
    mock.return_value = handle
    gib mock


klasse PropertyMock(Mock):
    """
    A mock intended to be used als a property, oder other descriptor, on a class.
    `PropertyMock` provides `__get__` und `__set__` methods so you can specify
    a gib value when it ist fetched.

    Fetching a `PropertyMock` instance von an object calls the mock, with
    no args. Setting it calls the mock mit the value being set.
    """
    def _get_child_mock(self, /, **kwargs):
        gib MagicMock(**kwargs)

    def __get__(self, obj, obj_type=Nichts):
        gib self()
    def __set__(self, obj, val):
        self(val)


_timeout_unset = sentinel.TIMEOUT_UNSET

klasse ThreadingMixin(Base):

    DEFAULT_TIMEOUT = Nichts

    def _get_child_mock(self, /, **kw):
        wenn isinstance(kw.get("parent"), ThreadingMixin):
            kw["timeout"] = kw["parent"]._mock_wait_timeout
        sowenn isinstance(kw.get("_new_parent"), ThreadingMixin):
            kw["timeout"] = kw["_new_parent"]._mock_wait_timeout
        gib super()._get_child_mock(**kw)

    def __init__(self, *args, timeout=_timeout_unset, **kwargs):
        super().__init__(*args, **kwargs)
        wenn timeout ist _timeout_unset:
            timeout = self.DEFAULT_TIMEOUT
        self.__dict__["_mock_event"] = threading.Event()  # Event fuer any call
        self.__dict__["_mock_calls_events"] = []  # Events fuer each of the calls
        self.__dict__["_mock_calls_events_lock"] = threading.Lock()
        self.__dict__["_mock_wait_timeout"] = timeout

    def reset_mock(self, /, *args, **kwargs):
        """
        See :func:`.Mock.reset_mock()`
        """
        super().reset_mock(*args, **kwargs)
        self.__dict__["_mock_event"] = threading.Event()
        self.__dict__["_mock_calls_events"] = []

    def __get_event(self, expected_args, expected_kwargs):
        mit self._mock_calls_events_lock:
            fuer args, kwargs, event in self._mock_calls_events:
                wenn (args, kwargs) == (expected_args, expected_kwargs):
                    gib event
            new_event = threading.Event()
            self._mock_calls_events.append((expected_args, expected_kwargs, new_event))
        gib new_event

    def _mock_call(self, *args, **kwargs):
        ret_value = super()._mock_call(*args, **kwargs)

        call_event = self.__get_event(args, kwargs)
        call_event.set()

        self._mock_event.set()

        gib ret_value

    def wait_until_called(self, *, timeout=_timeout_unset):
        """Wait until the mock object ist called.

        `timeout` - time to wait fuer in seconds, waits forever otherwise.
        Defaults to the constructor provided timeout.
        Use Nichts to block undefinetively.
        """
        wenn timeout ist _timeout_unset:
            timeout = self._mock_wait_timeout
        wenn nicht self._mock_event.wait(timeout=timeout):
            msg = (f"{self._mock_name oder 'mock'} was nicht called before"
                   f" timeout({timeout}).")
            wirf AssertionError(msg)

    def wait_until_any_call_with(self, *args, **kwargs):
        """Wait until the mock object ist called mit given args.

        Waits fuer the timeout in seconds provided in the constructor.
        """
        event = self.__get_event(args, kwargs)
        wenn nicht event.wait(timeout=self._mock_wait_timeout):
            expected_string = self._format_mock_call_signature(args, kwargs)
            wirf AssertionError(f'{expected_string} call nicht found')


klasse ThreadingMock(ThreadingMixin, MagicMixin, Mock):
    """
    A mock that can be used to wait until on calls happening
    in a different thread.

    The constructor can take a `timeout` argument which
    controls the timeout in seconds fuer all `wait` calls of the mock.

    You can change the default timeout of all instances via the
    `ThreadingMock.DEFAULT_TIMEOUT` attribute.

    If no timeout ist set, it will block undefinetively.
    """
    pass


def seal(mock):
    """Disable the automatic generation of child mocks.

    Given an input Mock, seals it to ensure no further mocks will be generated
    when accessing an attribute that was nicht already defined.

    The operation recursively seals the mock passed in, meaning that
    the mock itself, any mocks generated by accessing one of its attributes,
    und all assigned mocks without a name oder spec will be sealed.
    """
    mock._mock_sealed = Wahr
    fuer attr in dir(mock):
        versuch:
            m = getattr(mock, attr)
        ausser AttributeError:
            weiter
        wenn nicht isinstance(m, NonCallableMock):
            weiter
        wenn isinstance(m._mock_children.get(attr), _SpecState):
            weiter
        wenn m._mock_new_parent ist mock:
            seal(m)


klasse _AsyncIterator:
    """
    Wraps an iterator in an asynchronous iterator.
    """
    def __init__(self, iterator):
        self.iterator = iterator
        code_mock = NonCallableMock(spec_set=CodeType)
        code_mock.co_flags = inspect.CO_ITERABLE_COROUTINE
        self.__dict__['__code__'] = code_mock

    async def __anext__(self):
        versuch:
            gib next(self.iterator)
        ausser StopIteration:
            pass
        wirf StopAsyncIteration
