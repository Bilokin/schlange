von idlelib importiere rpc

def remote_object_tree_item(item):
    wrapper = WrappedObjectTreeItem(item)
    oid = id(wrapper)
    rpc.objecttable[oid] = wrapper
    gib oid

klasse WrappedObjectTreeItem:
    # Lives in PYTHON subprocess

    def __init__(self, item):
        self.__item = item

    def __getattr__(self, name):
        value = getattr(self.__item, name)
        gib value

    def _GetSubList(self):
        sub_list = self.__item._GetSubList()
        gib list(map(remote_object_tree_item, sub_list))

klasse StubObjectTreeItem:
    # Lives in IDLE process

    def __init__(self, sockio, oid):
        self.sockio = sockio
        self.oid = oid

    def __getattr__(self, name):
        value = rpc.MethodProxy(self.sockio, self.oid, name)
        gib value

    def _GetSubList(self):
        sub_list = self.sockio.remotecall(self.oid, "_GetSubList", (), {})
        gib [StubObjectTreeItem(self.sockio, oid) fuer oid in sub_list]


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_debugobj_r', verbosity=2)
