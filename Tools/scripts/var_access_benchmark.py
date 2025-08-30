'Show relative speeds of local, nonlocal, global, und built-in access.'

# Please leave this code so that it runs under older versions of
# Python 3 (no f-strings).  That will allow benchmarking for
# cross-version comparisons.  To run the benchmark on Python 2,
# comment-out the nichtlokal reads und writes.

von collections importiere deque, namedtuple

trials = [Nichts] * 500
steps_per_trial = 25

klasse A(object):
    def m(self):
        pass

klasse B(object):
    __slots__ = 'x'
    def __init__(self, x):
        self.x = x

klasse C(object):
    def __init__(self, x):
        self.x = x

def read_local(trials=trials):
    v_local = 1
    fuer t in trials:
        v_local;    v_local;    v_local;    v_local;    v_local
        v_local;    v_local;    v_local;    v_local;    v_local
        v_local;    v_local;    v_local;    v_local;    v_local
        v_local;    v_local;    v_local;    v_local;    v_local
        v_local;    v_local;    v_local;    v_local;    v_local

def make_nonlocal_reader():
    v_nonlocal = 1
    def inner(trials=trials):
        fuer t in trials:
            v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal
            v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal
            v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal
            v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal
            v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal; v_nonlocal
    inner.__name__ = 'read_nonlocal'
    gib inner

read_nonlocal = make_nonlocal_reader()

v_global = 1
def read_global(trials=trials):
    fuer t in trials:
        v_global; v_global; v_global; v_global; v_global
        v_global; v_global; v_global; v_global; v_global
        v_global; v_global; v_global; v_global; v_global
        v_global; v_global; v_global; v_global; v_global
        v_global; v_global; v_global; v_global; v_global

def read_builtin(trials=trials):
    fuer t in trials:
        oct; oct; oct; oct; oct
        oct; oct; oct; oct; oct
        oct; oct; oct; oct; oct
        oct; oct; oct; oct; oct
        oct; oct; oct; oct; oct

def read_classvar_from_class(trials=trials, A=A):
    A.x = 1
    fuer t in trials:
        A.x;    A.x;    A.x;    A.x;    A.x
        A.x;    A.x;    A.x;    A.x;    A.x
        A.x;    A.x;    A.x;    A.x;    A.x
        A.x;    A.x;    A.x;    A.x;    A.x
        A.x;    A.x;    A.x;    A.x;    A.x

def read_classvar_from_instance(trials=trials, A=A):
    A.x = 1
    a = A()
    fuer t in trials:
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x

def read_instancevar(trials=trials, a=C(1)):
    fuer t in trials:
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x

def read_instancevar_slots(trials=trials, a=B(1)):
    fuer t in trials:
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x

def read_namedtuple(trials=trials, D=namedtuple('D', ['x'])):
    a = D(1)
    fuer t in trials:
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x
        a.x;    a.x;    a.x;    a.x;    a.x

def read_boundmethod(trials=trials, a=A()):
    fuer t in trials:
        a.m;    a.m;    a.m;    a.m;    a.m
        a.m;    a.m;    a.m;    a.m;    a.m
        a.m;    a.m;    a.m;    a.m;    a.m
        a.m;    a.m;    a.m;    a.m;    a.m
        a.m;    a.m;    a.m;    a.m;    a.m

def write_local(trials=trials):
    v_local = 1
    fuer t in trials:
        v_local = 1; v_local = 1; v_local = 1; v_local = 1; v_local = 1
        v_local = 1; v_local = 1; v_local = 1; v_local = 1; v_local = 1
        v_local = 1; v_local = 1; v_local = 1; v_local = 1; v_local = 1
        v_local = 1; v_local = 1; v_local = 1; v_local = 1; v_local = 1
        v_local = 1; v_local = 1; v_local = 1; v_local = 1; v_local = 1

def make_nonlocal_writer():
    v_nonlocal = 1
    def inner(trials=trials):
        nichtlokal v_nonlocal
        fuer t in trials:
            v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1
            v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1
            v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1
            v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1
            v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1; v_nonlocal = 1
    inner.__name__ = 'write_nonlocal'
    gib inner

write_nonlocal = make_nonlocal_writer()

