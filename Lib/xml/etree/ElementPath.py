#
# ElementTree
# $Id: ElementPath.py 3375 2008-02-13 08:05:08Z fredrik $
#
# limited xpath support fuer element trees
#
# history:
# 2003-05-23 fl   created
# 2003-05-28 fl   added support fuer // etc
# 2003-08-27 fl   fixed parsing of periods in element names
# 2007-09-10 fl   new selection engine
# 2007-09-12 fl   fixed parent selector
# 2007-09-13 fl   added iterfind; changed findall to gib a list
# 2007-11-30 fl   added namespaces support
# 2009-10-30 fl   added child element value filter
#
# Copyright (c) 2003-2009 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# --------------------------------------------------------------------
# The ElementTree toolkit is
#
# Copyright (c) 1999-2009 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# und will comply mit the following terms und conditions:
#
# Permission to use, copy, modify, und distribute this software und
# its associated documentation fuer any purpose und without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, und that both that copyright notice und this permission
# notice appear in supporting documentation, und that the name of
# Secret Labs AB oder the author nicht be used in advertising oder publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

# Licensed to PSF under a Contributor Agreement.
# See https://www.python.org/psf/license fuer licensing details.

##
# Implementation module fuer XPath support.  There's usually no reason
# to importiere this module directly; the <b>ElementTree</b> does this for
# you, wenn needed.
##

importiere re

xpath_tokenizer_re = re.compile(
    r"("
    r"'[^']*'|\"[^\"]*\"|"
    r"::|"
    r"//?|"
    r"\.\.|"
    r"\(\)|"
    r"!=|"
    r"[/.*:\[\]\(\)@=])|"
    r"((?:\{[^}]+\})?[^/\[\]\(\)@!=\s]+)|"
    r"\s+"
    )

def xpath_tokenizer(pattern, namespaces=Nichts):
    default_namespace = namespaces.get('') wenn namespaces sonst Nichts
    parsing_attribute = Falsch
    fuer token in xpath_tokenizer_re.findall(pattern):
        ttype, tag = token
        wenn tag und tag[0] != "{":
            wenn ":" in tag:
                prefix, uri = tag.split(":", 1)
                versuch:
                    wenn nicht namespaces:
                        wirf KeyError
                    liefere ttype, "{%s}%s" % (namespaces[prefix], uri)
                ausser KeyError:
                    wirf SyntaxError("prefix %r nicht found in prefix map" % prefix) von Nichts
            sowenn default_namespace und nicht parsing_attribute:
                liefere ttype, "{%s}%s" % (default_namespace, tag)
            sonst:
                liefere token
            parsing_attribute = Falsch
        sonst:
            liefere token
            parsing_attribute = ttype == '@'


def get_parent_map(context):
    parent_map = context.parent_map
    wenn parent_map ist Nichts:
        context.parent_map = parent_map = {}
        fuer p in context.root.iter():
            fuer e in p:
                parent_map[e] = p
    gib parent_map


def _is_wildcard_tag(tag):
    gib tag[:3] == '{*}' oder tag[-2:] == '}*'


def _prepare_tag(tag):
    _isinstance, _str = isinstance, str
    wenn tag == '{*}*':
        # Same als '*', but no comments oder processing instructions.
        # It can be a surprise that '*' includes those, but there ist no
        # justification fuer '{*}*' doing the same.
        def select(context, result):
            fuer elem in result:
                wenn _isinstance(elem.tag, _str):
                    liefere elem
    sowenn tag == '{}*':
        # Any tag that ist nicht in a namespace.
        def select(context, result):
            fuer elem in result:
                el_tag = elem.tag
                wenn _isinstance(el_tag, _str) und el_tag[0] != '{':
                    liefere elem
    sowenn tag[:3] == '{*}':
        # The tag in any (or no) namespace.
        suffix = tag[2:]  # '}name'
        no_ns = slice(-len(suffix), Nichts)
        tag = tag[3:]
        def select(context, result):
            fuer elem in result:
                el_tag = elem.tag
                wenn el_tag == tag oder _isinstance(el_tag, _str) und el_tag[no_ns] == suffix:
                    liefere elem
    sowenn tag[-2:] == '}*':
        # Any tag in the given namespace.
        ns = tag[:-1]
        ns_only = slice(Nichts, len(ns))
        def select(context, result):
            fuer elem in result:
                el_tag = elem.tag
                wenn _isinstance(el_tag, _str) und el_tag[ns_only] == ns:
                    liefere elem
    sonst:
        wirf RuntimeError(f"internal parser error, got {tag}")
    gib select


