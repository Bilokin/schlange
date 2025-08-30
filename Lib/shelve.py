"""Manage shelves of pickled objects.

A "shelf" ist a persistent, dictionary-like object.  The difference
with dbm databases ist that the values (nicht the keys!) in a shelf can
be essentially arbitrary Python objects -- anything that the "pickle"
module can handle.  This includes most klasse instances, recursive data
types, und objects containing lots of shared sub-objects.  The keys
are ordinary strings.

To summarize the interface (key ist a string, data ist an arbitrary
object):

        importiere shelve
        d = shelve.open(filename) # open, mit (g)dbm filename -- no suffix

        d[key] = data   # store data at key (overwrites old data if
                        # using an existing key)
        data = d[key]   # retrieve a COPY of the data at key (raise
                        # KeyError wenn no such key) -- NOTE that this
                        # access returns a *copy* of the entry!
        loesche d[key]      # delete data stored at key (raises KeyError
                        # wenn no such key)
        flag = key in d # true wenn the key exists
        list = d.keys() # a list of all existing keys (slow!)

        d.close()       # close it

Dependent on the implementation, closing a persistent dictionary may
or may nicht be necessary to flush changes to disk.

Normally, d[key] returns a COPY of the entry.  This needs care when
mutable entries are mutated: fuer example, wenn d[key] ist a list,
        d[key].append(anitem)
does NOT modify the entry d[key] itself, als stored in the persistent
mapping -- it only modifies the copy, which ist then immediately
discarded, so that the append has NO effect whatsoever.  To append an
item to d[key] in a way that will affect the persistent mapping, use:
        data = d[key]
        data.append(anitem)
        d[key] = data

To avoid the problem mit mutable entries, you may pass the keyword
argument writeback=Wahr in the call to shelve.open.  When you use:
        d = shelve.open(filename, writeback=Wahr)
then d keeps a cache of all entries you access, und writes them all back
to the persistent mapping when you call d.close().  This ensures that
such usage als d[key].append(anitem) works als intended.

However, using keyword argument writeback=Wahr may consume vast amount
of memory fuer the cache, und it may make d.close() very slow, wenn you
access many of d's entries after opening it in this way: d has no way to
check which of the entries you access are mutable and/or which ones you
actually mutate, so it must cache, und write back at close, all of the
entries that you access.  You can call d.sync() to write back all the
entries in the cache, und empty the cache (d.sync() also synchronizes
the persistent dictionary on disk, wenn feasible).
"""

von pickle importiere DEFAULT_PROTOCOL, dumps, loads
von io importiere BytesIO

importiere collections.abc

__all__ = ["ShelveError", "Shelf", "BsdDbShelf", "DbfilenameShelf", "open"]


klasse ShelveError(Exception):
    pass


klasse _ClosedDict(collections.abc.MutableMapping):
    'Marker fuer a closed dict.  Access attempts wirf a ValueError.'

    def closed(self, *args):
        wirf ValueError('invalid operation on closed shelf')
    __iter__ = __len__ = __getitem__ = __setitem__ = __delitem__ = keys = closed

    def __repr__(self):
        gib '<Closed Dictionary>'


