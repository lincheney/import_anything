import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import Loader, Compiler

class TestLoader(unittest.TestCase):
    def default_loader(self, compiler = sentinel.compiler):
        return Loader('', 'path', compiler = compiler)
    
    def test_from_compiler(self):
        """
        .from_compiler should subclass and set COMPILER
        """
        
        compiler_cls = mock.Mock(return_value = sentinel.compiler)
        factory = Loader.from_compiler(compiler_cls)
        
        assert callable(factory)
        
        loader = factory('', 'path')
        self.assertIsInstance(loader, Loader)
        self.assertIs(loader.compiler, sentinel.compiler)
    
    @mock.patch.object(Loader, 'compiler')
    def test_get_data_compiled(self, compiler):
        """
        .get_data should return the translated code
        when re-compiling
        """
        
        loader = self.default_loader()
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
            loader = self.default_loader()
            loader._size = size
            
            result = loader.get_data('different path')
            self.assertIsInstance(result, bytes)
            
            self.assertEqual(result[:8], data[:8])
            self.assertEqual(int.from_bytes(result[8:12], 'little'), size)
            self.assertEqual(result[12:], data[12:])
    
    @mock.patch('builtins.compile')
    @mock.patch.object(Loader, 'compiler')
    def test_source_to_code_compiled(self, compiler, compile):
        """
        .source_to_code should compile a code object
        when re-compiling
        """
        
        compile.return_value = sentinel.code
        
        loader = self.default_loader()
        result = loader.source_to_code(None, sentinel.path)
        
        compile.assert_called_once_with(compiler.make_ast_tree(), sentinel.path, mock.ANY)
        self.assertIs(result, sentinel.code)
    
    @mock.patch('importlib.machinery.SourceFileLoader.set_data', return_value = sentinel.super_result)
    def test_set_data(self, super_set_data):
        """
        .set_data should replace data with recompiled code
        """
        import marshal
        
        data = b'0' * 100
        code = 'code'
        
        with mock.patch.object(Loader, 'source_to_code', return_value = code):
            loader = self.default_loader()
            result = loader.set_data('bytecode path', data)
            
            super_set_data.assert_called_once_with('bytecode path', data[:12] + marshal.dumps(code))
            # returns the super call
            self.assertIs(result, sentinel.super_result)
    
    @mock.patch('importlib.machinery.SourceFileLoader.path_stats')
    def test_path_stats(self, super_path_stats):
        """
        .path_stats should store the returned size
        """
        
        super_path_stats.return_value = dict(size = sentinel.size)
        
        loader = self.default_loader()
        result = loader.path_stats('some path')
        
        super_path_stats.assert_called_once_with('some path')
        self.assertEqual(loader._size, sentinel.size)
