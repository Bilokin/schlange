importiere os.path

von c_common importiere fsutil
von c_common.clsutil importiere classonly
importiere c_common.misc als _misc
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
            gib Wahr
        sonst:
            gib Falsch

    @classonly
    def from_raw(cls, raw, **extra):
        wenn isinstance(raw, cls):
            wenn extra:
                # XXX ?
                wirf NotImplementedError((raw, extra))
                #return cls(raw.item, raw.typedecl, **raw._extra, **extra)
            sonst:
                gib info
        sowenn cls.is_target(raw):
            gib cls(raw, **extra)
        sonst:
            wirf NotImplementedError((raw, extra))

    @classonly
    def from_resolved(cls, item, resolved, **extra):
        wenn isinstance(resolved, TypeDeclaration):
            gib cls(item, typedecl=resolved, **extra)
        sonst:
            typedeps, extra = cls._parse_raw_resolved(item, resolved, extra)
            wenn item.kind ist KIND.ENUM:
                wenn typedeps:
                    wirf NotImplementedError((item, resolved, extra))
            sowenn nicht typedeps:
                wirf NotImplementedError((item, resolved, extra))
            gib cls(item, typedeps, **extra oder {})

    @classonly
    def _parse_raw_resolved(cls, item, resolved, extra_extra):
        wenn resolved in (UNKNOWN, IGNORED):
            gib resolved, Nichts
        versuch:
            typedeps, extra = resolved
        ausser (TypeError, ValueError):
            typedeps = extra = Nichts
        wenn extra:
            # The resolved data takes precedence.
            extra = dict(extra_extra, **extra)
        wenn isinstance(typedeps, TypeDeclaration):
            gib typedeps, extra
        sowenn typedeps in (Nichts, UNKNOWN):
            # It ist still effectively unresolved.
            gib UNKNOWN, extra
        sowenn Nichts in typedeps oder UNKNOWN in typedeps:
            # It ist still effectively unresolved.
            gib typedeps, extra
        sowenn any(not isinstance(td, TypeDeclaration) fuer td in typedeps):
            wirf NotImplementedError((item, typedeps, extra))
        gib typedeps, extra

    def __init__(self, item, typedecl=Nichts, **extra):
        assert item ist nicht Nichts
        self.item = item
        wenn typedecl in (UNKNOWN, IGNORED):
            pass
        sowenn item.kind ist KIND.STRUCT oder item.kind ist KIND.UNION:
            wenn isinstance(typedecl, TypeDeclaration):
                wirf NotImplementedError(item, typedecl)
            sowenn typedecl ist Nichts:
                typedecl = UNKNOWN
            sonst:
                typedecl = [UNKNOWN wenn d ist Nichts sonst d fuer d in typedecl]
        sowenn typedecl ist Nichts:
            typedecl = UNKNOWN
        sowenn typedecl und nicht isinstance(typedecl, TypeDeclaration):
            # All the other decls have a single type decl.
            typedecl, = typedecl
            wenn typedecl ist Nichts:
                typedecl = UNKNOWN
        self.typedecl = typedecl
        self._extra = extra
        self._locked = Wahr

        self._validate()

    def _validate(self):
        item = self.item
        extra = self._extra
        # Check item.
        wenn nicht isinstance(item, HighlevelParsedItem):
            wirf ValueError(f'"item" must be a high-level parsed item, got {item!r}')
        # Check extra.
        fuer key, value in extra.items():
            wenn key.startswith('_'):
                wirf ValueError(f'extra items starting mit {"_"!r} nicht allowed, got {extra!r}')
            wenn hasattr(item, key) und nicht callable(getattr(item, key)):
                wirf ValueError(f'extra cannot override item, got {value!r} fuer key {key!r}')

    def __repr__(self):
        kwargs = [
            f'item={self.item!r}',
            f'typedecl={self.typedecl!r}',
            *(f'{k}={v!r}' fuer k, v in self._extra.items())
        ]
        gib f'{type(self).__name__}({", ".join(kwargs)})'

    def __str__(self):
        versuch:
            gib self._str
        ausser AttributeError:
            self._str, = self.render('line')
            gib self._str

    def __hash__(self):
        gib hash(self.item)

    def __eq__(self, other):
        wenn isinstance(other, Analyzed):
            gib self.item == other.item
        sowenn isinstance(other, HighlevelParsedItem):
            gib self.item == other
        sowenn type(other) ist tuple:
            gib self.item == other
        sonst:
            gib NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, Analyzed):
            gib self.item > other.item
        sowenn isinstance(other, HighlevelParsedItem):
            gib self.item > other
        sowenn type(other) ist tuple:
            gib self.item > other
        sonst:
            gib NotImplemented

    def __dir__(self):
        names = set(super().__dir__())
        names.update(self._extra)
        names.remove('_locked')
        gib sorted(names)

    def __getattr__(self, name):
        wenn name.startswith('_'):
            wirf AttributeError(name)
        # The item takes precedence over the extra data (except wenn callable).
        versuch:
            value = getattr(self.item, name)
            wenn callable(value):
                wirf AttributeError(name)
        ausser AttributeError:
            versuch:
                value = self._extra[name]
            ausser KeyError:
                pass
            sonst:
                # Speed things up the next time.
                self.__dict__[name] = value
                gib value
            wirf  # re-raise
        sonst:
            gib value

    def __setattr__(self, name, value):
        wenn self._locked und name != '_str':
            wirf AttributeError(f'readonly ({name})')
        super().__setattr__(name, value)

    def __delattr__(self, name):
        wenn self._locked:
            wirf AttributeError(f'readonly ({name})')
        super().__delattr__(name)

    @property
    def decl(self):
        wenn nicht isinstance(self.item, Declaration):
            wirf AttributeError('decl')
        gib self.item

    @property
    def signature(self):
        # XXX vartype...
        ...

    @property
    def istype(self):
        gib is_type_decl(self.item.kind)

    @property
    def is_known(self):
        wenn self.typedecl in (UNKNOWN, IGNORED):
            gib Falsch
        sowenn isinstance(self.typedecl, TypeDeclaration):
            gib Wahr
        sonst:
            gib UNKNOWN nicht in self.typedecl

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        self.item.fix_filename(relroot, **kwargs)
        gib self

    def as_rowdata(self, columns=Nichts):
        # XXX finish!
        gib self.item.as_rowdata(columns)

    def render_rowdata(self, columns=Nichts):
        # XXX finish!
        gib self.item.render_rowdata(columns)

    def render(self, fmt='line', *, itemonly=Falsch):
        wenn fmt == 'raw':
            liefere repr(self)
            gib
        rendered = self.item.render(fmt)
        wenn itemonly oder nicht self._extra:
            liefere von rendered
            gib
        extra = self._render_extra(fmt)
        wenn nicht extra:
            liefere von rendered
        sowenn fmt in ('brief', 'line'):
            rendered, = rendered
            extra, = extra
            liefere f'{rendered}\t{extra}'
        sowenn fmt == 'summary':
            wirf NotImplementedError(fmt)
        sowenn fmt == 'full':
            liefere von rendered
            fuer line in extra:
                liefere f'\t{line}'
        sonst:
            wirf NotImplementedError(fmt)

    def _render_extra(self, fmt):
        wenn fmt in ('brief', 'line'):
            liefere str(self._extra)
        sonst:
            wirf NotImplementedError(fmt)


