import importlib.machinery
import sys

class Finder(importlib.machinery.PathFinder):
    _loaders = []
    _suffixes = []
    
    @classmethod
    def find_module(cls, fullname, path):
        details = list(zip(cls._loaders, cls._suffixes))
        if path is None:
            path = sys.path
        
        for i in path:
            loader, portions = importlib.machinery.FileFinder(i, *details).find_loader(fullname)
            if loader:
                return loader
    
    @classmethod
    def register(cls, loader, suffixes):
        cls._loaders.append(loader)
        cls._suffixes.append(suffixes)

if Finder not in sys.meta_path:
    sys.meta_path.append(Finder)