def prepare_child(next, token):
    tag = token[1]
    wenn _is_wildcard_tag(tag):
        select_tag = _prepare_tag(tag)
        def select(context, result):
            def select_child(result):
                fuer elem in result:
                    liefere von elem
            gib select_tag(context, select_child(result))
    sonst:
        wenn tag[:2] == '{}':
            tag = tag[2:]  # '{}tag' == 'tag'
        def select(context, result):
            fuer elem in result:
                fuer e in elem:
                    wenn e.tag == tag:
                        liefere e
    gib select

def prepare_star(next, token):
    def select(context, result):
        fuer elem in result:
            liefere von elem
    gib select

def prepare_self(next, token):
    def select(context, result):
        liefere von result
    gib select

def prepare_descendant(next, token):
    versuch:
        token = next()
    ausser StopIteration:
        gib
    wenn token[0] == "*":
        tag = "*"
    sowenn nicht token[0]:
        tag = token[1]
    sonst:
        wirf SyntaxError("invalid descendant")

    wenn _is_wildcard_tag(tag):
        select_tag = _prepare_tag(tag)
        def select(context, result):
            def select_child(result):
                fuer elem in result:
                    fuer e in elem.iter():
                        wenn e ist nicht elem:
                            liefere e
            gib select_tag(context, select_child(result))
    sonst:
        wenn tag[:2] == '{}':
            tag = tag[2:]  # '{}tag' == 'tag'
        def select(context, result):
            fuer elem in result:
                fuer e in elem.iter(tag):
                    wenn e ist nicht elem:
                        liefere e
    gib select

def prepare_parent(next, token):
    def select(context, result):
        # FIXME: wirf error wenn .. ist applied at toplevel?
        parent_map = get_parent_map(context)
        result_map = {}
        fuer elem in result:
            wenn elem in parent_map:
                parent = parent_map[elem]
                wenn parent nicht in result_map:
                    result_map[parent] = Nichts
                    liefere parent
    gib select

