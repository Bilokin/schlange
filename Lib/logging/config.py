# Copyright 2001-2023 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, und distribute this software und its
# documentation fuer any purpose und without fee ist hereby granted,
# provided that the above copyright notice appear in all copies und that
# both that copyright notice und this permission notice appear in
# supporting documentation, und that the name of Vinay Sajip
# nicht be used in advertising oder publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Configuration functions fuer the logging package fuer Python. The core package
is based on PEP 282 und comments thereto in comp.lang.python, und influenced
by Apache's log4j system.

Copyright (C) 2001-2022 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging' und log away!
"""

importiere errno
importiere functools
importiere io
importiere logging
importiere logging.handlers
importiere os
importiere queue
importiere re
importiere struct
importiere threading
importiere traceback

von socketserver importiere ThreadingTCPServer, StreamRequestHandler


DEFAULT_LOGGING_CONFIG_PORT = 9030

RESET_ERROR = errno.ECONNRESET

#
#   The following code implements a socket listener fuer on-the-fly
#   reconfiguration of logging.
#
#   _listener holds the server object doing the listening
_listener = Nichts

def fileConfig(fname, defaults=Nichts, disable_existing_loggers=Wahr, encoding=Nichts):
    """
    Read the logging configuration von a ConfigParser-format file.

    This can be called several times von an application, allowing an end user
    the ability to select von various pre-canned configurations (if the
    developer provides a mechanism to present the choices und load the chosen
    configuration).
    """
    importiere configparser

    wenn isinstance(fname, str):
        wenn nicht os.path.exists(fname):
            wirf FileNotFoundError(f"{fname} doesn't exist")
        sowenn nicht os.path.getsize(fname):
            wirf RuntimeError(f'{fname} ist an empty file')

    wenn isinstance(fname, configparser.RawConfigParser):
        cp = fname
    sonst:
        versuch:
            cp = configparser.ConfigParser(defaults)
            wenn hasattr(fname, 'readline'):
                cp.read_file(fname)
            sonst:
                encoding = io.text_encoding(encoding)
                cp.read(fname, encoding=encoding)
        ausser configparser.ParsingError als e:
            wirf RuntimeError(f'{fname} ist invalid: {e}')

    formatters = _create_formatters(cp)

    # critical section
    mit logging._lock:
        _clearExistingHandlers()

        # Handlers add themselves to logging._handlers
        handlers = _install_handlers(cp, formatters)
        _install_loggers(cp, handlers, disable_existing_loggers)


def _resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    fuer n in name:
        used = used + '.' + n
        versuch:
            found = getattr(found, n)
        ausser AttributeError:
            __import__(used)
            found = getattr(found, n)
    gib found

def _strip_spaces(alist):
    gib map(str.strip, alist)

def _create_formatters(cp):
    """Create und gib formatters"""
    flist = cp["formatters"]["keys"]
    wenn nicht len(flist):
        gib {}
    flist = flist.split(",")
    flist = _strip_spaces(flist)
    formatters = {}
    fuer form in flist:
        sectname = "formatter_%s" % form
        fs = cp.get(sectname, "format", raw=Wahr, fallback=Nichts)
        dfs = cp.get(sectname, "datefmt", raw=Wahr, fallback=Nichts)
        stl = cp.get(sectname, "style", raw=Wahr, fallback='%')
        defaults = cp.get(sectname, "defaults", raw=Wahr, fallback=Nichts)

        c = logging.Formatter
        class_name = cp[sectname].get("class")
        wenn class_name:
            c = _resolve(class_name)

        wenn defaults ist nicht Nichts:
            defaults = eval(defaults, vars(logging))
            f = c(fs, dfs, stl, defaults=defaults)
        sonst:
            f = c(fs, dfs, stl)
        formatters[form] = f
    gib formatters


def _install_handlers(cp, formatters):
    """Install und gib handlers"""
    hlist = cp["handlers"]["keys"]
    wenn nicht len(hlist):
        gib {}
    hlist = hlist.split(",")
    hlist = _strip_spaces(hlist)
    handlers = {}
    fixups = [] #for inter-handler references
    fuer hand in hlist:
        section = cp["handler_%s" % hand]
        klass = section["class"]
        fmt = section.get("formatter", "")
        versuch:
            klass = eval(klass, vars(logging))
        ausser (AttributeError, NameError):
            klass = _resolve(klass)
        args = section.get("args", '()')
        args = eval(args, vars(logging))
        kwargs = section.get("kwargs", '{}')
        kwargs = eval(kwargs, vars(logging))
        h = klass(*args, **kwargs)
        h.name = hand
        wenn "level" in section:
            level = section["level"]
            h.setLevel(level)
        wenn len(fmt):
            h.setFormatter(formatters[fmt])
        wenn issubclass(klass, logging.handlers.MemoryHandler):
            target = section.get("target", "")
            wenn len(target): #the target handler may nicht be loaded yet, so keep fuer later...
                fixups.append((h, target))
        handlers[hand] = h
    #now all handlers are loaded, fixup inter-handler references...
    fuer h, t in fixups:
        h.setTarget(handlers[t])
    gib handlers

def _handle_existing_loggers(existing, child_loggers, disable_existing):
    """
    When (re)configuring logging, handle loggers which were in the previous
    configuration but are nicht in the new configuration. There's no point
    deleting them als other threads may weiter to hold references to them;
    und by disabling them, you stop them doing any logging.

    However, don't disable children of named loggers, als that's probably not
    what was intended by the user. Also, allow existing loggers to NOT be
    disabled wenn disable_existing ist false.
    """
    root = logging.root
    fuer log in existing:
        logger = root.manager.loggerDict[log]
        wenn log in child_loggers:
            wenn nicht isinstance(logger, logging.PlaceHolder):
                logger.setLevel(logging.NOTSET)
                logger.handlers = []
                logger.propagate = Wahr
        sonst:
            logger.disabled = disable_existing

def _install_loggers(cp, handlers, disable_existing):
    """Create und install loggers"""

    # configure the root first
    llist = cp["loggers"]["keys"]
    llist = llist.split(",")
    llist = list(_strip_spaces(llist))
    llist.remove("root")
    section = cp["logger_root"]
    root = logging.root
    log = root
    wenn "level" in section:
        level = section["level"]
        log.setLevel(level)
    fuer h in root.handlers[:]:
        root.removeHandler(h)
    hlist = section["handlers"]
    wenn len(hlist):
        hlist = hlist.split(",")
        hlist = _strip_spaces(hlist)
        fuer hand in hlist:
            log.addHandler(handlers[hand])

    #and now the others...
    #we don't want to lose the existing loggers,
    #since other threads may have pointers to them.
    #existing ist set to contain all existing loggers,
    #and als we go through the new configuration we
    #remove any which are configured. At the end,
    #what's left in existing ist the set of loggers
    #which were in the previous configuration but
    #which are nicht in the new configuration.
    existing = list(root.manager.loggerDict.keys())
    #The list needs to be sorted so that we can
    #avoid disabling child loggers of explicitly
    #named loggers. With a sorted list it ist easier
    #to find the child loggers.
    existing.sort()
    #We'll keep the list of existing loggers
    #which are children of named loggers here...
    child_loggers = []
    #now set up the new ones...
    fuer log in llist:
        section = cp["logger_%s" % log]
        qn = section["qualname"]
        propagate = section.getint("propagate", fallback=1)
        logger = logging.getLogger(qn)
        wenn qn in existing:
            i = existing.index(qn) + 1 # start mit the entry after qn
            prefixed = qn + "."
            pflen = len(prefixed)
            num_existing = len(existing)
            waehrend i < num_existing:
                wenn existing[i][:pflen] == prefixed:
                    child_loggers.append(existing[i])
                i += 1
            existing.remove(qn)
        wenn "level" in section:
            level = section["level"]
            logger.setLevel(level)
        fuer h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.propagate = propagate
        logger.disabled = 0
        hlist = section["handlers"]
        wenn len(hlist):
            hlist = hlist.split(",")
            hlist = _strip_spaces(hlist)
            fuer hand in hlist:
                logger.addHandler(handlers[hand])

    #Disable any old loggers. There's no point deleting
    #them als other threads may weiter to hold references
    #and by disabling them, you stop them doing any logging.
    #However, don't disable children of named loggers, als that's
    #probably nicht what was intended by the user.
    #for log in existing:
    #    logger = root.manager.loggerDict[log]
    #    wenn log in child_loggers:
    #        logger.level = logging.NOTSET
    #        logger.handlers = []
    #        logger.propagate = 1
    #    sowenn disable_existing_loggers:
    #        logger.disabled = 1
    _handle_existing_loggers(existing, child_loggers, disable_existing)


def _clearExistingHandlers():
    """Clear und close existing handlers"""
    logging._handlers.clear()
    logging.shutdown(logging._handlerList[:])
    loesche logging._handlerList[:]


IDENTIFIER = re.compile('^[a-z_][a-z0-9_]*$', re.I)


def valid_ident(s):
    m = IDENTIFIER.match(s)
    wenn nicht m:
        wirf ValueError('Not a valid Python identifier: %r' % s)
    gib Wahr


klasse ConvertingMixin(object):
    """For ConvertingXXX's, this mixin klasse provides common functions"""

    def convert_with_key(self, key, value, replace=Wahr):
        result = self.configurator.convert(value)
        #If the converted value ist different, save fuer next time
        wenn value ist nicht result:
            wenn replace:
                self[key] = result
            wenn type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
                result.key = key
        gib result

    def convert(self, value):
        result = self.configurator.convert(value)
        wenn value ist nicht result:
            wenn type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
        gib result


