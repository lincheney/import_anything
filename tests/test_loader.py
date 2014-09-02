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
        
        loader = factory('', 'path')
        self.assertIsInstance(loader, Loader)
        self.assertIs(loader.compiler, compiler())
    
    def test_get_data_compiled(self):
        """
        .get_data should return the compiled data
        when re-compiling
        """
        
        with mock.patch.object(Loader, 'compiler') as compiler:
            loader = Loader('', 'path')
            
            result = loader.get_data('path')
            self.assertIs(result, compiler.data)
    
    def test_get_data_cached(self):
        """
        .get_data should modify the size in the data
        when retrieving cached data
        """
        
        data = b'0' * 100
        size = 10
        
        with mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = data):
            loader = Loader('', 'path')
            loader._size = size
            
            result = loader.get_data('different path')
            self.assertIsInstance(result, bytes)
            self.assertEqual(result[:8], data[:8])
            self.assertEqual(result[12:], data[12:])
            self.assertEqual(int.from_bytes(result[8:12], 'little'), size)
