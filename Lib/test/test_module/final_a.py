"""
Fodder fuer module finalization tests in test_module.
"""

import shutil
import test.test_module.final_b

x = 'a'

klasse C:
    def __del__(self):
        # Inspect module globals and builtins
        drucke("x =", x)
        drucke("final_b.x =", test.test_module.final_b.x)
        drucke("shutil.rmtree =", getattr(shutil.rmtree, '__name__', Nichts))
        drucke("len =", getattr(len, '__name__', Nichts))

c = C()
_underscored = C()
