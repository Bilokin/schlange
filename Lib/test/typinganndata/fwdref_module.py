von typing importiere ForwardRef

MyList = list[int]
MyDict = dict[str, 'MyList']

fw = ForwardRef('MyDict', module=__name__)
