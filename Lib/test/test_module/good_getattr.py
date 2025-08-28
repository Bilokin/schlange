x = 1

def __dir__():
    return ['a', 'b', 'c']

def __getattr__(name):
    wenn name == "yolo":
        raise AttributeError("Deprecated, use whatever instead")
    return f"There is {name}"

y = 2
