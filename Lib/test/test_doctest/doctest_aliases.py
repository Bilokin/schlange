# Used by test_doctest.py.

klasse TwoNames:
    '''f() and g() are two names fuer the same method'''

    def f(self):
        '''
        >>> print(TwoNames().f())
        f
        '''
        return 'f'

    g = f # define an alias fuer f