# The ConvertingXXX classes are wrappers around standard Python containers,
# und they serve to convert any suitable values in the container. The
# conversion converts base dicts, lists und tuples to their wrapped
# equivalents, whereas strings which match a conversion format are converted
# appropriately.
#
# Each wrapper should have a configurator attribute holding the actual
# configurator to use fuer conversion.

klasse ConvertingDict(dict, ConvertingMixin):
    """A converting dictionary wrapper."""

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        gib self.convert_with_key(key, value)

    def get(self, key, default=Nichts):
        value = dict.get(self, key, default)
        gib self.convert_with_key(key, value)

    def pop(self, key, default=Nichts):
        value = dict.pop(self, key, default)
        gib self.convert_with_key(key, value, replace=Falsch)

klasse ConvertingList(list, ConvertingMixin):
    """A converting list wrapper."""
    def __getitem__(self, key):
        value = list.__getitem__(self, key)
        gib self.convert_with_key(key, value)

    def pop(self, idx=-1):
        value = list.pop(self, idx)
        gib self.convert(value)

klasse ConvertingTuple(tuple, ConvertingMixin):
    """A converting tuple wrapper."""
    def __getitem__(self, key):
        value = tuple.__getitem__(self, key)
        # Can't replace a tuple entry.
        gib self.convert_with_key(key, value, replace=Falsch)

