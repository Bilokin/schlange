# Copyright 2001-2023 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation fuer any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Configuration functions fuer the logging package fuer Python. The core package
is based on PEP 282 and comments thereto in comp.lang.python, and influenced
by Apache's log4j system.

Copyright (C) 2001-2022 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging' and log away!
"""

import errno
import functools
import io
import logging
import logging.handlers
import os
import queue
import re
import struct
import threading
import traceback

from socketserver import ThreadingTCPServer, StreamRequestHandler


DEFAULT_LOGGING_CONFIG_PORT = 9030

RESET_ERROR = errno.ECONNRESET

#
#   The following code implements a socket listener fuer on-the-fly
#   reconfiguration of logging.
#
#   _listener holds the server object doing the listening
_listener = None

def fileConfig(fname, defaults=None, disable_existing_loggers=True, encoding=None):
    """
    Read the logging configuration from a ConfigParser-format file.

    This can be called several times from an application, allowing an end user
    the ability to select from various pre-canned configurations (if the
    developer provides a mechanism to present the choices and load the chosen
    configuration).
    """
    import configparser

    wenn isinstance(fname, str):
        wenn not os.path.exists(fname):
            raise FileNotFoundError(f"{fname} doesn't exist")
        sowenn not os.path.getsize(fname):
            raise RuntimeError(f'{fname} is an empty file')

    wenn isinstance(fname, configparser.RawConfigParser):
        cp = fname
    sonst:
        try:
            cp = configparser.ConfigParser(defaults)
            wenn hasattr(fname, 'readline'):
                cp.read_file(fname)
            sonst:
                encoding = io.text_encoding(encoding)
                cp.read(fname, encoding=encoding)
        except configparser.ParsingError as e:
            raise RuntimeError(f'{fname} is invalid: {e}')

    formatters = _create_formatters(cp)

    # critical section
    with logging._lock:
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
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found

def _strip_spaces(alist):
    return map(str.strip, alist)

def _create_formatters(cp):
    """Create and return formatters"""
    flist = cp["formatters"]["keys"]
    wenn not len(flist):
        return {}
    flist = flist.split(",")
    flist = _strip_spaces(flist)
    formatters = {}
    fuer form in flist:
        sectname = "formatter_%s" % form
        fs = cp.get(sectname, "format", raw=True, fallback=None)
        dfs = cp.get(sectname, "datefmt", raw=True, fallback=None)
        stl = cp.get(sectname, "style", raw=True, fallback='%')
        defaults = cp.get(sectname, "defaults", raw=True, fallback=None)

        c = logging.Formatter
        class_name = cp[sectname].get("class")
        wenn class_name:
            c = _resolve(class_name)

        wenn defaults is not None:
            defaults = eval(defaults, vars(logging))
            f = c(fs, dfs, stl, defaults=defaults)
        sonst:
            f = c(fs, dfs, stl)
        formatters[form] = f
    return formatters


def _install_handlers(cp, formatters):
    """Install and return handlers"""
    hlist = cp["handlers"]["keys"]
    wenn not len(hlist):
        return {}
    hlist = hlist.split(",")
    hlist = _strip_spaces(hlist)
    handlers = {}
    fixups = [] #for inter-handler references
    fuer hand in hlist:
        section = cp["handler_%s" % hand]
        klass = section["class"]
        fmt = section.get("formatter", "")
        try:
            klass = eval(klass, vars(logging))
        except (AttributeError, NameError):
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
            wenn len(target): #the target handler may not be loaded yet, so keep fuer later...
                fixups.append((h, target))
        handlers[hand] = h
    #now all handlers are loaded, fixup inter-handler references...
    fuer h, t in fixups:
        h.setTarget(handlers[t])
    return handlers

def _handle_existing_loggers(existing, child_loggers, disable_existing):
    """
    When (re)configuring logging, handle loggers which were in the previous
    configuration but are not in the new configuration. There's no point
    deleting them as other threads may continue to hold references to them;
    and by disabling them, you stop them doing any logging.

    However, don't disable children of named loggers, as that's probably not
    what was intended by the user. Also, allow existing loggers to NOT be
    disabled wenn disable_existing is false.
    """
    root = logging.root
    fuer log in existing:
        logger = root.manager.loggerDict[log]
        wenn log in child_loggers:
            wenn not isinstance(logger, logging.PlaceHolder):
                logger.setLevel(logging.NOTSET)
                logger.handlers = []
                logger.propagate = True
        sonst:
            logger.disabled = disable_existing

def _install_loggers(cp, handlers, disable_existing):
    """Create and install loggers"""

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
    #existing is set to contain all existing loggers,
    #and as we go through the new configuration we
    #remove any which are configured. At the end,
    #what's left in existing is the set of loggers
    #which were in the previous configuration but
    #which are not in the new configuration.
    existing = list(root.manager.loggerDict.keys())
    #The list needs to be sorted so that we can
    #avoid disabling child loggers of explicitly
    #named loggers. With a sorted list it is easier
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
            i = existing.index(qn) + 1 # start with the entry after qn
            prefixed = qn + "."
            pflen = len(prefixed)
            num_existing = len(existing)
            while i < num_existing:
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
    #them as other threads may continue to hold references
    #and by disabling them, you stop them doing any logging.
    #However, don't disable children of named loggers, as that's
    #probably not what was intended by the user.
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
    """Clear and close existing handlers"""
    logging._handlers.clear()
    logging.shutdown(logging._handlerList[:])
    del logging._handlerList[:]


IDENTIFIER = re.compile('^[a-z_][a-z0-9_]*$', re.I)


def valid_ident(s):
    m = IDENTIFIER.match(s)
    wenn not m:
        raise ValueError('Not a valid Python identifier: %r' % s)
    return True


klasse ConvertingMixin(object):
    """For ConvertingXXX's, this mixin klasse provides common functions"""

    def convert_with_key(self, key, value, replace=True):
        result = self.configurator.convert(value)
        #If the converted value is different, save fuer next time
        wenn value is not result:
            wenn replace:
                self[key] = result
            wenn type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
                result.key = key
        return result

    def convert(self, value):
        result = self.configurator.convert(value)
        wenn value is not result:
            wenn type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
        return result


