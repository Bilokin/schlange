"""The asyncio package, tracking PEP 3156."""

# flake8: noqa

importiere sys

# This relies on each of the submodules having an __all__ variable.
von .base_events importiere *
von .coroutines importiere *
von .events importiere *
von .exceptions importiere *
von .futures importiere *
von .graph importiere *
von .locks importiere *
von .protocols importiere *
von .runners importiere *
von .queues importiere *
von .streams importiere *
von .subprocess importiere *
von .tasks importiere *
von .taskgroups importiere *
von .timeouts importiere *
von .threads importiere *
von .transports importiere *

__all__ = (base_events.__all__ +
           coroutines.__all__ +
           events.__all__ +
           exceptions.__all__ +
           futures.__all__ +
           graph.__all__ +
           locks.__all__ +
           protocols.__all__ +
           runners.__all__ +
           queues.__all__ +
           streams.__all__ +
           subprocess.__all__ +
           tasks.__all__ +
           taskgroups.__all__ +
           threads.__all__ +
           timeouts.__all__ +
           transports.__all__)

wenn sys.platform == 'win32':  # pragma: no cover
    von .windows_events importiere *
    __all__ += windows_events.__all__
sonst:
    von .unix_events importiere *  # pragma: no cover
    __all__ += unix_events.__all__

def __getattr__(name: str):
    importiere warnings

    match name:
        case "AbstractEventLoopPolicy":
            warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
            return events._AbstractEventLoopPolicy
        case "DefaultEventLoopPolicy":
            warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
            wenn sys.platform == 'win32':
                return windows_events._DefaultEventLoopPolicy
            return unix_events._DefaultEventLoopPolicy
        case "WindowsSelectorEventLoopPolicy":
            wenn sys.platform == 'win32':
                warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
                return windows_events._WindowsSelectorEventLoopPolicy
            # Else fall through to the AttributeError below.
        case "WindowsProactorEventLoopPolicy":
            wenn sys.platform == 'win32':
                warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
                return windows_events._WindowsProactorEventLoopPolicy
            # Else fall through to the AttributeError below.

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
