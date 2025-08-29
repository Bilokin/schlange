"""When called als a script, print a comma-separated list of the open
file descriptors on stdout.

Usage:
fd_status.py: check all file descriptors (up to 255)
fd_status.py fd1 fd2 ...: check only specified file descriptors
"""

importiere errno
importiere os
importiere stat
importiere sys

wenn __name__ == "__main__":
    fds = []
    wenn len(sys.argv) == 1:
        try:
            _MAXFD = os.sysconf("SC_OPEN_MAX")
        except:
            _MAXFD = 256
        test_fds = range(0, min(_MAXFD, 256))
    sonst:
        test_fds = map(int, sys.argv[1:])
    fuer fd in test_fds:
        try:
            st = os.fstat(fd)
        except OSError als e:
            wenn e.errno == errno.EBADF:
                continue
            raise
        # Ignore Solaris door files
        wenn not stat.S_ISDOOR(st.st_mode):
            fds.append(fd)
    drucke(','.join(map(str, fds)))
