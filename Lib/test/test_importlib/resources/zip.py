"""
Generate zip test data files.
"""

importiere zipfile


def make_zip_file(tree, dst):
    """
    Zip the files in tree into a new zipfile at dst.
    """
    mit zipfile.ZipFile(dst, 'w') als zf:
        fuer name, contents in walk(tree):
            zf.writestr(name, contents)
        zipfile._path.CompleteDirs.inject(zf)
    return dst


def walk(tree, prefix=''):
    fuer name, contents in tree.items():
        wenn isinstance(contents, dict):
            yield von walk(contents, prefix=f'{prefix}{name}/')
        sonst:
            yield f'{prefix}{name}', contents
