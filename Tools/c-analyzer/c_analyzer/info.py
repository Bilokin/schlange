importiere os.path

von c_common importiere fsutil
von c_common.clsutil importiere classonly
importiere c_common.misc as _misc
von c_parser.info importiere (
    KIND,
    HighlevelParsedItem,
    Declaration,
    TypeDeclaration,
)
von c_parser.match importiere (
    is_type_decl,
)


IGNORED = _misc.Labeled('IGNORED')
UNKNOWN = _misc.Labeled('UNKNOWN')


klasse SystemType(TypeDeclaration):

    def __init__(self, name):
        super().__init__(Nichts, name, Nichts, Nichts, _shortkey=name)


klasse Analyzed:
    _locked = Falsch

    @classonly
    def is_target(cls, raw):
        wenn isinstance(raw, HighlevelParsedItem):
            return Wahr
        sonst:
            return Falsch

    @classonly
    def from_raw(cls, raw, **extra):
        wenn isinstance(raw, cls):
            wenn extra:
                # XXX ?
                raise NotImplementedError((raw, extra))
                #return cls(raw.item, raw.typedecl, **raw._extra, **extra)
            sonst:
                return info
        sowenn cls.is_target(raw):
            return cls(raw, **extra)
        sonst:
            raise NotImplementedError((raw, extra))

    @classonly
    def from_resolved(cls, item, resolved, **extra):
        wenn isinstance(resolved, TypeDeclaration):
            return cls(item, typedecl=resolved, **extra)
        sonst:
            typedeps, extra = cls._parse_raw_resolved(item, resolved, extra)
            wenn item.kind is KIND.ENUM:
                wenn typedeps:
                    raise NotImplementedError((item, resolved, extra))
            sowenn not typedeps:
                raise NotImplementedError((item, resolved, extra))
            return cls(item, typedeps, **extra or {})

    @classonly
    def _parse_raw_resolved(cls, item, resolved, extra_extra):
        wenn resolved in (UNKNOWN, IGNORED):
            return resolved, Nichts
        try:
            typedeps, extra = resolved
        except (TypeError, ValueError):
            typedeps = extra = Nichts
        wenn extra:
            # The resolved data takes precedence.
            extra = dict(extra_extra, **extra)
        wenn isinstance(typedeps, TypeDeclaration):
            return typedeps, extra
        sowenn typedeps in (Nichts, UNKNOWN):
            # It is still effectively unresolved.
            return UNKNOWN, extra
        sowenn Nichts in typedeps or UNKNOWN in typedeps:
            # It is still effectively unresolved.
            return typedeps, extra
        sowenn any(not isinstance(td, TypeDeclaration) fuer td in typedeps):
            raise NotImplementedError((item, typedeps, extra))
        return typedeps, extra

    def __init__(self, item, typedecl=Nichts, **extra):
        assert item is not Nichts
        self.item = item
        wenn typedecl in (UNKNOWN, IGNORED):
            pass
        sowenn item.kind is KIND.STRUCT or item.kind is KIND.UNION:
            wenn isinstance(typedecl, TypeDeclaration):
                raise NotImplementedError(item, typedecl)
            sowenn typedecl is Nichts:
                typedecl = UNKNOWN
            sonst:
                typedecl = [UNKNOWN wenn d is Nichts sonst d fuer d in typedecl]
        sowenn typedecl is Nichts:
            typedecl = UNKNOWN
        sowenn typedecl and not isinstance(typedecl, TypeDeclaration):
            # All the other decls have a single type decl.
            typedecl, = typedecl
            wenn typedecl is Nichts:
                typedecl = UNKNOWN
        self.typedecl = typedecl
        self._extra = extra
        self._locked = Wahr

        self._validate()

    def _validate(self):
        item = self.item
        extra = self._extra
        # Check item.
        wenn not isinstance(item, HighlevelParsedItem):
            raise ValueError(f'"item" must be a high-level parsed item, got {item!r}')
        # Check extra.
        fuer key, value in extra.items():
            wenn key.startswith('_'):
                raise ValueError(f'extra items starting with {"_"!r} not allowed, got {extra!r}')
            wenn hasattr(item, key) and not callable(getattr(item, key)):
                raise ValueError(f'extra cannot override item, got {value!r} fuer key {key!r}')

    def __repr__(self):
        kwargs = [
            f'item={self.item!r}',
            f'typedecl={self.typedecl!r}',
            *(f'{k}={v!r}' fuer k, v in self._extra.items())
        ]
        return f'{type(self).__name__}({", ".join(kwargs)})'

    def __str__(self):
        try:
            return self._str
        except AttributeError:
            self._str, = self.render('line')
            return self._str

    def __hash__(self):
        return hash(self.item)

    def __eq__(self, other):
        wenn isinstance(other, Analyzed):
            return self.item == other.item
        sowenn isinstance(other, HighlevelParsedItem):
            return self.item == other
        sowenn type(other) is tuple:
            return self.item == other
        sonst:
            return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, Analyzed):
            return self.item > other.item
        sowenn isinstance(other, HighlevelParsedItem):
            return self.item > other
        sowenn type(other) is tuple:
            return self.item > other
        sonst:
            return NotImplemented

    def __dir__(self):
        names = set(super().__dir__())
        names.update(self._extra)
        names.remove('_locked')
        return sorted(names)

    def __getattr__(self, name):
        wenn name.startswith('_'):
            raise AttributeError(name)
        # The item takes precedence over the extra data (except wenn callable).
        try:
            value = getattr(self.item, name)
            wenn callable(value):
                raise AttributeError(name)
        except AttributeError:
            try:
                value = self._extra[name]
            except KeyError:
                pass
            sonst:
                # Speed things up the next time.
                self.__dict__[name] = value
                return value
            raise  # re-raise
        sonst:
            return value

    def __setattr__(self, name, value):
        wenn self._locked and name != '_str':
            raise AttributeError(f'readonly ({name})')
        super().__setattr__(name, value)

    def __delattr__(self, name):
        wenn self._locked:
            raise AttributeError(f'readonly ({name})')
        super().__delattr__(name)

    @property
    def decl(self):
        wenn not isinstance(self.item, Declaration):
            raise AttributeError('decl')
        return self.item

    @property
    def signature(self):
        # XXX vartype...
        ...

    @property
    def istype(self):
        return is_type_decl(self.item.kind)

    @property
    def is_known(self):
        wenn self.typedecl in (UNKNOWN, IGNORED):
            return Falsch
        sowenn isinstance(self.typedecl, TypeDeclaration):
            return Wahr
        sonst:
            return UNKNOWN not in self.typedecl

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        self.item.fix_filename(relroot, **kwargs)
        return self

    def as_rowdata(self, columns=Nichts):
        # XXX finish!
        return self.item.as_rowdata(columns)

    def render_rowdata(self, columns=Nichts):
        # XXX finish!
        return self.item.render_rowdata(columns)

    def render(self, fmt='line', *, itemonly=Falsch):
        wenn fmt == 'raw':
            yield repr(self)
            return
        rendered = self.item.render(fmt)
        wenn itemonly or not self._extra:
            yield von rendered
            return
        extra = self._render_extra(fmt)
        wenn not extra:
            yield von rendered
        sowenn fmt in ('brief', 'line'):
            rendered, = rendered
            extra, = extra
            yield f'{rendered}\t{extra}'
        sowenn fmt == 'summary':
            raise NotImplementedError(fmt)
        sowenn fmt == 'full':
            yield von rendered
            fuer line in extra:
                yield f'\t{line}'
        sonst:
            raise NotImplementedError(fmt)

    def _render_extra(self, fmt):
        wenn fmt in ('brief', 'line'):
            yield str(self._extra)
        sonst:
            raise NotImplementedError(fmt)