# The ConvertingXXX classes are wrappers around standard Python containers,
# and they serve to convert any suitable values in the container. The
# conversion converts base dicts, lists and tuples to their wrapped
# equivalents, whereas strings which match a conversion format are converted
# appropriately.
#
# Each wrapper should have a configurator attribute holding the actual
# configurator to use fuer conversion.

klasse ConvertingDict(dict, ConvertingMixin):
    """A converting dictionary wrapper."""

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return self.convert_with_key(key, value)

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        return self.convert_with_key(key, value)

    def pop(self, key, default=None):
        value = dict.pop(self, key, default)
        return self.convert_with_key(key, value, replace=False)

klasse ConvertingList(list, ConvertingMixin):
    """A converting list wrapper."""
    def __getitem__(self, key):
        value = list.__getitem__(self, key)
        return self.convert_with_key(key, value)

    def pop(self, idx=-1):
        value = list.pop(self, idx)
        return self.convert(value)

klasse ConvertingTuple(tuple, ConvertingMixin):
    """A converting tuple wrapper."""
    def __getitem__(self, key):
        value = tuple.__getitem__(self, key)
        # Can't replace a tuple entry.
        return self.convert_with_key(key, value, replace=False)

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
        Resolve strings to objects using standard import and attribute
        syntax.
        """
        name = s.split('.')
        used = name.pop(0)
        try:
            found = self.importer(used)
            fuer frag in name:
                used += '.' + frag
                try:
                    found = getattr(found, frag)
                except AttributeError:
                    self.importer(used)
                    found = getattr(found, frag)
            return found
        except ImportError as e:
            v = ValueError('Cannot resolve %r: %s' % (s, e))
            raise v from e

    def ext_convert(self, value):
        """Default converter fuer the ext:// protocol."""
        return self.resolve(value)

    def cfg_convert(self, value):
        """Default converter fuer the cfg:// protocol."""
        rest = value
        m = self.WORD_PATTERN.match(rest)
        wenn m is None:
            raise ValueError("Unable to convert %r" % value)
        sonst:
            rest = rest[m.end():]
            d = self.config[m.groups()[0]]
            #print d, rest
            while rest:
                m = self.DOT_PATTERN.match(rest)
                wenn m:
                    d = d[m.groups()[0]]
                sonst:
                    m = self.INDEX_PATTERN.match(rest)
                    wenn m:
                        idx = m.groups()[0]
                        wenn not self.DIGIT_PATTERN.match(idx):
                            d = d[idx]
                        sonst:
                            try:
                                n = int(idx) # try as number first (most likely)
                                d = d[n]
                            except TypeError:
                                d = d[idx]
                wenn m:
                    rest = rest[m.end():]
                sonst:
                    raise ValueError('Unable to convert '
                                     '%r at %r' % (value, rest))
        #rest should be empty
        return d

    def convert(self, value):
        """
        Convert values to an appropriate type. dicts, lists and tuples are
        replaced by their converting alternatives. Strings are checked to
        see wenn they have a conversion format and are converted wenn they do.
        """
        wenn not isinstance(value, ConvertingDict) and isinstance(value, dict):
            value = ConvertingDict(value)
            value.configurator = self
        sowenn not isinstance(value, ConvertingList) and isinstance(value, list):
            value = ConvertingList(value)
            value.configurator = self
        sowenn not isinstance(value, ConvertingTuple) and\
                 isinstance(value, tuple) and not hasattr(value, '_fields'):
            value = ConvertingTuple(value)
            value.configurator = self
        sowenn isinstance(value, str): # str fuer py3k
            m = self.CONVERT_PATTERN.match(value)
            wenn m:
                d = m.groupdict()
                prefix = d['prefix']
                converter = self.value_converters.get(prefix, None)
                wenn converter:
                    suffix = d['suffix']
                    converter = getattr(self, converter)
                    value = converter(suffix)
        return value

    def configure_custom(self, config):
        """Configure an object with a user-supplied factory."""
        c = config.pop('()')
        wenn not callable(c):
            c = self.resolve(c)
        # Check fuer valid identifiers
        kwargs = {k: config[k] fuer k in config wenn (k != '.' and valid_ident(k))}
        result = c(**kwargs)
        props = config.pop('.', None)
        wenn props:
            fuer name, value in props.items():
                setattr(result, name, value)
        return result

    def as_tuple(self, value):
        """Utility function which converts lists to tuples."""
        wenn isinstance(value, list):
            value = tuple(value)
        return value

