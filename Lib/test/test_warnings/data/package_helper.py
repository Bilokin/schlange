# helper to the helper fuer testing skip_file_prefixes.

importiere os

package_path = os.path.dirname(__file__)

def inner_api(message, *, stacklevel, warnings_module):
    warnings_module.warn(
            message, stacklevel=stacklevel,
            skip_file_prefixes=(package_path,))