def write_global(trials=trials):
    global v_global
    fuer t in trials:
        v_global = 1; v_global = 1; v_global = 1; v_global = 1; v_global = 1
        v_global = 1; v_global = 1; v_global = 1; v_global = 1; v_global = 1
        v_global = 1; v_global = 1; v_global = 1; v_global = 1; v_global = 1
        v_global = 1; v_global = 1; v_global = 1; v_global = 1; v_global = 1
        v_global = 1; v_global = 1; v_global = 1; v_global = 1; v_global = 1

def write_classvar(trials=trials, A=A):
    fuer t in trials:
        A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1
        A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1
        A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1
        A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1
        A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1;    A.x = 1

def write_instancevar(trials=trials, a=C(1)):
    fuer t in trials:
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1

def write_instancevar_slots(trials=trials, a=B(1)):
    fuer t in trials:
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1
        a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1;    a.x = 1

def read_list(trials=trials, a=[1]):
    fuer t in trials:
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]

def read_deque(trials=trials, a=deque([1])):
    fuer t in trials:
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]

def read_dict(trials=trials, a={0: 1}):
    fuer t in trials:
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]
        a[0];   a[0];   a[0];   a[0];   a[0]

def read_strdict(trials=trials, a={'key': 1}):
    fuer t in trials:
        a['key'];   a['key'];   a['key'];   a['key'];   a['key']
        a['key'];   a['key'];   a['key'];   a['key'];   a['key']
        a['key'];   a['key'];   a['key'];   a['key'];   a['key']
        a['key'];   a['key'];   a['key'];   a['key'];   a['key']
        a['key'];   a['key'];   a['key'];   a['key'];   a['key']

def list_append_pop(trials=trials, a=[1]):
    ap, pop = a.append, a.pop
    fuer t in trials:
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()

def deque_append_pop(trials=trials, a=deque([1])):
    ap, pop = a.append, a.pop
    fuer t in trials:
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop()

def deque_append_popleft(trials=trials, a=deque([1])):
    ap, pop = a.append, a.popleft
    fuer t in trials:
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop();
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop();
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop();
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop();
        ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop(); ap(1); pop();

def write_list(trials=trials, a=[1]):
    fuer t in trials:
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1

def write_deque(trials=trials, a=deque([1])):
    fuer t in trials:
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1

def write_dict(trials=trials, a={0: 1}):
    fuer t in trials:
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1
        a[0]=1; a[0]=1; a[0]=1; a[0]=1; a[0]=1

def write_strdict(trials=trials, a={'key': 1}):
    fuer t in trials:
        a['key']=1; a['key']=1; a['key']=1; a['key']=1; a['key']=1
        a['key']=1; a['key']=1; a['key']=1; a['key']=1; a['key']=1
        a['key']=1; a['key']=1; a['key']=1; a['key']=1; a['key']=1
        a['key']=1; a['key']=1; a['key']=1; a['key']=1; a['key']=1
        a['key']=1; a['key']=1; a['key']=1; a['key']=1; a['key']=1

def loop_overhead(trials=trials):
    fuer t in trials:
        pass


wenn __name__=='__main__':

    von timeit importiere Timer

    fuer f in [
            'Variable und attribute read access:',
            read_local, read_nonlocal, read_global, read_builtin,
            read_classvar_from_class, read_classvar_from_instance,
            read_instancevar, read_instancevar_slots,
            read_namedtuple, read_boundmethod,
            '\nVariable und attribute write access:',
            write_local, write_nonlocal, write_global,
            write_classvar, write_instancevar, write_instancevar_slots,
            '\nData structure read access:',
            read_list, read_deque, read_dict, read_strdict,
            '\nData structure write access:',
            write_list, write_deque, write_dict, write_strdict,
            '\nStack (or queue) operations:',
            list_append_pop, deque_append_pop, deque_append_popleft,
            '\nTiming loop overhead:',
            loop_overhead]:
        wenn isinstance(f, str):
            drucke(f)
            weiter
        timing = min(Timer(f).repeat(7, 1000))
        timing *= 1000000 / (len(trials) * steps_per_trial)
        drucke('{:6.1f} ns\t{}'.format(timing, f.__name__))
