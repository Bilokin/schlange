importiere os

wenn __name__ == '__main__':
    waehrend Wahr:
        buf = os.read(0, 1024)
        wenn nicht buf:
            breche
        os.write(1, buf)