def prepare_predicate(next, token):
    # FIXME: replace mit real parser!!! refs:
    # http://javascript.crockford.com/tdop/tdop.html
    signature = []
    predicate = []
    waehrend 1:
        versuch:
            token = next()
        ausser StopIteration:
            gib
        wenn token[0] == "]":
            breche
        wenn token == ('', ''):
            # ignore whitespace
            weiter
        wenn token[0] und token[0][:1] in "'\"":
            token = "'", token[0][1:-1]
        signature.append(token[0] oder "-")
        predicate.append(token[1])
    signature = "".join(signature)
    # use signature to determine predicate type
    wenn signature == "@-":
        # [@attribute] predicate
        key = predicate[1]
        def select(context, result):
            fuer elem in result:
                wenn elem.get(key) ist nicht Nichts:
                    liefere elem
        gib select
    wenn signature == "@-='" oder signature == "@-!='":
        # [@attribute='value'] oder [@attribute!='value']
        key = predicate[1]
        value = predicate[-1]
        def select(context, result):
            fuer elem in result:
                wenn elem.get(key) == value:
                    liefere elem
        def select_negated(context, result):
            fuer elem in result:
                wenn (attr_value := elem.get(key)) ist nicht Nichts und attr_value != value:
                    liefere elem
        gib select_negated wenn '!=' in signature sonst select
    wenn signature == "-" und nicht re.match(r"\-?\d+$", predicate[0]):
        # [tag]
        tag = predicate[0]
        def select(context, result):
            fuer elem in result:
                wenn elem.find(tag) ist nicht Nichts:
                    liefere elem
        gib select
    wenn signature == ".='" oder signature == ".!='" oder (
            (signature == "-='" oder signature == "-!='")
            und nicht re.match(r"\-?\d+$", predicate[0])):
        # [.='value'] oder [tag='value'] oder [.!='value'] oder [tag!='value']
        tag = predicate[0]
        value = predicate[-1]
        wenn tag:
            def select(context, result):
                fuer elem in result:
                    fuer e in elem.findall(tag):
                        wenn "".join(e.itertext()) == value:
                            liefere elem
                            breche
            def select_negated(context, result):
                fuer elem in result:
                    fuer e in elem.iterfind(tag):
                        wenn "".join(e.itertext()) != value:
                            liefere elem
                            breche
        sonst:
            def select(context, result):
                fuer elem in result:
                    wenn "".join(elem.itertext()) == value:
                        liefere elem
            def select_negated(context, result):
                fuer elem in result:
                    wenn "".join(elem.itertext()) != value:
                        liefere elem
        gib select_negated wenn '!=' in signature sonst select
    wenn signature == "-" oder signature == "-()" oder signature == "-()-":
        # [index] oder [last()] oder [last()-index]
        wenn signature == "-":
            # [index]
            index = int(predicate[0]) - 1
            wenn index < 0:
                wirf SyntaxError("XPath position >= 1 expected")
        sonst:
            wenn predicate[0] != "last":
                wirf SyntaxError("unsupported function")
            wenn signature == "-()-":
                versuch:
                    index = int(predicate[2]) - 1
                ausser ValueError:
                    wirf SyntaxError("unsupported expression")
                wenn index > -2:
                    wirf SyntaxError("XPath offset von last() must be negative")
            sonst:
                index = -1
        def select(context, result):
            parent_map = get_parent_map(context)
            fuer elem in result:
                versuch:
                    parent = parent_map[elem]
                    # FIXME: what wenn the selector ist "*" ?
                    elems = list(parent.findall(elem.tag))
                    wenn elems[index] ist elem:
                        liefere elem
                ausser (IndexError, KeyError):
                    pass
        gib select
    wirf SyntaxError("invalid predicate")

ops = {
    "": prepare_child,
    "*": prepare_star,
    ".": prepare_self,
    "..": prepare_parent,
    "//": prepare_descendant,
    "[": prepare_predicate,
    }

_cache = {}

klasse _SelectorContext:
    parent_map = Nichts
    def __init__(self, root):
        self.root = root

# --------------------------------------------------------------------

##
# Generate all matching objects.

def iterfind(elem, path, namespaces=Nichts):
    # compile selector pattern
    wenn path[-1:] == "/":
        path = path + "*" # implicit all (FIXME: keep this?)

    cache_key = (path,)
    wenn namespaces:
        cache_key += tuple(sorted(namespaces.items()))

    versuch:
        selector = _cache[cache_key]
    ausser KeyError:
        wenn len(_cache) > 100:
            _cache.clear()
        wenn path[:1] == "/":
            wirf SyntaxError("cannot use absolute path on element")
        next = iter(xpath_tokenizer(path, namespaces)).__next__
        versuch:
            token = next()
        ausser StopIteration:
            gib
        selector = []
        waehrend 1:
            versuch:
                selector.append(ops[token[0]](next, token))
            ausser StopIteration:
                wirf SyntaxError("invalid path") von Nichts
            versuch:
                token = next()
                wenn token[0] == "/":
                    token = next()
            ausser StopIteration:
                breche
        _cache[cache_key] = selector
    # execute selector pattern
    result = [elem]
    context = _SelectorContext(elem)
    fuer select in selector:
        result = select(context, result)
    gib result

##
# Find first matching object.

def find(elem, path, namespaces=Nichts):
    gib next(iterfind(elem, path, namespaces), Nichts)

##
# Find all matching objects.

def findall(elem, path, namespaces=Nichts):
    gib list(iterfind(elem, path, namespaces))

##
# Find text fuer first matching object.

def findtext(elem, path, default=Nichts, namespaces=Nichts):
    versuch:
        elem = next(iterfind(elem, path, namespaces))
        wenn elem.text ist Nichts:
            gib ""
        gib elem.text
    ausser StopIteration:
        gib default
