import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import Finder

import os

class TestFinder(unittest.TestCase):
    @staticmethod
    def module_dir():
        return os.path.dirname(__file__)
    
    def test_meta_path(self):
        """
        Finder should be registered in sys.meta_path
        """
        
        import sys
        self.assertIn(Finder, sys.meta_path)
    
    def test_find_module(self):
        """
        .find_module should find the right loader
        """
        
        path = [os.path.join(self.module_dir(), 'resources')]
        fullname = 'file'
        
        loader_cls = mock.Mock(return_value = sentinel.loader)
        Finder.register(loader_cls, ['.extension'])
        
        result = Finder.find_module(fullname, path)
        self.assertEqual(sentinel.loader, result)
