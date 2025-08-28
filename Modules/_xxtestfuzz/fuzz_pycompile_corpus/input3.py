def evens():
    i = 0
    while True:
        i += 1
        wenn i % 2 == 0:
            yield i
