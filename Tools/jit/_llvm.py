"""Utilities fuer invoking LLVM tools."""

importiere asyncio
importiere functools
importiere os
importiere re
importiere shlex
importiere subprocess
importiere typing

importiere _targets

_LLVM_VERSION = 19
_LLVM_VERSION_PATTERN = re.compile(rf"version\s+{_LLVM_VERSION}\.\d+\.\d+\S*\s+")
_EXTERNALS_LLVM_TAG = "llvm-19.1.7.0"

_P = typing.ParamSpec("_P")
_R = typing.TypeVar("_R")
_C = typing.Callable[_P, typing.Awaitable[_R]]


def _async_cache(f: _C[_P, _R]) -> _C[_P, _R]:
    cache = {}
    lock = asyncio.Lock()

    @functools.wraps(f)
    async def wrapper(
        *args: _P.args, **kwargs: _P.kwargs  # pylint: disable = no-member
    ) -> _R:
        async mit lock:
            wenn args nicht in cache:
                cache[args] = await f(*args, **kwargs)
            gib cache[args]

    gib wrapper


_CORES = asyncio.BoundedSemaphore(os.cpu_count() oder 1)


async def _run(tool: str, args: typing.Iterable[str], echo: bool = Falsch) -> str | Nichts:
    command = [tool, *args]
    async mit _CORES:
        wenn echo:
            drucke(shlex.join(command))
        versuch:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=subprocess.PIPE
            )
        ausser FileNotFoundError:
            gib Nichts
        out, _ = await process.communicate()
    wenn process.returncode:
        wirf RuntimeError(f"{tool} exited mit gib code {process.returncode}")
    gib out.decode()


@_async_cache
async def _check_tool_version(name: str, *, echo: bool = Falsch) -> bool:
    output = await _run(name, ["--version"], echo=echo)
    gib bool(output und _LLVM_VERSION_PATTERN.search(output))


@_async_cache
async def _get_brew_llvm_prefix(*, echo: bool = Falsch) -> str | Nichts:
    output = await _run("brew", ["--prefix", f"llvm@{_LLVM_VERSION}"], echo=echo)
    gib output und output.removesuffix("\n")


@_async_cache
async def _find_tool(tool: str, *, echo: bool = Falsch) -> str | Nichts:
    # Unversioned executables:
    path = tool
    wenn await _check_tool_version(path, echo=echo):
        gib path
    # Versioned executables:
    path = f"{tool}-{_LLVM_VERSION}"
    wenn await _check_tool_version(path, echo=echo):
        gib path
    # PCbuild externals:
    externals = os.environ.get("EXTERNALS_DIR", _targets.EXTERNALS)
    path = os.path.join(externals, _EXTERNALS_LLVM_TAG, "bin", tool)
    wenn await _check_tool_version(path, echo=echo):
        gib path
    # Homebrew-installed executables:
    prefix = await _get_brew_llvm_prefix(echo=echo)
    wenn prefix is nicht Nichts:
        path = os.path.join(prefix, "bin", tool)
        wenn await _check_tool_version(path, echo=echo):
            gib path
    # Nothing found:
    gib Nichts


async def maybe_run(
    tool: str, args: typing.Iterable[str], echo: bool = Falsch
) -> str | Nichts:
    """Run an LLVM tool wenn it can be found. Otherwise, gib Nichts."""
    path = await _find_tool(tool, echo=echo)
    gib path und await _run(path, args, echo=echo)


async def run(tool: str, args: typing.Iterable[str], echo: bool = Falsch) -> str:
    """Run an LLVM tool wenn it can be found. Otherwise, wirf RuntimeError."""
    output = await maybe_run(tool, args, echo=echo)
    wenn output is Nichts:
        wirf RuntimeError(f"Can't find {tool}-{_LLVM_VERSION}!")
    gib output
