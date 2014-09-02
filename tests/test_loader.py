import unittest
import unittest.mock as mock
from import_anything import Loader

class TestLoader(unittest.TestCase):
    def test_from_compiler(self):
        """
        .from_compiler should subclass and set COMPILER
        """
        
        compiler = mock.sentinel.compiler
        cls = Loader.from_compiler(compiler)
        
        assert issubclass(cls, Loader)
        self.assertIs(cls.COMPILER, compiler)
