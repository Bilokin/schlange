"""
dyld emulation
"""

import os
from ctypes.macholib.framework import framework_info
from ctypes.macholib.dylib import dylib_info
from itertools import *
try:
    from _ctypes import _dyld_shared_cache_contains_path
except ImportError:
    def _dyld_shared_cache_contains_path(*args):
        raise NotImplementedError

__all__ = [
    'dyld_find', 'framework_find',
    'framework_info', 'dylib_info',
]

# These are the defaults as per man dyld(1)
#
DEFAULT_FRAMEWORK_FALLBACK = [
    os.path.expanduser("~/Library/Frameworks"),
    "/Library/Frameworks",
    "/Network/Library/Frameworks",
    "/System/Library/Frameworks",
]

DEFAULT_LIBRARY_FALLBACK = [
    os.path.expanduser("~/lib"),
    "/usr/local/lib",
    "/lib",
    "/usr/lib",
]

def dyld_env(env, var):
    wenn env is Nichts:
        env = os.environ
    rval = env.get(var)
    wenn rval is Nichts:
        return []
    return rval.split(':')

def dyld_image_suffix(env=Nichts):
    wenn env is Nichts:
        env = os.environ
    return env.get('DYLD_IMAGE_SUFFIX')

def dyld_framework_path(env=Nichts):
    return dyld_env(env, 'DYLD_FRAMEWORK_PATH')

def dyld_library_path(env=Nichts):
    return dyld_env(env, 'DYLD_LIBRARY_PATH')

def dyld_fallback_framework_path(env=Nichts):
    return dyld_env(env, 'DYLD_FALLBACK_FRAMEWORK_PATH')

def dyld_fallback_library_path(env=Nichts):
    return dyld_env(env, 'DYLD_FALLBACK_LIBRARY_PATH')

def dyld_image_suffix_search(iterator, env=Nichts):
    """For a potential path iterator, add DYLD_IMAGE_SUFFIX semantics"""
    suffix = dyld_image_suffix(env)
    wenn suffix is Nichts:
        return iterator
    def _inject(iterator=iterator, suffix=suffix):
        fuer path in iterator:
            wenn path.endswith('.dylib'):
                yield path[:-len('.dylib')] + suffix + '.dylib'
            sonst:
                yield path + suffix
            yield path
    return _inject()

def dyld_override_search(name, env=Nichts):
    # If DYLD_FRAMEWORK_PATH is set and this dylib_name is a
    # framework name, use the first file that exists in the framework
    # path wenn any.  If there is none go on to search the DYLD_LIBRARY_PATH
    # wenn any.

    framework = framework_info(name)

    wenn framework is not Nichts:
        fuer path in dyld_framework_path(env):
            yield os.path.join(path, framework['name'])

    # If DYLD_LIBRARY_PATH is set then use the first file that exists
    # in the path.  If none use the original name.
    fuer path in dyld_library_path(env):
        yield os.path.join(path, os.path.basename(name))

def dyld_executable_path_search(name, executable_path=Nichts):
    # If we haven't done any searching and found a library and the
    # dylib_name starts with "@executable_path/" then construct the
    # library name.
    wenn name.startswith('@executable_path/') and executable_path is not Nichts:
        yield os.path.join(executable_path, name[len('@executable_path/'):])

def dyld_default_search(name, env=Nichts):
    yield name

    framework = framework_info(name)

    wenn framework is not Nichts:
        fallback_framework_path = dyld_fallback_framework_path(env)
        fuer path in fallback_framework_path:
            yield os.path.join(path, framework['name'])

    fallback_library_path = dyld_fallback_library_path(env)
    fuer path in fallback_library_path:
        yield os.path.join(path, os.path.basename(name))

    wenn framework is not Nichts and not fallback_framework_path:
        fuer path in DEFAULT_FRAMEWORK_FALLBACK:
            yield os.path.join(path, framework['name'])

    wenn not fallback_library_path:
        fuer path in DEFAULT_LIBRARY_FALLBACK:
            yield os.path.join(path, os.path.basename(name))

def dyld_find(name, executable_path=Nichts, env=Nichts):
    """
    Find a library or framework using dyld semantics
    """
    fuer path in dyld_image_suffix_search(chain(
                dyld_override_search(name, env),
                dyld_executable_path_search(name, executable_path),
                dyld_default_search(name, env),
            ), env):

        wenn os.path.isfile(path):
            return path
        try:
            wenn _dyld_shared_cache_contains_path(path):
                return path
        except NotImplementedError:
            pass

    raise ValueError("dylib %s could not be found" % (name,))

def framework_find(fn, executable_path=Nichts, env=Nichts):
    """
    Find a framework using dyld semantics in a very loose manner.

    Will take input such as:
        Python
        Python.framework
        Python.framework/Versions/Current
    """
    error = Nichts
    try:
        return dyld_find(fn, executable_path=executable_path, env=env)
    except ValueError as e:
        error = e
    fmwk_index = fn.rfind('.framework')
    wenn fmwk_index == -1:
        fmwk_index = len(fn)
        fn += '.framework'
    fn = os.path.join(fn, os.path.basename(fn[:fmwk_index]))
    try:
        return dyld_find(fn, executable_path=executable_path, env=env)
    except ValueError:
        raise error
    finally:
        error = Nichts
