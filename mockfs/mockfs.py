"""
mockfs: An in-memory filesystem use with unittest

>>> import mockfs

"""
import os
import glob

__version__ = '0.5.0'


# Python functions to replace
builtins = {
    'os.path.exists': os.path.exists,
    'os.path.islink': os.path.islink,
    'os.path.isdir': os.path.isdir,
    'os.walk': os.walk,
    'os.listdir': os.listdir,
}


_mockfs = None
def singleton(entries=None, pathmap=None):
    """Return a global MockFS singleton."""
    global _mockfs
    if not _mockfs:
        _mockfs = MockFS(entries=entries, pathmap=pathmap)
    return _mockfs


def install(entries=None, pathmap=None):
    """Replace builtin modules with mockfs equivalents."""
    mockfs = singleton(entries=entries, pathmap=pathmap)
    os.path.exists = mockfs.exists
    os.path.islink = mockfs.islink
    os.path.isdir = mockfs.isdir
    os.walk = mockfs.walk
    os.listdir = mockfs.listdir

def uninstall():
    """Restore the original builtin functions."""
    for k, v in builtins.iteritems():
        mod, func = k.rsplit('.', 1)
        item = None
        for elt in mod.split('.'):
            if item is None:
                item = globals()[elt]
            else:
                item = getattr(item, elt)
        setattr(item, func, v)


class MockFS(object):
    def __init__(self, entries=None, pathmap=None):
        self._entries = entries
        self._pathmap = pathmap
        self._inwalk = False
        self._path = None
        self._walkdir = self._entries

    def sanitize(self, path):
        """
        Clean up path arguments for use with MockFS

        MockFS isn't happy with trailing slashes since it uses a dict
        to simulate the file system.

        """
        path = path.replace('//', '/')
        while len(path) > 1 and path.endswith('/'):
            path = path[:-1]
        return path

    def exists(self, path):
        path = self.sanitize(path)
        dirent = self.direntry(os.path.dirname(path))
        return dirent and os.path.basename(path) in dirent

    def isdir(self, path):
        path = self.sanitize(path)
        return type(self.direntry(path)) is dict

    def listdir(self, path):
        path = self.sanitize(path)
        direntry = self.direntry(path)
        if direntry:
            entries = list(direntry.keys())
            entries.sort()
            return entries
        return []

    def islink(self, path):
        path = self.sanitize(path)
        return False

    def walk(self, path):
        path = self.sanitize(path)
        entries = []
        inspect = [path]
        while True:
            dirstack = []
            for entry in inspect:
                dirent = self.direntry(entry)
                dirs = []
                files = []
                if dirent:
                    for e in dirent:
                        if type(dirent[e]) is dict:
                            dirs.append(e)
                        else:
                            files.append(e)
                yield (entry, dirs, files)
                dirstack.extend([os.path.join(entry, d) for d in dirs])
            inspect = dirstack
            if not inspect:
                break
        raise StopIteration

    def direntry(self, path):
        path = self.sanitize(path)
        if path == '/':
            return self._entries
        elts = path.split('/')[1:]
        current = self._entries
        retval = None
        for elt in elts:
            if elt in current:
                retval = current[elt]
                current = current[elt]
            else:
                return None
        return retval