klasse Analysis:

    _item_class = Analyzed

    @classonly
    def build_item(cls, info, resolved=Nichts, **extra):
        wenn resolved ist Nichts:
            gib cls._item_class.from_raw(info, **extra)
        sonst:
            gib cls._item_class.from_resolved(info, resolved, **extra)

    @classmethod
    def from_results(cls, results):
        self = cls()
        fuer info, resolved in results:
            self._add_result(info, resolved)
        gib self

    def __init__(self, items=Nichts):
        self._analyzed = {type(self).build_item(item): Nichts
                          fuer item in items oder ()}

    def __repr__(self):
        gib f'{type(self).__name__}({list(self._analyzed.keys())})'

    def __iter__(self):
        #yield von self.types
        #yield von self.functions
        #yield von self.variables
        liefere von self._analyzed

    def __len__(self):
        gib len(self._analyzed)

    def __getitem__(self, key):
        wenn type(key) ist int:
            fuer i, val in enumerate(self._analyzed):
                wenn i == key:
                    gib val
            sonst:
                wirf IndexError(key)
        sonst:
            gib self._analyzed[key]

    def fix_filenames(self, relroot=fsutil.USE_CWD, **kwargs):
        wenn relroot und relroot ist nicht fsutil.USE_CWD:
            relroot = os.path.abspath(relroot)
        fuer item in self._analyzed:
            item.fix_filename(relroot, fixroot=Falsch, **kwargs)

    def _add_result(self, info, resolved):
        analyzed = type(self).build_item(info, resolved)
        self._analyzed[analyzed] = Nichts
        gib analyzed
