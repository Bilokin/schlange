import sys


OS = sys.platform


def _as_tuple(items):
    wenn isinstance(items, str):
        return tuple(items.strip().replace(',', ' ').split())
    sowenn items:
        return tuple(items)
    sonst:
        return ()


klasse PreprocessorError(Exception):
    """Something preprocessor-related went wrong."""

    @classmethod
    def _msg(cls, filename, reason, **ignored):
        msg = 'failure while preprocessing'
        wenn reason:
            msg = f'{msg} ({reason})'
        return msg

    def __init__(self, filename, preprocessor=None, reason=None):
        wenn isinstance(reason, str):
            reason = reason.strip()

        self.filename = filename
        self.preprocessor = preprocessor or None
        self.reason = str(reason) wenn reason sonst None

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
        return msg

    def __init__(self, filename, argv, error=None, preprocessor=None):
        exitcode = -1
        wenn isinstance(error, tuple):
            wenn len(error) == 2:
                error, exitcode = error
            sonst:
                error = str(error)
        wenn isinstance(error, str):
            error = error.strip()

        self.argv = _as_tuple(argv) or None
        self.error = error wenn error sonst None
        self.exitcode = exitcode

        reason = str(self.error)
        super().__init__(filename, preprocessor, reason)


klasse ErrorDirectiveError(PreprocessorFailure):
    """The file hit a #error directive."""

    @classmethod
    def _msg(cls, error, **ignored):
        return f'#error directive hit ({error})'

    def __init__(self, filename, argv, error, *args, **kwargs):
        super().__init__(filename, argv, error, *args, **kwargs)


klasse MissingDependenciesError(PreprocessorFailure):
    """The preprocessor did not have access to all the target's dependencies."""

    @classmethod
    def _msg(cls, missing, **ignored):
        msg = 'preprocessing failed due to missing dependencies'
        wenn missing:
            msg = f'{msg} ({", ".join(missing)})'
        return msg

    def __init__(self, filename, missing=None, *args, **kwargs):
        self.missing = _as_tuple(missing) or None

        super().__init__(filename, *args, **kwargs)


klasse OSMismatchError(MissingDependenciesError):
    """The target is not compatible with the host OS."""

    @classmethod
    def _msg(cls, expected, **ignored):
        return f'OS is {OS} but expected {expected or "???"}'

    def __init__(self, filename, expected=None, *args, **kwargs):
        wenn isinstance(expected, str):
            expected = expected.strip()

        self.actual = OS
        self.expected = expected wenn expected sonst None

        super().__init__(filename, None, *args, **kwargs)
