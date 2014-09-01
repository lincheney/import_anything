import unittest
import unittest.mock as mock
from import_anything import Finder

class TestFinder(unittest.TestCase):
    def test_meta_path(self):
        """
        Finder should be registered in sys.meta_path
        """
        
        import sys
        self.assertIn(Finder, sys.meta_path)
    
    @mock.patch('importlib.machinery.FileFinder')
    def test_find_module(self, file_finder):
        """
        Finder#find_module should search for the loader
        """
        
        find_loader = file_finder().find_loader
        find_loader.return_value = [None, None]
        
        path = ['a', 'b']
        fullname = 'fullname'
        
        loader = mock.Mock()
        Finder.register(loader, '.extension')
        
        Finder.find_module(fullname, path)
        
        for i in path:
            # should have made a FileFinder for each path
            file_finder.assert_any_call(i, (loader, '.extension'))
        # should have searched for fullname
        find_loader.assert_called_with(fullname)
