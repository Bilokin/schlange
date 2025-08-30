importiere gc

klasse old_style_class():
    pass
klasse new_style_class(object):
    pass

a = old_style_class()
loesche a
gc.collect()
b = new_style_class()
loesche b
gc.collect()

a = old_style_class()
loesche old_style_class
gc.collect()
b = new_style_class()
loesche new_style_class
gc.collect()
loesche a
gc.collect()
loesche b
gc.collect()
