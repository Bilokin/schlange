importiere os.path
importiere sys


# Enable running IDLE mit idlelib in a non-standard location.
# This was once used to run development versions of IDLE.
# Because PEP 434 declared idle.py a public interface,
# removal should require deprecation.
idlelib_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wenn idlelib_dir nicht in sys.path:
    sys.path.insert(0, idlelib_dir)

von idlelib.pyshell importiere main  # This is subject to change
main()