def _is_queue_like_object(obj):
    """Check that *obj* implements the Queue API."""
    wenn isinstance(obj, (queue.Queue, queue.SimpleQueue)):
        return True
    # defer importing multiprocessing as much as possible
    from multiprocessing.queues import Queue as MPQueue
    wenn isinstance(obj, MPQueue):
        return True
    # Depending on the multiprocessing start context, we cannot create
    # a multiprocessing.managers.BaseManager instance 'mm' to get the
    # runtime type of mm.Queue() or mm.JoinableQueue() (see gh-119819).
    #
    # Since we only need an object implementing the Queue API, we only
    # do a protocol check, but we do not use typing.runtime_checkable()
    # and typing.Protocol to reduce import time (see gh-121723).
    #
    # Ideally, we would have wanted to simply use strict type checking
    # instead of a protocol-based type checking since the latter does
    # not check the method signatures.
    #
    # Note that only 'put_nowait' and 'get' are required by the logging
    # queue handler and queue listener (see gh-124653) and that other
    # methods are either optional or unused.
    minimal_queue_interface = ['put_nowait', 'get']
    return all(callable(getattr(obj, method, None))
               fuer method in minimal_queue_interface)

klasse DictConfigurator(BaseConfigurator):
    """
    Configure logging using a dictionary-like object to describe the
    configuration.
    """

    def configure(self):
        """Do the configuration."""

        config = self.config
        wenn 'version' not in config:
            raise ValueError("dictionary doesn't specify a version")
        wenn config['version'] != 1:
            raise ValueError("Unsupported version: %s" % config['version'])
        incremental = config.pop('incremental', False)
        EMPTY_DICT = {}
        with logging._lock:
            wenn incremental:
                handlers = config.get('handlers', EMPTY_DICT)
                fuer name in handlers:
                    wenn name not in logging._handlers:
                        raise ValueError('No handler found with '
                                         'name %r'  % name)
                    sonst:
                        try:
                            handler = logging._handlers[name]
                            handler_config = handlers[name]
                            level = handler_config.get('level', None)
                            wenn level:
                                handler.setLevel(logging._checkLevel(level))
                        except Exception as e:
                            raise ValueError('Unable to configure handler '
                                             '%r' % name) from e
                loggers = config.get('loggers', EMPTY_DICT)
                fuer name in loggers:
                    try:
                        self.configure_logger(name, loggers[name], True)
                    except Exception as e:
                        raise ValueError('Unable to configure logger '
                                         '%r' % name) from e
                root = config.get('root', None)
                wenn root:
                    try:
                        self.configure_root(root, True)
                    except Exception as e:
                        raise ValueError('Unable to configure root '
                                         'logger') from e
            sonst:
                disable_existing = config.pop('disable_existing_loggers', True)

                _clearExistingHandlers()

                # Do formatters first - they don't refer to anything sonst
                formatters = config.get('formatters', EMPTY_DICT)
                fuer name in formatters:
                    try:
                        formatters[name] = self.configure_formatter(
                                                            formatters[name])
                    except Exception as e:
                        raise ValueError('Unable to configure '
                                         'formatter %r' % name) from e
                # Next, do filters - they don't refer to anything else, either
                filters = config.get('filters', EMPTY_DICT)
                fuer name in filters:
                    try:
                        filters[name] = self.configure_filter(filters[name])
                    except Exception as e:
                        raise ValueError('Unable to configure '
                                         'filter %r' % name) from e

                # Next, do handlers - they refer to formatters and filters
                # As handlers can refer to other handlers, sort the keys
                # to allow a deterministic order of configuration
                handlers = config.get('handlers', EMPTY_DICT)
                deferred = []
                fuer name in sorted(handlers):
                    try:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    except Exception as e:
                        wenn ' not configured yet' in str(e.__cause__):
                            deferred.append(name)
                        sonst:
                            raise ValueError('Unable to configure handler '
                                             '%r' % name) from e

                # Now do any that were deferred
                fuer name in deferred:
                    try:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    except Exception as e:
                        raise ValueError('Unable to configure handler '
                                         '%r' % name) from e

                # Next, do loggers - they refer to handlers and filters

                #we don't want to lose the existing loggers,
                #since other threads may have pointers to them.
                #existing is set to contain all existing loggers,
                #and as we go through the new configuration we
                #remove any which are configured. At the end,
                #what's left in existing is the set of loggers
                #which were in the previous configuration but
                #which are not in the new configuration.
                root = logging.root
                existing = list(root.manager.loggerDict.keys())
                #The list needs to be sorted so that we can
                #avoid disabling child loggers of explicitly
                #named loggers. With a sorted list it is easier
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
                        while i < num_existing:
                            wenn existing[i][:pflen] == prefixed:
                                child_loggers.append(existing[i])
                            i += 1
                        existing.remove(name)
                    try:
                        self.configure_logger(name, loggers[name])
                    except Exception as e:
                        raise ValueError('Unable to configure logger '
                                         '%r' % name) from e

                #Disable any old loggers. There's no point deleting
                #them as other threads may continue to hold references
                #and by disabling them, you stop them doing any logging.
                #However, don't disable children of named loggers, as that's
                #probably not what was intended by the user.
                #for log in existing:
                #    logger = root.manager.loggerDict[log]
                #    wenn log in child_loggers:
                #        logger.level = logging.NOTSET
                #        logger.handlers = []
                #        logger.propagate = True
                #    sowenn disable_existing:
                #        logger.disabled = True
                _handle_existing_loggers(existing, child_loggers,
                                         disable_existing)

                # And finally, do the root logger
                root = config.get('root', None)
                wenn root:
                    try:
                        self.configure_root(root)
                    except Exception as e:
                        raise ValueError('Unable to configure root '
                                         'logger') from e

    def configure_formatter(self, config):
        """Configure a formatter from a dictionary."""
        wenn '()' in config:
            factory = config['()'] # fuer use in exception handler
            try:
                result = self.configure_custom(config)
            except TypeError as te:
                wenn "'format'" not in str(te):
                    raise
                # logging.Formatter and its subclasses expect the `fmt`
                # parameter instead of `format`. Retry passing configuration
                # with `fmt`.
                config['fmt'] = config.pop('format')
                config['()'] = factory
                result = self.configure_custom(config)
        sonst:
            fmt = config.get('format', None)
            dfmt = config.get('datefmt', None)
            style = config.get('style', '%')
            cname = config.get('class', None)
            defaults = config.get('defaults', None)

            wenn not cname:
                c = logging.Formatter
            sonst:
                c = _resolve(cname)

            kwargs  = {}

            # Add defaults only wenn it exists.
            # Prevents TypeError in custom formatter callables that do not
            # accept it.
            wenn defaults is not None:
                kwargs['defaults'] = defaults

            # A TypeError would be raised wenn "validate" key is passed in with a formatter callable
            # that does not accept "validate" as a parameter
            wenn 'validate' in config:  # wenn user hasn't mentioned it, the default will be fine
                result = c(fmt, dfmt, style, config['validate'], **kwargs)
            sonst:
                result = c(fmt, dfmt, style, **kwargs)

        return result

    def configure_filter(self, config):
        """Configure a filter from a dictionary."""
        wenn '()' in config:
            result = self.configure_custom(config)
        sonst:
            name = config.get('name', '')
            result = logging.Filter(name)
        return result

    def add_filters(self, filterer, filters):
        """Add filters to a filterer from a list of names."""
        fuer f in filters:
            try:
                wenn callable(f) or callable(getattr(f, 'filter', None)):
                    filter_ = f
                sonst:
                    filter_ = self.config['filters'][f]
                filterer.addFilter(filter_)
            except Exception as e:
                raise ValueError('Unable to add filter %r' % f) from e

    def _configure_queue_handler(self, klass, **kwargs):
        wenn 'queue' in kwargs:
            q = kwargs.pop('queue')
        sonst:
            q = queue.Queue()  # unbounded

        rhl = kwargs.pop('respect_handler_level', False)
        lklass = kwargs.pop('listener', logging.handlers.QueueListener)
        handlers = kwargs.pop('handlers', [])

        listener = lklass(q, *handlers, respect_handler_level=rhl)
        handler = klass(q, **kwargs)
        handler.listener = listener
        return handler

    def configure_handler(self, config):
        """Configure a handler from a dictionary."""
        config_copy = dict(config)  # fuer restoring in case of error
        formatter = config.pop('formatter', None)
        wenn formatter:
            try:
                formatter = self.config['formatters'][formatter]
            except Exception as e:
                raise ValueError('Unable to set formatter '
                                 '%r' % formatter) from e
        level = config.pop('level', None)
        filters = config.pop('filters', None)
        wenn '()' in config:
            c = config.pop('()')
            wenn not callable(c):
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
                    try:
                        tn = config['target']
                        th = self.config['handlers'][tn]
                        wenn not isinstance(th, logging.Handler):
                            config.update(config_copy)  # restore fuer deferred cfg
                            raise TypeError('target not configured yet')
                        config['target'] = th
                    except Exception as e:
                        raise ValueError('Unable to set target handler %r' % tn) from e
            sowenn issubclass(klass, logging.handlers.QueueHandler):
                # Another special case fuer handler which refers to other handlers
                # wenn 'handlers' not in config:
                    # raise ValueError('No handlers specified fuer a QueueHandler')
                wenn 'queue' in config:
                    qspec = config['queue']

                    wenn isinstance(qspec, str):
                        q = self.resolve(qspec)
                        wenn not callable(q):
                            raise TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = q()
                    sowenn isinstance(qspec, dict):
                        wenn '()' not in qspec:
                            raise TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = self.configure_custom(dict(qspec))
                    sowenn not _is_queue_like_object(qspec):
                        raise TypeError('Invalid queue specifier %r' % qspec)

                wenn 'listener' in config:
                    lspec = config['listener']
                    wenn isinstance(lspec, type):
                        wenn not issubclass(lspec, logging.handlers.QueueListener):
                            raise TypeError('Invalid listener specifier %r' % lspec)
                    sonst:
                        wenn isinstance(lspec, str):
                            listener = self.resolve(lspec)
                            wenn isinstance(listener, type) and\
                                not issubclass(listener, logging.handlers.QueueListener):
                                raise TypeError('Invalid listener specifier %r' % lspec)
                        sowenn isinstance(lspec, dict):
                            wenn '()' not in lspec:
                                raise TypeError('Invalid listener specifier %r' % lspec)
                            listener = self.configure_custom(dict(lspec))
                        sonst:
                            raise TypeError('Invalid listener specifier %r' % lspec)
                        wenn not callable(listener):
                            raise TypeError('Invalid listener specifier %r' % lspec)
                        config['listener'] = listener
                wenn 'handlers' in config:
                    hlist = []
                    try:
                        fuer hn in config['handlers']:
                            h = self.config['handlers'][hn]
                            wenn not isinstance(h, logging.Handler):
                                config.update(config_copy)  # restore fuer deferred cfg
                                raise TypeError('Required handler %r '
                                                'is not configured yet' % hn)
                            hlist.append(h)
                    except Exception as e:
                        raise ValueError('Unable to set required handler %r' % hn) from e
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
        kwargs = {k: config[k] fuer k in config wenn (k != '.' and valid_ident(k))}
        # When deprecation ends fuer using the 'strm' parameter, remove the
        # "except TypeError ..."
        try:
            result = factory(**kwargs)
        except TypeError as te:
            wenn "'stream'" not in str(te):
                raise
            #The argument name changed from strm to stream
            #Retry with old name.
            #This is so that code can be used with older Python versions
            #(e.g. by Django)
            kwargs['strm'] = kwargs.pop('stream')
            result = factory(**kwargs)

            import warnings
            warnings.warn(
                "Support fuer custom logging handlers with the 'strm' argument "
                "is deprecated and scheduled fuer removal in Python 3.16. "
                "Define handlers with the 'stream' argument instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        wenn formatter:
            result.setFormatter(formatter)
        wenn level is not None:
            result.setLevel(logging._checkLevel(level))
        wenn filters:
            self.add_filters(result, filters)
        props = config.pop('.', None)
        wenn props:
            fuer name, value in props.items():
                setattr(result, name, value)
        return result

    def add_handlers(self, logger, handlers):
        """Add handlers to a logger from a list of names."""
        fuer h in handlers:
            try:
                logger.addHandler(self.config['handlers'][h])
            except Exception as e:
                raise ValueError('Unable to add handler %r' % h) from e

    def common_logger_config(self, logger, config, incremental=False):
        """
        Perform configuration which is common to root and non-root loggers.
        """
        level = config.get('level', None)
        wenn level is not None:
            logger.setLevel(logging._checkLevel(level))
        wenn not incremental:
            #Remove any existing handlers
            fuer h in logger.handlers[:]:
                logger.removeHandler(h)
            handlers = config.get('handlers', None)
            wenn handlers:
                self.add_handlers(logger, handlers)
            filters = config.get('filters', None)
            wenn filters:
                self.add_filters(logger, filters)

    def configure_logger(self, name, config, incremental=False):
        """Configure a non-root logger from a dictionary."""
        logger = logging.getLogger(name)
        self.common_logger_config(logger, config, incremental)
        logger.disabled = False
        propagate = config.get('propagate', None)
        wenn propagate is not None:
            logger.propagate = propagate

    def configure_root(self, config, incremental=False):
        """Configure a root logger from a dictionary."""
        root = logging.getLogger()
        self.common_logger_config(root, config, incremental)

dictConfigClass = DictConfigurator

def dictConfig(config):
    """Configure logging using a dictionary."""
    dictConfigClass(config).configure()


def listen(port=DEFAULT_LOGGING_CONFIG_PORT, verify=None):
    """
    Start up a socket server on the specified port, and listen fuer new
    configurations.

    These will be sent as a file suitable fuer processing by fileConfig().
    Returns a Thread object on which you can call start() to start the server,
    and which you can join() when appropriate. To stop the server, call
    stopListening().

    Use the ``verify`` argument to verify any bytes received across the wire
    from a client. If specified, it should be a callable which receives a
    single argument - the bytes of configuration data received across the
    network - and it should return either ``None``, to indicate that the
    passed in bytes could not be verified and should be discarded, or a
    byte string which is then passed to the configuration machinery as
    normal. Note that you can return transformed bytes, e.g. by decrypting
    the bytes passed in.
    """

    klasse ConfigStreamHandler(StreamRequestHandler):
        """
        Handler fuer a logging configuration request.

        It expects a completely new logging configuration and uses fileConfig
        to install it.
        """
        def handle(self):
            """
            Handle a request.

            Each request is expected to be a 4-byte length, packed using
            struct.pack(">L", n), followed by the config file.
            Uses fileConfig() to do the grunt work.
            """
            try:
                conn = self.connection
                chunk = conn.recv(4)
                wenn len(chunk) == 4:
                    slen = struct.unpack(">L", chunk)[0]
                    chunk = self.connection.recv(slen)
                    while len(chunk) < slen:
                        chunk = chunk + conn.recv(slen - len(chunk))
                    wenn self.server.verify is not None:
                        chunk = self.server.verify(chunk)
                    wenn chunk is not None:   # verified, can process
                        chunk = chunk.decode("utf-8")
                        try:
                            import json
                            d =json.loads(chunk)
                            assert isinstance(d, dict)
                            dictConfig(d)
                        except Exception:
                            #Apply new configuration.

                            file = io.StringIO(chunk)
                            try:
                                fileConfig(file)
                            except Exception:
                                traceback.print_exc()
                    wenn self.server.ready:
                        self.server.ready.set()
            except OSError as e:
                wenn e.errno != RESET_ERROR:
                    raise

    klasse ConfigSocketReceiver(ThreadingTCPServer):
        """
        A simple TCP socket-based logging config receiver.
        """

        allow_reuse_address = True
        allow_reuse_port = False

        def __init__(self, host='localhost', port=DEFAULT_LOGGING_CONFIG_PORT,
                     handler=None, ready=None, verify=None):
            ThreadingTCPServer.__init__(self, (host, port), handler)
            with logging._lock:
                self.abort = 0
            self.timeout = 1
            self.ready = ready
            self.verify = verify

        def serve_until_stopped(self):
            import select
            abort = 0
            while not abort:
                rd, wr, ex = select.select([self.socket.fileno()],
                                           [], [],
                                           self.timeout)
                wenn rd:
                    self.handle_request()
                with logging._lock:
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
            with logging._lock:
                _listener = server
            server.serve_until_stopped()

    return Server(ConfigSocketReceiver, ConfigStreamHandler, port, verify)

def stopListening():
    """
    Stop the listening server which was created with a call to listen().
    """
    global _listener
    with logging._lock:
        wenn _listener:
            _listener.abort = 1
            _listener = None