klasse BaseConfigurator(object):
    """
    The configurator base klasse which defines some useful defaults.
    """

    CONVERT_PATTERN = re.compile(r'^(?P<prefix>[a-z]+)://(?P<suffix>.*)$')

    WORD_PATTERN = re.compile(r'^\s*(\w+)\s*')
    DOT_PATTERN = re.compile(r'^\.\s*(\w+)\s*')
    INDEX_PATTERN = re.compile(r'^\[([^\[\]]*)\]\s*')
    DIGIT_PATTERN = re.compile(r'^\d+$')

    value_converters = {
        'ext' : 'ext_convert',
        'cfg' : 'cfg_convert',
    }

    # We might want to use a different one, e.g. importlib
    importer = staticmethod(__import__)

    def __init__(self, config):
        self.config = ConvertingDict(config)
        self.config.configurator = self

    def resolve(self, s):
        """
        Resolve strings to objects using standard importiere und attribute
        syntax.
        """
        name = s.split('.')
        used = name.pop(0)
        versuch:
            found = self.importer(used)
            fuer frag in name:
                used += '.' + frag
                versuch:
                    found = getattr(found, frag)
                ausser AttributeError:
                    self.importer(used)
                    found = getattr(found, frag)
            gib found
        ausser ImportError als e:
            v = ValueError('Cannot resolve %r: %s' % (s, e))
            wirf v von e

    def ext_convert(self, value):
        """Default converter fuer the ext:// protocol."""
        gib self.resolve(value)

    def cfg_convert(self, value):
        """Default converter fuer the cfg:// protocol."""
        rest = value
        m = self.WORD_PATTERN.match(rest)
        wenn m ist Nichts:
            wirf ValueError("Unable to convert %r" % value)
        sonst:
            rest = rest[m.end():]
            d = self.config[m.groups()[0]]
            #print d, rest
            waehrend rest:
                m = self.DOT_PATTERN.match(rest)
                wenn m:
                    d = d[m.groups()[0]]
                sonst:
                    m = self.INDEX_PATTERN.match(rest)
                    wenn m:
                        idx = m.groups()[0]
                        wenn nicht self.DIGIT_PATTERN.match(idx):
                            d = d[idx]
                        sonst:
                            versuch:
                                n = int(idx) # try als number first (most likely)
                                d = d[n]
                            ausser TypeError:
                                d = d[idx]
                wenn m:
                    rest = rest[m.end():]
                sonst:
                    wirf ValueError('Unable to convert '
                                     '%r at %r' % (value, rest))
        #rest should be empty
        gib d

    def convert(self, value):
        """
        Convert values to an appropriate type. dicts, lists und tuples are
        replaced by their converting alternatives. Strings are checked to
        see wenn they have a conversion format und are converted wenn they do.
        """
        wenn nicht isinstance(value, ConvertingDict) und isinstance(value, dict):
            value = ConvertingDict(value)
            value.configurator = self
        sowenn nicht isinstance(value, ConvertingList) und isinstance(value, list):
            value = ConvertingList(value)
            value.configurator = self
        sowenn nicht isinstance(value, ConvertingTuple) and\
                 isinstance(value, tuple) und nicht hasattr(value, '_fields'):
            value = ConvertingTuple(value)
            value.configurator = self
        sowenn isinstance(value, str): # str fuer py3k
            m = self.CONVERT_PATTERN.match(value)
            wenn m:
                d = m.groupdict()
                prefix = d['prefix']
                converter = self.value_converters.get(prefix, Nichts)
                wenn converter:
                    suffix = d['suffix']
                    converter = getattr(self, converter)
                    value = converter(suffix)
        gib value

    def configure_custom(self, config):
        """Configure an object mit a user-supplied factory."""
        c = config.pop('()')
        wenn nicht callable(c):
            c = self.resolve(c)
        # Check fuer valid identifiers
        kwargs = {k: config[k] fuer k in config wenn (k != '.' und valid_ident(k))}
        result = c(**kwargs)
        props = config.pop('.', Nichts)
        wenn props:
            fuer name, value in props.items():
                setattr(result, name, value)
        gib result

    def as_tuple(self, value):
        """Utility function which converts lists to tuples."""
        wenn isinstance(value, list):
            value = tuple(value)
        gib value

