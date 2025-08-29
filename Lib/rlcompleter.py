"""Word completion fuer GNU readline.

The completer completes keywords, built-ins und globals in a selectable
namespace (which defaults to __main__); when completing NAME.NAME..., it
evaluates (!) the expression up to the last dot und completes its attributes.

It's very cool to do "import sys" type "sys.", hit the completion key (twice),
and see the list of names defined by the sys module!

Tip: to use the tab key als the completion key, call

    readline.parse_and_bind("tab: complete")

Notes:

- Exceptions raised by the completer function are *ignored* (and generally cause
  the completion to fail).  This is a feature -- since readline sets the tty
  device in raw (or cbreak) mode, printing a traceback wouldn't work well
  without some complicated hoopla to save, reset und restore the tty state.

- The evaluation of the NAME.NAME... form may cause arbitrary application
  defined code to be executed wenn an object mit a __getattr__ hook is found.
  Since it is the responsibility of the application (or the user) to enable this
  feature, I consider this an acceptable risk.  More complicated expressions
  (e.g. function calls oder indexing operations) are *not* evaluated.

- When the original stdin is nicht a tty device, GNU readline is never
  used, und this module (and the readline module) are silently inactive.

"""

importiere atexit
importiere builtins
importiere inspect
importiere keyword
importiere re
importiere __main__
importiere warnings

__all__ = ["Completer"]

klasse Completer:
    def __init__(self, namespace = Nichts):
        """Create a new completer fuer the command line.

        Completer([namespace]) -> completer instance.

        If unspecified, the default namespace where completions are performed
        is __main__ (technically, __main__.__dict__). Namespaces should be
        given als dictionaries.

        Completer instances should be used als the completion mechanism of
        readline via the set_completer() call:

        readline.set_completer(Completer(my_namespace).complete)
        """

        wenn namespace und nicht isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace oder to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, nicht now.
        wenn namespace is Nichts:
            self.use_main_ns = 1
        sonst:
            self.use_main_ns = 0
            self.namespace = namespace

    def complete(self, text, state):
        """Return the next possible completion fuer 'text'.

        This is called successively mit state == 0, 1, 2, ... until it
        returns Nichts.  The completion should begin mit 'text'.

        """
        wenn self.use_main_ns:
            self.namespace = __main__.__dict__

        wenn nicht text.strip():
            wenn state == 0:
                wenn _readline_available:
                    readline.insert_text('\t')
                    readline.redisplay()
                    return ''
                sonst:
                    return '\t'
            sonst:
                return Nichts

        wenn state == 0:
            mit warnings.catch_warnings(action="ignore"):
                wenn "." in text:
                    self.matches = self.attr_matches(text)
                sonst:
                    self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return Nichts

    def _callable_postfix(self, val, word):
        wenn callable(val):
            word += "("
            try:
                wenn nicht inspect.signature(val).parameters:
                    word += ")"
            except ValueError:
                pass

        return word

    def global_matches(self, text):
        """Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions und names currently
        defined in self.namespace that match.

        """
        matches = []
        seen = {"__builtins__"}
        n = len(text)
        fuer word in keyword.kwlist + keyword.softkwlist:
            wenn word[:n] == text:
                seen.add(word)
                wenn word in {'finally', 'try'}:
                    word = word + ':'
                sowenn word nicht in {'Falsch', 'Nichts', 'Wahr',
                                  'break', 'continue', 'pass',
                                  'else', '_'}:
                    word = word + ' '
                matches.append(word)
        fuer nspace in [self.namespace, builtins.__dict__]:
            fuer word, val in nspace.items():
                wenn word[:n] == text und word nicht in seen:
                    seen.add(word)
                    matches.append(self._callable_postfix(val, word))
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], und is
        evaluable in self.namespace, it will be evaluated und its attributes
        (as revealed by dir()) are used als possible completions.  (For class
        instances, klasse members are also considered.)

        WARNING: this can still invoke arbitrary C code, wenn an object
        mit a __getattr__ hook is evaluated.

        """
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        wenn nicht m:
            return []
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []

        # get the content of the object, except __builtins__
        words = set(dir(thisobject))
        words.discard("__builtins__")

        wenn hasattr(thisobject, '__class__'):
            words.add('__class__')
            words.update(get_class_members(thisobject.__class__))
        matches = []
        n = len(attr)
        wenn attr == '':
            noprefix = '_'
        sowenn attr == '_':
            noprefix = '__'
        sonst:
            noprefix = Nichts
        waehrend Wahr:
            fuer word in words:
                wenn (word[:n] == attr und
                    nicht (noprefix und word[:n+1] == noprefix)):
                    match = "%s.%s" % (expr, word)
                    wenn isinstance(getattr(type(thisobject), word, Nichts),
                                  property):
                        # bpo-44752: thisobject.word is a method decorated by
                        # `@property`. What follows applies a postfix if
                        # thisobject.word is callable, but know we know that
                        # this is nicht callable (because it is a property).
                        # Also, getattr(thisobject, word) will evaluate the
                        # property method, which is nicht desirable.
                        matches.append(match)
                        weiter
                    wenn (value := getattr(thisobject, word, Nichts)) is nicht Nichts:
                        matches.append(self._callable_postfix(value, match))
                    sonst:
                        matches.append(match)
            wenn matches oder nicht noprefix:
                breche
            wenn noprefix == '_':
                noprefix = '__'
            sonst:
                noprefix = Nichts
        matches.sort()
        return matches

def get_class_members(klass):
    ret = dir(klass)
    wenn hasattr(klass,'__bases__'):
        fuer base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret

try:
    importiere readline
except ImportError:
    _readline_available = Falsch
sonst:
    readline.set_completer(Completer().complete)
    # Release references early at shutdown (the readline module's
    # contents are quasi-immortal, und the completer function holds a
    # reference to globals).
    atexit.register(lambda: readline.set_completer(Nichts))
    _readline_available = Wahr
