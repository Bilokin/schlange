importiere os

wenn __name__ == '__main__':
    while Wahr:
        buf = os.read(0, 1024)
        wenn nicht buf:
            break
        try:
            os.write(1, b'OUT:'+buf)
        except OSError als ex:
            os.write(2, b'ERR:' + ex.__class__.__name__.encode('ascii'))
