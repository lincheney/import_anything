import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import Loader, Compiler

class TestLoader(unittest.TestCase):
    def default_loader(self, compiler = None):
        if compiler is None:
            compiler = mock.Mock()
            compiler.MAGIC = None
            compiler.MAGIC_TAG = None
        
        return Loader('filename', 'path', compiler = compiler)
    
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
    
    def test_get_data_compiled(self):
        """
        .get_data should return the translated code
        when re-compiling
        """
        
        loader = self.default_loader()
        result = loader.get_data('path')
        self.assertIs(result, loader.compiler.data)
    
    def test_get_data_cached(self):
        """
        .get_data should modify the size in data
        when retrieving cached data
        """
        
        data = b'0' * 100
        _size = 10
        
        with mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = data):
            loader = self.default_loader()
            loader._size = _size
            loader._compiler_cls.MAGIC = None
            
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
        
        compiler_magic = 10
        data = b'0' * 100
        
        with mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = data):
            loader = self.default_loader()
            loader._size = 10
            loader._compiler_cls.MAGIC = compiler_magic
            
            expected_magic = loader.apply_compiler_magic(data[:2]) + data[2:4]
            
            result = loader.get_data('different path')
            
            self.assertEqual(result[:4], expected_magic)
    
    @mock.patch('builtins.compile')
    def test_source_to_code_compiled(self, compile):
        """
        .source_to_code should compile a code object
        when re-compiling
        """
        
        compile.return_value = sentinel.code
        
        loader = self.default_loader()
        result = loader.source_to_code(None, sentinel.path)
        
        compile.assert_called_once_with(loader.compiler.make_ast_tree(), sentinel.path, mock.ANY)
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
    
    @mock.patch('importlib.machinery.SourceFileLoader.set_data', return_value = sentinel.super_result)
    def test_set_data_with_magic(self, super_set_data):
        """
        .set_data should apply the compiler magic to the data
        """
        import ctypes
        
        compiler_magic = 100
        data = b'0' * 100
        
        with mock.patch.object(Loader, 'source_to_code', return_value = 'code'):
            loader = self.default_loader()
            loader._compiler_cls.MAGIC = compiler_magic
            
            expected_magic = loader.apply_compiler_magic(data[:2])
            
            result = loader.set_data('bytecode path', data)
            
            args = super_set_data.call_args[0]
            self.assertEqual(args[0], 'bytecode path')
            self.assertEqual(args[1][:2], expected_magic)
    
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
    
    def test_apply_compiler_magic_no_magic(self):
        """
        .apply_compiler_magic should do nothing with no magic
        """
        
        data = b'0' * 100
        
        loader = self.default_loader()
        loader._compiler_cls.MAGIC = None
        
        result = loader.apply_compiler_magic(data)
        self.assertEqual(result, data)
    
    def test_apply_compiler_magic_with_magic(self):
        """
        .apply_compiler_magic should xor magic to data
        """
        import ctypes
        
        compiler_magic = 10
        data = b'0' * 100
        
        magic_data = int.from_bytes(data[:2], 'little') ^ ~compiler_magic
        magic_data = ctypes.c_uint16(magic_data).value.to_bytes(2, 'little')
        magic_data = magic_data + data[2:]
        
        loader = self.default_loader()
        loader._compiler_cls.MAGIC = compiler_magic
        
        result = loader.apply_compiler_magic(data)
        self.assertEqual(result, magic_data)
    
    def test_apply_compiler_magic_tag_no_magic_tag(self):
        """
        .apply_compiler_magic_tag should do nothing with no magic tag
        """
        
        path = '/abc/def/xyz.cpython.pyc'
        
        loader = self.default_loader()
        loader._compiler_cls.MAGIC_TAG = None
        
        result = loader.apply_compiler_magic_tag(path)
        self.assertEqual(result, path)
    
    def test_apply_compiler_magic_tag_with_magic_tag(self):
        """
        .apply_compiler_magic_tag should insert the magic tag
        into the path
        """
        
        magic_tag = 'custom-magic'
        path = '/abc/def/xyz.cpython.pyc'
        expected_path = '/abc/def/xyz.cpython.{}.pyc'.format(magic_tag)
        
        loader = self.default_loader()
        loader._compiler_cls.MAGIC_TAG = magic_tag
        
        result = loader.apply_compiler_magic_tag(path)
        self.assertEqual(result, expected_path)
