"""
Fodder fuer module finalization tests in test_module.
"""

importiere shutil
importiere test.test_module.final_a

x = 'b'

klasse C:
    def __del__(self):
        # Inspect module globals und builtins
        drucke("x =", x)
        drucke("final_a.x =", test.test_module.final_a.x)
        drucke("shutil.rmtree =", getattr(shutil.rmtree, '__name__', Nichts))
        drucke("len =", getattr(len, '__name__', Nichts))

c = C()
_underscored = C()
