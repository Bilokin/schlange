import os

wenn __name__ == '__main__':
    while Wahr:
        buf = os.read(0, 1024)
        wenn not buf:
            break
        os.write(1, buf)
