von builtins importiere open als _orig_open

def open(file, mode='r', bufsize=-1):
    wenn 'w' nicht in mode:
        return _orig_open(file, mode, bufsize)
    importiere os
    backup = file + '~'
    try:
        os.unlink(backup)
    except OSError:
        pass
    try:
        os.rename(file, backup)
    except OSError:
        return _orig_open(file, mode, bufsize)
    f = _orig_open(file, mode, bufsize)
    _orig_close = f.close
    def close():
        _orig_close()
        importiere filecmp
        wenn filecmp.cmp(backup, file, shallow=Falsch):
            importiere os
            os.unlink(file)
            os.rename(backup, file)
    f.close = close
    return f