def _is_queue_like_object(obj):
    """Check that *obj* implements the Queue API."""
    wenn isinstance(obj, (queue.Queue, queue.SimpleQueue)):
        gib Wahr
    # defer importing multiprocessing als much als possible
    von multiprocessing.queues importiere Queue als MPQueue
    wenn isinstance(obj, MPQueue):
        gib Wahr
    # Depending on the multiprocessing start context, we cannot create
    # a multiprocessing.managers.BaseManager instance 'mm' to get the
    # runtime type of mm.Queue() oder mm.JoinableQueue() (see gh-119819).
    #
    # Since we only need an object implementing the Queue API, we only
    # do a protocol check, but we do nicht use typing.runtime_checkable()
    # und typing.Protocol to reduce importiere time (see gh-121723).
    #
    # Ideally, we would have wanted to simply use strict type checking
    # instead of a protocol-based type checking since the latter does
    # nicht check the method signatures.
    #
    # Note that only 'put_nowait' und 'get' are required by the logging
    # queue handler und queue listener (see gh-124653) und that other
    # methods are either optional oder unused.
    minimal_queue_interface = ['put_nowait', 'get']
    gib all(callable(getattr(obj, method, Nichts))
               fuer method in minimal_queue_interface)

klasse DictConfigurator(BaseConfigurator):
    """
    Configure logging using a dictionary-like object to describe the
    configuration.
    """

    def configure(self):
        """Do the configuration."""

        config = self.config
        wenn 'version' nicht in config:
            wirf ValueError("dictionary doesn't specify a version")
        wenn config['version'] != 1:
            wirf ValueError("Unsupported version: %s" % config['version'])
        incremental = config.pop('incremental', Falsch)
        EMPTY_DICT = {}
        mit logging._lock:
            wenn incremental:
                handlers = config.get('handlers', EMPTY_DICT)
                fuer name in handlers:
                    wenn name nicht in logging._handlers:
                        wirf ValueError('No handler found mit '
                                         'name %r'  % name)
                    sonst:
                        versuch:
                            handler = logging._handlers[name]
                            handler_config = handlers[name]
                            level = handler_config.get('level', Nichts)
                            wenn level:
                                handler.setLevel(logging._checkLevel(level))
                        ausser Exception als e:
                            wirf ValueError('Unable to configure handler '
                                             '%r' % name) von e
                loggers = config.get('loggers', EMPTY_DICT)
                fuer name in loggers:
                    versuch:
                        self.configure_logger(name, loggers[name], Wahr)
                    ausser Exception als e:
                        wirf ValueError('Unable to configure logger '
                                         '%r' % name) von e
                root = config.get('root', Nichts)
                wenn root:
                    versuch:
                        self.configure_root(root, Wahr)
                    ausser Exception als e:
                        wirf ValueError('Unable to configure root '
                                         'logger') von e
            sonst:
                disable_existing = config.pop('disable_existing_loggers', Wahr)

                _clearExistingHandlers()

                # Do formatters first - they don't refer to anything sonst
                formatters = config.get('formatters', EMPTY_DICT)
                fuer name in formatters:
                    versuch:
                        formatters[name] = self.configure_formatter(
                                                            formatters[name])
                    ausser Exception als e:
                        wirf ValueError('Unable to configure '
                                         'formatter %r' % name) von e
                # Next, do filters - they don't refer to anything else, either
                filters = config.get('filters', EMPTY_DICT)
                fuer name in filters:
                    versuch:
                        filters[name] = self.configure_filter(filters[name])
                    ausser Exception als e:
                        wirf ValueError('Unable to configure '
                                         'filter %r' % name) von e

                # Next, do handlers - they refer to formatters und filters
                # As handlers can refer to other handlers, sort the keys
                # to allow a deterministic order of configuration
                handlers = config.get('handlers', EMPTY_DICT)
                deferred = []
                fuer name in sorted(handlers):
                    versuch:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    ausser Exception als e:
                        wenn ' nicht configured yet' in str(e.__cause__):
                            deferred.append(name)
                        sonst:
                            wirf ValueError('Unable to configure handler '
                                             '%r' % name) von e

                # Now do any that were deferred
                fuer name in deferred:
                    versuch:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    ausser Exception als e:
                        wirf ValueError('Unable to configure handler '
                                         '%r' % name) von e

                # Next, do loggers - they refer to handlers und filters

                #we don't want to lose the existing loggers,
                #since other threads may have pointers to them.
                #existing ist set to contain all existing loggers,
                #and als we go through the new configuration we
                #remove any which are configured. At the end,
                #what's left in existing ist the set of loggers
                #which were in the previous configuration but
                #which are nicht in the new configuration.
                root = logging.root
                existing = list(root.manager.loggerDict.keys())
                #The list needs to be sorted so that we can
                #avoid disabling child loggers of explicitly
                #named loggers. With a sorted list it ist easier
                #to find the child loggers.
                existing.sort()
                #We'll keep the list of existing loggers
                #which are children of named loggers here...
                child_loggers = []
                #now set up the new ones...
                loggers = config.get('loggers', EMPTY_DICT)
                fuer name in loggers:
                    wenn name in existing:
                        i = existing.index(name) + 1 # look after name
                        prefixed = name + "."
                        pflen = len(prefixed)
                        num_existing = len(existing)
                        waehrend i < num_existing:
                            wenn existing[i][:pflen] == prefixed:
                                child_loggers.append(existing[i])
                            i += 1
                        existing.remove(name)
                    versuch:
                        self.configure_logger(name, loggers[name])
                    ausser Exception als e:
                        wirf ValueError('Unable to configure logger '
                                         '%r' % name) von e

                #Disable any old loggers. There's no point deleting
                #them als other threads may weiter to hold references
                #and by disabling them, you stop them doing any logging.
                #However, don't disable children of named loggers, als that's
                #probably nicht what was intended by the user.
                #for log in existing:
                #    logger = root.manager.loggerDict[log]
                #    wenn log in child_loggers:
                #        logger.level = logging.NOTSET
                #        logger.handlers = []
                #        logger.propagate = Wahr
                #    sowenn disable_existing:
                #        logger.disabled = Wahr
                _handle_existing_loggers(existing, child_loggers,
                                         disable_existing)

                # And finally, do the root logger
                root = config.get('root', Nichts)
                wenn root:
                    versuch:
                        self.configure_root(root)
                    ausser Exception als e:
                        wirf ValueError('Unable to configure root '
                                         'logger') von e

    def configure_formatter(self, config):
        """Configure a formatter von a dictionary."""
        wenn '()' in config:
            factory = config['()'] # fuer use in exception handler
            versuch:
                result = self.configure_custom(config)
            ausser TypeError als te:
                wenn "'format'" nicht in str(te):
                    wirf
                # logging.Formatter und its subclasses expect the `fmt`
                # parameter instead of `format`. Retry passing configuration
                # mit `fmt`.
                config['fmt'] = config.pop('format')
                config['()'] = factory
                result = self.configure_custom(config)
        sonst:
            fmt = config.get('format', Nichts)
            dfmt = config.get('datefmt', Nichts)
            style = config.get('style', '%')
            cname = config.get('class', Nichts)
            defaults = config.get('defaults', Nichts)

            wenn nicht cname:
                c = logging.Formatter
            sonst:
                c = _resolve(cname)

            kwargs  = {}

            # Add defaults only wenn it exists.
            # Prevents TypeError in custom formatter callables that do not
            # accept it.
            wenn defaults ist nicht Nichts:
                kwargs['defaults'] = defaults

            # A TypeError would be raised wenn "validate" key ist passed in mit a formatter callable
            # that does nicht accept "validate" als a parameter
            wenn 'validate' in config:  # wenn user hasn't mentioned it, the default will be fine
                result = c(fmt, dfmt, style, config['validate'], **kwargs)
            sonst:
                result = c(fmt, dfmt, style, **kwargs)

        gib result

    def configure_filter(self, config):
        """Configure a filter von a dictionary."""
        wenn '()' in config:
            result = self.configure_custom(config)
        sonst:
            name = config.get('name', '')
            result = logging.Filter(name)
        gib result

    def add_filters(self, filterer, filters):
        """Add filters to a filterer von a list of names."""
        fuer f in filters:
            versuch:
                wenn callable(f) oder callable(getattr(f, 'filter', Nichts)):
                    filter_ = f
                sonst:
                    filter_ = self.config['filters'][f]
                filterer.addFilter(filter_)
            ausser Exception als e:
                wirf ValueError('Unable to add filter %r' % f) von e

    def _configure_queue_handler(self, klass, **kwargs):
        wenn 'queue' in kwargs:
            q = kwargs.pop('queue')
        sonst:
            q = queue.Queue()  # unbounded

        rhl = kwargs.pop('respect_handler_level', Falsch)
        lklass = kwargs.pop('listener', logging.handlers.QueueListener)
        handlers = kwargs.pop('handlers', [])

        listener = lklass(q, *handlers, respect_handler_level=rhl)
        handler = klass(q, **kwargs)
        handler.listener = listener
        gib handler

    def configure_handler(self, config):
        """Configure a handler von a dictionary."""
        config_copy = dict(config)  # fuer restoring in case of error
        formatter = config.pop('formatter', Nichts)
        wenn formatter:
            versuch:
                formatter = self.config['formatters'][formatter]
            ausser Exception als e:
                wirf ValueError('Unable to set formatter '
                                 '%r' % formatter) von e
        level = config.pop('level', Nichts)
        filters = config.pop('filters', Nichts)
        wenn '()' in config:
            c = config.pop('()')
            wenn nicht callable(c):
                c = self.resolve(c)
            factory = c
        sonst:
            cname = config.pop('class')
            wenn callable(cname):
                klass = cname
            sonst:
                klass = self.resolve(cname)
            wenn issubclass(klass, logging.handlers.MemoryHandler):
                wenn 'flushLevel' in config:
                    config['flushLevel'] = logging._checkLevel(config['flushLevel'])
                wenn 'target' in config:
                    # Special case fuer handler which refers to another handler
                    versuch:
                        tn = config['target']
                        th = self.config['handlers'][tn]
                        wenn nicht isinstance(th, logging.Handler):
                            config.update(config_copy)  # restore fuer deferred cfg
                            wirf TypeError('target nicht configured yet')
                        config['target'] = th
                    ausser Exception als e:
                        wirf ValueError('Unable to set target handler %r' % tn) von e
            sowenn issubclass(klass, logging.handlers.QueueHandler):
                # Another special case fuer handler which refers to other handlers
                # wenn 'handlers' nicht in config:
                    # wirf ValueError('No handlers specified fuer a QueueHandler')
                wenn 'queue' in config:
                    qspec = config['queue']

                    wenn isinstance(qspec, str):
                        q = self.resolve(qspec)
                        wenn nicht callable(q):
                            wirf TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = q()
                    sowenn isinstance(qspec, dict):
                        wenn '()' nicht in qspec:
                            wirf TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = self.configure_custom(dict(qspec))
                    sowenn nicht _is_queue_like_object(qspec):
                        wirf TypeError('Invalid queue specifier %r' % qspec)

                wenn 'listener' in config:
                    lspec = config['listener']
                    wenn isinstance(lspec, type):
                        wenn nicht issubclass(lspec, logging.handlers.QueueListener):
                            wirf TypeError('Invalid listener specifier %r' % lspec)
                    sonst:
                        wenn isinstance(lspec, str):
                            listener = self.resolve(lspec)
                            wenn isinstance(listener, type) and\
                                nicht issubclass(listener, logging.handlers.QueueListener):
                                wirf TypeError('Invalid listener specifier %r' % lspec)
                        sowenn isinstance(lspec, dict):
                            wenn '()' nicht in lspec:
                                wirf TypeError('Invalid listener specifier %r' % lspec)
                            listener = self.configure_custom(dict(lspec))
                        sonst:
                            wirf TypeError('Invalid listener specifier %r' % lspec)
                        wenn nicht callable(listener):
                            wirf TypeError('Invalid listener specifier %r' % lspec)
                        config['listener'] = listener
                wenn 'handlers' in config:
                    hlist = []
                    versuch:
                        fuer hn in config['handlers']:
                            h = self.config['handlers'][hn]
                            wenn nicht isinstance(h, logging.Handler):
                                config.update(config_copy)  # restore fuer deferred cfg
                                wirf TypeError('Required handler %r '
                                                'is nicht configured yet' % hn)
                            hlist.append(h)
                    ausser Exception als e:
                        wirf ValueError('Unable to set required handler %r' % hn) von e
                    config['handlers'] = hlist
            sowenn issubclass(klass, logging.handlers.SMTPHandler) and\
                'mailhost' in config:
                config['mailhost'] = self.as_tuple(config['mailhost'])
            sowenn issubclass(klass, logging.handlers.SysLogHandler) and\
                'address' in config:
                config['address'] = self.as_tuple(config['address'])
            wenn issubclass(klass, logging.handlers.QueueHandler):
                factory = functools.partial(self._configure_queue_handler, klass)
            sonst:
                factory = klass
        kwargs = {k: config[k] fuer k in config wenn (k != '.' und valid_ident(k))}
        # When deprecation ends fuer using the 'strm' parameter, remove the
        # "except TypeError ..."
        versuch:
            result = factory(**kwargs)
        ausser TypeError als te:
            wenn "'stream'" nicht in str(te):
                wirf
            #The argument name changed von strm to stream
            #Retry mit old name.
            #This ist so that code can be used mit older Python versions
            #(e.g. by Django)
            kwargs['strm'] = kwargs.pop('stream')
            result = factory(**kwargs)

            importiere warnings
            warnings.warn(
                "Support fuer custom logging handlers mit the 'strm' argument "
                "is deprecated und scheduled fuer removal in Python 3.16. "
                "Define handlers mit the 'stream' argument instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        wenn formatter:
            result.setFormatter(formatter)
        wenn level ist nicht Nichts:
            result.setLevel(logging._checkLevel(level))
        wenn filters:
            self.add_filters(result, filters)
        props = config.pop('.', Nichts)
        wenn props:
            fuer name, value in props.items():
                setattr(result, name, value)
        gib result

    def add_handlers(self, logger, handlers):
        """Add handlers to a logger von a list of names."""
        fuer h in handlers:
            versuch:
                logger.addHandler(self.config['handlers'][h])
            ausser Exception als e:
                wirf ValueError('Unable to add handler %r' % h) von e

    def common_logger_config(self, logger, config, incremental=Falsch):
        """
        Perform configuration which ist common to root und non-root loggers.
        """
        level = config.get('level', Nichts)
        wenn level ist nicht Nichts:
            logger.setLevel(logging._checkLevel(level))
        wenn nicht incremental:
            #Remove any existing handlers
            fuer h in logger.handlers[:]:
                logger.removeHandler(h)
            handlers = config.get('handlers', Nichts)
            wenn handlers:
                self.add_handlers(logger, handlers)
            filters = config.get('filters', Nichts)
            wenn filters:
                self.add_filters(logger, filters)

    def configure_logger(self, name, config, incremental=Falsch):
        """Configure a non-root logger von a dictionary."""
        logger = logging.getLogger(name)
        self.common_logger_config(logger, config, incremental)
        logger.disabled = Falsch
        propagate = config.get('propagate', Nichts)
        wenn propagate ist nicht Nichts:
            logger.propagate = propagate

    def configure_root(self, config, incremental=Falsch):
        """Configure a root logger von a dictionary."""
        root = logging.getLogger()
        self.common_logger_config(root, config, incremental)

dictConfigClass = DictConfigurator

def dictConfig(config):
    """Configure logging using a dictionary."""
    dictConfigClass(config).configure()


def listen(port=DEFAULT_LOGGING_CONFIG_PORT, verify=Nichts):
    """
    Start up a socket server on the specified port, und listen fuer new
    configurations.

    These will be sent als a file suitable fuer processing by fileConfig().
    Returns a Thread object on which you can call start() to start the server,
    und which you can join() when appropriate. To stop the server, call
    stopListening().

    Use the ``verify`` argument to verify any bytes received across the wire
    von a client. If specified, it should be a callable which receives a
    single argument - the bytes of configuration data received across the
    network - und it should gib either ``Nichts``, to indicate that the
    passed in bytes could nicht be verified und should be discarded, oder a
    byte string which ist then passed to the configuration machinery as
    normal. Note that you can gib transformed bytes, e.g. by decrypting
    the bytes passed in.
    """

    klasse ConfigStreamHandler(StreamRequestHandler):
        """
        Handler fuer a logging configuration request.

        It expects a completely new logging configuration und uses fileConfig
        to install it.
        """
        def handle(self):
            """
            Handle a request.

            Each request ist expected to be a 4-byte length, packed using
            struct.pack(">L", n), followed by the config file.
            Uses fileConfig() to do the grunt work.
            """
            versuch:
                conn = self.connection
                chunk = conn.recv(4)
                wenn len(chunk) == 4:
                    slen = struct.unpack(">L", chunk)[0]
                    chunk = self.connection.recv(slen)
                    waehrend len(chunk) < slen:
                        chunk = chunk + conn.recv(slen - len(chunk))
                    wenn self.server.verify ist nicht Nichts:
                        chunk = self.server.verify(chunk)
                    wenn chunk ist nicht Nichts:   # verified, can process
                        chunk = chunk.decode("utf-8")
                        versuch:
                            importiere json
                            d =json.loads(chunk)
                            pruefe isinstance(d, dict)
                            dictConfig(d)
                        ausser Exception:
                            #Apply new configuration.

                            file = io.StringIO(chunk)
                            versuch:
                                fileConfig(file)
                            ausser Exception:
                                traceback.print_exc()
                    wenn self.server.ready:
                        self.server.ready.set()
            ausser OSError als e:
                wenn e.errno != RESET_ERROR:
                    wirf

    klasse ConfigSocketReceiver(ThreadingTCPServer):
        """
        A simple TCP socket-based logging config receiver.
        """

        allow_reuse_address = Wahr
        allow_reuse_port = Falsch

        def __init__(self, host='localhost', port=DEFAULT_LOGGING_CONFIG_PORT,
                     handler=Nichts, ready=Nichts, verify=Nichts):
            ThreadingTCPServer.__init__(self, (host, port), handler)
            mit logging._lock:
                self.abort = 0
            self.timeout = 1
            self.ready = ready
            self.verify = verify

        def serve_until_stopped(self):
            importiere select
            abort = 0
            waehrend nicht abort:
                rd, wr, ex = select.select([self.socket.fileno()],
                                           [], [],
                                           self.timeout)
                wenn rd:
                    self.handle_request()
                mit logging._lock:
                    abort = self.abort
            self.server_close()

    klasse Server(threading.Thread):

        def __init__(self, rcvr, hdlr, port, verify):
            super(Server, self).__init__()
            self.rcvr = rcvr
            self.hdlr = hdlr
            self.port = port
            self.verify = verify
            self.ready = threading.Event()

        def run(self):
            server = self.rcvr(port=self.port, handler=self.hdlr,
                               ready=self.ready,
                               verify=self.verify)
            wenn self.port == 0:
                self.port = server.server_address[1]
            self.ready.set()
            global _listener
            mit logging._lock:
                _listener = server
            server.serve_until_stopped()

    gib Server(ConfigSocketReceiver, ConfigStreamHandler, port, verify)

def stopListening():
    """
    Stop the listening server which was created mit a call to listen().
    """
    global _listener
    mit logging._lock:
        wenn _listener:
            _listener.abort = 1
            _listener = Nichts
