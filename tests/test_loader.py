import unittest
import unittest.mock as mock
from import_anything import Loader, Compiler

class TestLoader(unittest.TestCase):
    def test_from_compiler(self):
        """
        .from_compiler should subclass and set COMPILER
        """
        
        compiler = mock.Mock()
        factory = Loader.from_compiler(compiler)
        
        assert callable(factory)
        
        loader = factory('', [])
        self.assertIsInstance(loader, Loader)
        self.assertIs(loader.compiler, compiler())
