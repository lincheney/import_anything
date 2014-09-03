import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import Loader, Compiler

def default_loader():
    compiler = mock.Mock()
    compiler.MAGIC = None
    compiler.MAGIC_TAG = None
    
    return Loader('filename', 'path', compiler = compiler)

class TestLoader(unittest.TestCase):
    @mock.patch('builtins.compile')
    def test_source_to_code_compiled(self, compile):
        """
        .source_to_code() should compile a code object
        when re-compiling
        """
        
        compile.return_value = sentinel.code
        
        loader = default_loader()
        result = loader.source_to_code(None, sentinel.path)
        
        compile.assert_called_once_with(loader.compiler.make_ast_tree(), sentinel.path, mock.ANY)
        self.assertIs(result, sentinel.code)
    
    @mock.patch('importlib.machinery.SourceFileLoader.path_stats')
    def test_path_stats(self, super_path_stats):
        """
        .path_stats() should store the returned size
        """
        
        super_path_stats.return_value = dict(size = sentinel.size)
        
        loader = default_loader()
        result = loader.path_stats('some path')
        
        super_path_stats.assert_called_once_with('some path')
        self.assertEqual(loader._size, sentinel.size)

class TestLoaderGetData(unittest.TestCase):
    """
    Tests for Loader.get_data()
    """
    
    data = b'0' * 100
    size = 10
    path = '/abc/def.py'
    
    def setUp(self):
        self.get_data_patch = mock.patch('importlib.machinery.SourceFileLoader.get_data', return_value = self.data)
        self.super_get_data = self.get_data_patch.start()
        
        self.loader = default_loader()
        self.loader._size = self.size
    
    def tearDown(self):
        self.get_data_patch.stop()
    
    
    def test_compiled(self):
        """
        .get_data() should not attempt to compile if we don't ask for bytecode
        """
        
        self.assertEqual(self.loader.get_data(self.loader.path), '')
    
    def test_without_magic(self):
        """
        .get_data() should only modify the size without magic
        """
        
        result = self.loader.get_data(self.path)
        self.super_get_data.assert_called_once_with(self.path)
        
        self.assertIsInstance(result, bytes)
        self.assertEqual(result[:8], self.data[:8])
        self.assertEqual(result[8:12], self.size.to_bytes(4, 'little'))
        self.assertEqual(result[12:], self.data[12:])
        
    def test_with_magic(self):
        """
        .get_data() should apply the compiler magic
        """
        
        self.loader._compiler_cls.MAGIC = 10
        expected_magic = self.loader.apply_compiler_magic(self.data[:2]) + self.data[2:4]
        
        result = self.loader.get_data(self.path)
        self.super_get_data.assert_called_once_with(self.path)
        self.assertEqual(result[:4], expected_magic)
    
    def test_with_magic_tag(self):
        """
        .get_data() should apply the magic tag to the
        path that data gets loaded from
        """
        
        magic_tag = 'magic-tag'
        self.loader._compiler_cls.MAGIC_TAG = magic_tag
        magic_path = self.loader.apply_compiler_magic_tag(self.path)
        
        result = self.loader.get_data(self.path)
        self.super_get_data.assert_called_once_with(magic_path)
    
    def test_recompile(self):
        """
        .get_data() should refuse to load data if recompiling
        """
        
        self.loader._recompile = True
        with self.assertRaises(Exception):
            self.loader.get_data(self.path)


class TestLoadSetData(unittest.TestCase):
    """
    Tests for Loader.set_data()
    """
    
    data = b'0' * 100
    code = 'code'
    path = '/abc/def.py'
    
    def setUp(self):
        self.set_data_patch = mock.patch('importlib.machinery.SourceFileLoader.set_data', return_value = sentinel.super_result)
        self.super_set_data = self.set_data_patch.start()
        
        self.source_to_code_patch = mock.patch.object(Loader, 'source_to_code', return_value = self.code)
        self.source_to_code_patch.start()
        
        self.loader = default_loader()
    
    def tearDown(self):
        self.set_data_patch.stop()
        self.source_to_code_patch.stop()
    
    
    def test_no_magic(self):
        """
        .set_data() should replace data with recompiled code
        """
        import marshal
        
        result = self.loader.set_data(self.path, self.data)
        self.super_set_data.assert_called_once_with(self.path, self.data[:12] + marshal.dumps(self.code))
        self.assertIs(result, sentinel.super_result)
    
    def test_with_magic(self):
        """
        .set_data() should apply the compiler magic
        """
        
        compiler_magic = 100
        self.loader._compiler_cls.MAGIC = compiler_magic
        
        result = self.loader.set_data(self.path, self.data)
        args = self.super_set_data.call_args[0]
        self.assertEqual(args[0], self.path)
        self.assertEqual(args[1][:2], self.loader.apply_compiler_magic(self.data[:2]))
    
    def test_with_magic_tag(self):
        """
        .set_data() should apply the magic tag to the path that data gets saved to
        """
        
        magic_tag = 'magic-tag'
        self.loader._compiler_cls.MAGIC_TAG = magic_tag
        magic_path = self.loader.apply_compiler_magic_tag(self.path)
        
        result = self.loader.set_data(self.path, self.data)
        self.super_set_data.assert_called_once_with(magic_path, mock.ANY)


class TestLoaderApplyCompilerMagic(unittest.TestCase):
    """
    Tests for Loader.apply_compiler_magic()
    """
    
    data = b'0' * 100
    
    def setUp(self):
        self.loader = default_loader()
    
    
    def test_no_magic(self):
        """
        .apply_compiler_magic() should do nothing with no magic
        """
        
        result = self.loader.apply_compiler_magic(self.data)
        self.assertEqual(result, self.data)
    
    def test_with_magic(self):
        """
        .apply_compiler_magic() should xor magic to data
        """
        import ctypes
        
        compiler_magic = 10
        
        magic_data = int.from_bytes(self.data[:2], 'little') ^ compiler_magic
        magic_data = ctypes.c_uint16(magic_data).value.to_bytes(2, 'little')
        magic_data = magic_data + self.data[2:]
        
        self.loader._compiler_cls.MAGIC = compiler_magic
        
        result = self.loader.apply_compiler_magic(self.data)
        self.assertEqual(result, magic_data)


class TestLoaderApplyCompilerMagicTag(unittest.TestCase):
    """
    Tests for Loader.apply_compiler_magic()
    """
    
    path = '/abc/def/xyz.cpython.pyc'
    
    def setUp(self):
        self.loader = default_loader()
    
    
    def test_no_magic_tag(self):
        """
        .apply_compiler_magic_tag() should do nothing with no magic tag
        """
        
        result = self.loader.apply_compiler_magic_tag(self.path)
        self.assertEqual(result, self.path)
    
    def test_with_magic_tag(self):
        """
        .apply_compiler_magic_tag() should insert the magic tag into the path
        """
        
        magic_tag = 'custom-magic'
        magic_path = '/abc/def/xyz.cpython.{}.pyc'.format(magic_tag)
        
        self.loader._compiler_cls.MAGIC_TAG = magic_tag
        
        result = self.loader.apply_compiler_magic_tag(self.path)
        self.assertEqual(result, magic_path)
