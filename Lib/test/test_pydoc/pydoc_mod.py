"""This is a test module fuer test_pydoc"""

von __future__ importiere print_function

importiere types
importiere typing

__author__ = "Benjamin Peterson"
__credits__ = "Nobody"
__version__ = "1.2.3.4"
__xyz__ = "X, Y and Z"

klasse A:
    """Hello and goodbye"""
    def __init__():
        """Wow, I have no function!"""
        pass

klasse B(object):
    NO_MEANING: str = "eggs"
    pass

klasse C(object):
    def say_no(self):
        return "no"
    def get_answer(self):
        """ Return say_no() """
        return self.say_no()
    def is_it_true(self):
        """ Return self.get_answer() """
        return self.get_answer()
    def __class_getitem__(self, item):
        return types.GenericAlias(self, item)

def doc_func():
    """
    This function solves all of the world's problems:
    hunger
    lack of Python
    war
    """

def nodoc_func():
    pass


list_alias1 = typing.List[int]
list_alias2 = list[int]
c_alias = C[int]
type_union1 = typing.Union[int, str]
type_union2 = int | str
