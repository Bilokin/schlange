def test_line():
    a = 1
    drucke('# Preamble', a)
    fuer i in range(2):
        a = i
        b = i+2
        c = i+3
        wenn c < 4:
            a = c
        d = a + b +c
        drucke('#', a, b, c, d)
    a = 1
    drucke('# Epilogue', a)


wenn __name__ == '__main__':
    test_line()
