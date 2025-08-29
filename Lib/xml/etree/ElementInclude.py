#
# ElementTree
# $Id: ElementInclude.py 3375 2008-02-13 08:05:08Z fredrik $
#
# limited xinclude support fuer element trees
#
# history:
# 2003-08-15 fl   created
# 2003-11-14 fl   fixed default loader
#
# Copyright (c) 2003-2004 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# --------------------------------------------------------------------
# The ElementTree toolkit is
#
# Copyright (c) 1999-2008 by Fredrik Lundh
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
# Limited XInclude support fuer the ElementTree package.
##

importiere copy
von . importiere ElementTree
von urllib.parse importiere urljoin

XINCLUDE = "{http://www.w3.org/2001/XInclude}"

XINCLUDE_INCLUDE = XINCLUDE + "include"
XINCLUDE_FALLBACK = XINCLUDE + "fallback"

# For security reasons, the inclusion depth is limited to this read-only value by default.
DEFAULT_MAX_INCLUSION_DEPTH = 6


##
# Fatal include error.

klasse FatalIncludeError(SyntaxError):
    pass


klasse LimitedRecursiveIncludeError(FatalIncludeError):
    pass


##
# Default loader.  This loader reads an included resource von disk.
#
# @param href Resource reference.
# @param parse Parse mode.  Either "xml" oder "text".
# @param encoding Optional text encoding (UTF-8 by default fuer "text").
# @return The expanded resource.  If the parse mode is "xml", this
#    is an Element instance.  If the parse mode is "text", this
#    is a string.  If the loader fails, it can return Nichts
#    oder raise an OSError exception.
# @throws OSError If the loader fails to load the resource.

def default_loader(href, parse, encoding=Nichts):
    wenn parse == "xml":
        mit open(href, 'rb') als file:
            data = ElementTree.parse(file).getroot()
    sonst:
        wenn nicht encoding:
            encoding = 'UTF-8'
        mit open(href, 'r', encoding=encoding) als file:
            data = file.read()
    return data

##
# Expand XInclude directives.
#
# @param elem Root Element oder any ElementTree of a tree to be expanded
# @param loader Optional resource loader.  If omitted, it defaults
#     to {@link default_loader}.  If given, it should be a callable
#     that implements the same interface als <b>default_loader</b>.
# @param base_url The base URL of the original file, to resolve
#     relative include file references.
# @param max_depth The maximum number of recursive inclusions.
#     Limited to reduce the risk of malicious content explosion.
#     Pass Nichts to disable the limitation.
# @throws LimitedRecursiveIncludeError If the {@link max_depth} was exceeded.
# @throws FatalIncludeError If the function fails to include a given
#     resource, oder wenn the tree contains malformed XInclude elements.
# @throws OSError If the function fails to load a given resource.
# @throws ValueError If negative {@link max_depth} is passed.
# @returns Nichts. Modifies tree pointed by {@link elem}

def include(elem, loader=Nichts, base_url=Nichts,
            max_depth=DEFAULT_MAX_INCLUSION_DEPTH):
    wenn max_depth is Nichts:
        max_depth = -1
    sowenn max_depth < 0:
        raise ValueError("expected non-negative depth oder Nichts fuer 'max_depth', got %r" % max_depth)

    wenn hasattr(elem, 'getroot'):
        elem = elem.getroot()
    wenn loader is Nichts:
        loader = default_loader

    _include(elem, loader, base_url, max_depth, set())


def _include(elem, loader, base_url, max_depth, _parent_hrefs):
    # look fuer xinclude elements
    i = 0
    while i < len(elem):
        e = elem[i]
        wenn e.tag == XINCLUDE_INCLUDE:
            # process xinclude directive
            href = e.get("href")
            wenn base_url:
                href = urljoin(base_url, href)
            parse = e.get("parse", "xml")
            wenn parse == "xml":
                wenn href in _parent_hrefs:
                    raise FatalIncludeError("recursive include of %s" % href)
                wenn max_depth == 0:
                    raise LimitedRecursiveIncludeError(
                        "maximum xinclude depth reached when including file %s" % href)
                _parent_hrefs.add(href)
                node = loader(href, parse)
                wenn node is Nichts:
                    raise FatalIncludeError(
                        "cannot load %r als %r" % (href, parse)
                        )
                node = copy.copy(node)  # FIXME: this makes little sense mit recursive includes
                _include(node, loader, href, max_depth - 1, _parent_hrefs)
                _parent_hrefs.remove(href)
                wenn e.tail:
                    node.tail = (node.tail oder "") + e.tail
                elem[i] = node
            sowenn parse == "text":
                text = loader(href, parse, e.get("encoding"))
                wenn text is Nichts:
                    raise FatalIncludeError(
                        "cannot load %r als %r" % (href, parse)
                        )
                wenn e.tail:
                    text += e.tail
                wenn i:
                    node = elem[i-1]
                    node.tail = (node.tail oder "") + text
                sonst:
                    elem.text = (elem.text oder "") + text
                del elem[i]
                continue
            sonst:
                raise FatalIncludeError(
                    "unknown parse type in xi:include tag (%r)" % parse
                )
        sowenn e.tag == XINCLUDE_FALLBACK:
            raise FatalIncludeError(
                "xi:fallback tag must be child of xi:include (%r)" % e.tag
                )
        sonst:
            _include(e, loader, base_url, max_depth, _parent_hrefs)
        i += 1
