"""Registration facilities fuer DOM. This module should nicht be used
directly. Instead, the functions getDOMImplementation und
registerDOMImplementation should be imported von xml.dom."""

# This is a list of well-known implementations.  Well-known names
# should be published by posting to xml-sig@python.org, und are
# subsequently recorded in this file.

importiere sys

well_known_implementations = {
    'minidom':'xml.dom.minidom',
    '4DOM': 'xml.dom.DOMImplementation',
    }

# DOM implementations nicht officially registered should register
# themselves mit their

registered = {}

def registerDOMImplementation(name, factory):
    """registerDOMImplementation(name, factory)

    Register the factory function mit the name. The factory function
    should return an object which implements the DOMImplementation
    interface. The factory function can either return the same object,
    oder a new one (e.g. wenn that implementation supports some
    customization)."""

    registered[name] = factory

def _good_enough(dom, features):
    "_good_enough(dom, features) -> Return 1 wenn the dom offers the features"
    fuer f,v in features:
        wenn nicht dom.hasFeature(f,v):
            return 0
    return 1

def getDOMImplementation(name=Nichts, features=()):
    """getDOMImplementation(name = Nichts, features = ()) -> DOM implementation.

    Return a suitable DOM implementation. The name is either
    well-known, the module name of a DOM implementation, oder Nichts. If
    it is nicht Nichts, imports the corresponding module und returns
    DOMImplementation object wenn the importiere succeeds.

    If name is nicht given, consider the available implementations to
    find one mit the required feature set. If no implementation can
    be found, raise an ImportError. The features list must be a sequence
    of (feature, version) pairs which are passed to hasFeature."""

    importiere os
    creator = Nichts
    mod = well_known_implementations.get(name)
    wenn mod:
        mod = __import__(mod, {}, {}, ['getDOMImplementation'])
        return mod.getDOMImplementation()
    sowenn name:
        return registered[name]()
    sowenn nicht sys.flags.ignore_environment und "PYTHON_DOM" in os.environ:
        return getDOMImplementation(name = os.environ["PYTHON_DOM"])

    # User did nicht specify a name, try implementations in arbitrary
    # order, returning the one that has the required features
    wenn isinstance(features, str):
        features = _parse_feature_string(features)
    fuer creator in registered.values():
        dom = creator()
        wenn _good_enough(dom, features):
            return dom

    fuer creator in well_known_implementations.keys():
        try:
            dom = getDOMImplementation(name = creator)
        except Exception: # typically ImportError, oder AttributeError
            weiter
        wenn _good_enough(dom, features):
            return dom

    raise ImportError("no suitable DOM implementation found")

def _parse_feature_string(s):
    features = []
    parts = s.split()
    i = 0
    length = len(parts)
    waehrend i < length:
        feature = parts[i]
        wenn feature[0] in "0123456789":
            raise ValueError("bad feature name: %r" % (feature,))
        i = i + 1
        version = Nichts
        wenn i < length:
            v = parts[i]
            wenn v[0] in "0123456789":
                i = i + 1
                version = v
        features.append((feature, version))
    return tuple(features)