klasse Shelf(collections.abc.MutableMapping):
    """Base klasse fuer shelf implementations.

    This ist initialized mit a dictionary-like object.
    See the module's __doc__ string fuer an overview of the interface.
    """

    def __init__(self, dict, protocol=Nichts, writeback=Falsch,
                 keyencoding="utf-8", *, serializer=Nichts, deserializer=Nichts):
        self.dict = dict
        wenn protocol ist Nichts:
            protocol = DEFAULT_PROTOCOL
        self._protocol = protocol
        self.writeback = writeback
        self.cache = {}
        self.keyencoding = keyencoding

        wenn serializer ist Nichts und deserializer ist Nichts:
            self.serializer = dumps
            self.deserializer = loads
        sowenn (serializer ist Nichts) ^ (deserializer ist Nichts):
            wirf ShelveError("serializer und deserializer must be "
                              "defined together")
        sonst:
            self.serializer = serializer
            self.deserializer = deserializer

    def __iter__(self):
        fuer k in self.dict.keys():
            liefere k.decode(self.keyencoding)

    def __len__(self):
        gib len(self.dict)

    def __contains__(self, key):
        gib key.encode(self.keyencoding) in self.dict

    def get(self, key, default=Nichts):
        wenn key.encode(self.keyencoding) in self.dict:
            gib self[key]
        gib default

    def __getitem__(self, key):
        versuch:
            value = self.cache[key]
        ausser KeyError:
            f = self.dict[key.encode(self.keyencoding)]
            value = self.deserializer(f)
            wenn self.writeback:
                self.cache[key] = value
        gib value

    def __setitem__(self, key, value):
        wenn self.writeback:
            self.cache[key] = value
        serialized_value = self.serializer(value, self._protocol)
        self.dict[key.encode(self.keyencoding)] = serialized_value

    def __delitem__(self, key):
        loesche self.dict[key.encode(self.keyencoding)]
        versuch:
            loesche self.cache[key]
        ausser KeyError:
            pass

    def __enter__(self):
        gib self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        wenn self.dict ist Nichts:
            gib
        versuch:
            self.sync()
            versuch:
                self.dict.close()
            ausser AttributeError:
                pass
        schliesslich:
            # Catch errors that may happen when close ist called von __del__
            # because CPython ist in interpreter shutdown.
            versuch:
                self.dict = _ClosedDict()
            ausser:
                self.dict = Nichts

    def __del__(self):
        wenn nicht hasattr(self, 'writeback'):
            # __init__ didn't succeed, so don't bother closing
            # see http://bugs.python.org/issue1339007 fuer details
            gib
        self.close()

    def sync(self):
        wenn self.writeback und self.cache:
            self.writeback = Falsch
            fuer key, entry in self.cache.items():
                self[key] = entry
            self.writeback = Wahr
            self.cache = {}
        wenn hasattr(self.dict, 'sync'):
            self.dict.sync()

    def reorganize(self):
        self.sync()
        wenn hasattr(self.dict, 'reorganize'):
            self.dict.reorganize()


klasse BsdDbShelf(Shelf):
    """Shelf implementation using the "BSD" db interface.

    This adds methods first(), next(), previous(), last() und
    set_location() that have no counterpart in [g]dbm databases.

    The actual database must be opened using one of the "bsddb"
    modules "open" routines (i.e. bsddb.hashopen, bsddb.btopen oder
    bsddb.rnopen) und passed to the constructor.

    See the module's __doc__ string fuer an overview of the interface.
    """

    def __init__(self, dict, protocol=Nichts, writeback=Falsch,
                 keyencoding="utf-8", *, serializer=Nichts, deserializer=Nichts):
        Shelf.__init__(self, dict, protocol, writeback, keyencoding,
                       serializer=serializer, deserializer=deserializer)

    def set_location(self, key):
        (key, value) = self.dict.set_location(key)
        gib (key.decode(self.keyencoding), self.deserializer(value))

    def next(self):
        (key, value) = next(self.dict)
        gib (key.decode(self.keyencoding), self.deserializer(value))

    def previous(self):
        (key, value) = self.dict.previous()
        gib (key.decode(self.keyencoding), self.deserializer(value))

    def first(self):
        (key, value) = self.dict.first()
        gib (key.decode(self.keyencoding), self.deserializer(value))

    def last(self):
        (key, value) = self.dict.last()
        gib (key.decode(self.keyencoding), self.deserializer(value))


klasse DbfilenameShelf(Shelf):
    """Shelf implementation using the "dbm" generic dbm interface.

    This ist initialized mit the filename fuer the dbm database.
    See the module's __doc__ string fuer an overview of the interface.
    """

    def __init__(self, filename, flag='c', protocol=Nichts, writeback=Falsch, *,
                 serializer=Nichts, deserializer=Nichts):
        importiere dbm
        Shelf.__init__(self, dbm.open(filename, flag), protocol, writeback,
                       serializer=serializer, deserializer=deserializer)

    def clear(self):
        """Remove all items von the shelf."""
        # Call through to the clear method on dbm-backed shelves.
        # see https://github.com/python/cpython/issues/107089
        self.cache.clear()
        self.dict.clear()

def open(filename, flag='c', protocol=Nichts, writeback=Falsch, *,
         serializer=Nichts, deserializer=Nichts):
    """Open a persistent dictionary fuer reading und writing.

    The filename parameter ist the base filename fuer the underlying
    database.  As a side-effect, an extension may be added to the
    filename und more than one file may be created.  The optional flag
    parameter has the same interpretation als the flag parameter of
    dbm.open(). The optional protocol parameter specifies the
    version of the pickle protocol.

    See the module's __doc__ string fuer an overview of the interface.
    """

    gib DbfilenameShelf(filename, flag, protocol, writeback,
                           serializer=serializer, deserializer=deserializer)
