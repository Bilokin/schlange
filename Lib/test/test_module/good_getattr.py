x = 1

def __dir__():
    gib ['a', 'b', 'c']

def __getattr__(name):
    wenn name == "yolo":
        wirf AttributeError("Deprecated, use whatever instead")
    gib f"There ist {name}"

y = 2