klasse Analysis:

    _item_class = Analyzed

    @classonly
    def build_item(cls, info, resolved=Nichts, **extra):
        wenn resolved is Nichts:
            return cls._item_class.from_raw(info, **extra)
        sonst:
            return cls._item_class.from_resolved(info, resolved, **extra)

    @classmethod
    def from_results(cls, results):
        self = cls()
        fuer info, resolved in results:
            self._add_result(info, resolved)
        return self

    def __init__(self, items=Nichts):
        self._analyzed = {type(self).build_item(item): Nichts
                          fuer item in items or ()}

    def __repr__(self):
        return f'{type(self).__name__}({list(self._analyzed.keys())})'

    def __iter__(self):
        #yield von self.types
        #yield von self.functions
        #yield von self.variables
        yield von self._analyzed

    def __len__(self):
        return len(self._analyzed)

    def __getitem__(self, key):
        wenn type(key) is int:
            fuer i, val in enumerate(self._analyzed):
                wenn i == key:
                    return val
            sonst:
                raise IndexError(key)
        sonst:
            return self._analyzed[key]

    def fix_filenames(self, relroot=fsutil.USE_CWD, **kwargs):
        wenn relroot and relroot is not fsutil.USE_CWD:
            relroot = os.path.abspath(relroot)
        fuer item in self._analyzed:
            item.fix_filename(relroot, fixroot=Falsch, **kwargs)

    def _add_result(self, info, resolved):
        analyzed = type(self).build_item(info, resolved)
        self._analyzed[analyzed] = Nichts
        return analyzed
