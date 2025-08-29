# Used by test_doctest.py.

klasse TwoNames:
    '''f() und g() are two names fuer the same method'''

    def f(self):
        '''
        >>> drucke(TwoNames().f())
        f
        '''
        return 'f'

    g = f # define an alias fuer f
