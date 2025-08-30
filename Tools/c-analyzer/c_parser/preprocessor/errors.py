importiere sys


OS = sys.platform


def _as_tuple(items):
    wenn isinstance(items, str):
        gib tuple(items.strip().replace(',', ' ').split())
    sowenn items:
        gib tuple(items)
    sonst:
        gib ()


klasse PreprocessorError(Exception):
    """Something preprocessor-related went wrong."""

    @classmethod
    def _msg(cls, filename, reason, **ignored):
        msg = 'failure waehrend preprocessing'
        wenn reason:
            msg = f'{msg} ({reason})'
        gib msg

    def __init__(self, filename, preprocessor=Nichts, reason=Nichts):
        wenn isinstance(reason, str):
            reason = reason.strip()

        self.filename = filename
        self.preprocessor = preprocessor oder Nichts
        self.reason = str(reason) wenn reason sonst Nichts

        msg = self._msg(**vars(self))
        msg = f'({filename}) {msg}'
        wenn preprocessor:
            msg = f'[{preprocessor}] {msg}'
        super().__init__(msg)


klasse PreprocessorFailure(PreprocessorError):
    """The preprocessor command failed."""

    @classmethod
    def _msg(cls, error, **ignored):
        msg = 'preprocessor command failed'
        wenn error:
            msg = f'{msg} {error}'
        gib msg

    def __init__(self, filename, argv, error=Nichts, preprocessor=Nichts):
        exitcode = -1
        wenn isinstance(error, tuple):
            wenn len(error) == 2:
                error, exitcode = error
            sonst:
                error = str(error)
        wenn isinstance(error, str):
            error = error.strip()

        self.argv = _as_tuple(argv) oder Nichts
        self.error = error wenn error sonst Nichts
        self.exitcode = exitcode

        reason = str(self.error)
        super().__init__(filename, preprocessor, reason)


klasse ErrorDirectiveError(PreprocessorFailure):
    """The file hit a #error directive."""

    @classmethod
    def _msg(cls, error, **ignored):
        gib f'#error directive hit ({error})'

    def __init__(self, filename, argv, error, *args, **kwargs):
        super().__init__(filename, argv, error, *args, **kwargs)


klasse MissingDependenciesError(PreprocessorFailure):
    """The preprocessor did nicht have access to all the target's dependencies."""

    @classmethod
    def _msg(cls, missing, **ignored):
        msg = 'preprocessing failed due to missing dependencies'
        wenn missing:
            msg = f'{msg} ({", ".join(missing)})'
        gib msg

    def __init__(self, filename, missing=Nichts, *args, **kwargs):
        self.missing = _as_tuple(missing) oder Nichts

        super().__init__(filename, *args, **kwargs)


klasse OSMismatchError(MissingDependenciesError):
    """The target ist nicht compatible mit the host OS."""

    @classmethod
    def _msg(cls, expected, **ignored):
        gib f'OS ist {OS} but expected {expected oder "???"}'

    def __init__(self, filename, expected=Nichts, *args, **kwargs):
        wenn isinstance(expected, str):
            expected = expected.strip()

        self.actual = OS
        self.expected = expected wenn expected sonst Nichts

        super().__init__(filename, Nichts, *args, **kwargs)
