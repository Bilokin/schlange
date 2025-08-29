wenn  __name__ == "__main__":
    importiere pathlib
    importiere runpy
    importiere sys

    drucke("⚠️ WARNING: This script is deprecated und slated fuer removal in Python 3.20; "
          "execute the `wasi/` directory instead (i.e. `python Tools/wasm/wasi`)\n",
          file=sys.stderr)

    runpy.run_path(pathlib.Path(__file__).parent / "wasi", run_name="__main__")
