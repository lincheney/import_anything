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
        .get_data should modify the size in data
        when retrieving cached data
        """
        
        compiler = mock.Mock()
        compiler.MAGIC = None
        
        data = b'0' * 100
        _size = 10
        
        with mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = data):
            loader = self.default_loader(compiler)
            loader._size = _size
            
            result = loader.get_data('different path')
            self.assertIsInstance(result, bytes)
            
            magic = result[:4]
            mtime = result[4:8]
            size = result[8:12]
            code = result[12:]
            
            self.assertEqual(magic, data[:4])
            self.assertEqual(mtime, data[4:8])
            self.assertEqual(size, _size.to_bytes(4, 'little'))
            self.assertEqual(code, data[12:])
    
    def test_get_data_with_magic(self):
        """
        .get_data should remove compiler's magic from data
        """
        import ctypes
        
        compiler = mock.Mock()
        compiler.MAGIC = 10
        
        expected_magic = 100
        data = b'0' * 100
        # xor then stuff into an unsigned
        magic_bytes = ctypes.c_uint16(expected_magic ^ ~compiler.MAGIC).value.to_bytes(2, 'little')
        data = magic_bytes + data
        
        with mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = data):
            loader = self.default_loader(compiler)
            loader._size = 10
            
            result = loader.get_data('different path')
            
            # last 2 bytes are unmodified
            self.assertEqual(result[2:4], data[2:4])
            
            magic = int.from_bytes(result[:2], 'little')
            # xor then stuff into an unsigned
            magic = ctypes.c_uint16(magic ^ ~compiler.MAGIC).value
            magic = magic.to_bytes(2, 'little')
            self.assertEqual(magic, data[:2])
    
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
