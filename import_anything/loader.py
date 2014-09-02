import importlib.machinery
import marshal
import functools
import ctypes

class Loader(importlib.machinery.SourceFileLoader):
    """
    Loader
    
    Loads/stores cached bytecode etc.
    
    Loader.from_compiler() returns a factory that
    makes Loader with a preset compiler
    
    When compiler.MAGIC is set:
        the magic number in the saved bytecode is XORed
        with the compiler.MAGIC
        This basically allows you to bump compiler version
        numbers and the importer will automatically
        recompile all the bytecode.
    
    When compiler.MAGIC_TAG is set:
        instead of reading/writing bytecode at
        /path/to/bytecode.cpython-33.pyc
        it reads/writes at
        /path/to/bytecode.cpython-33.{magic-tag}.pyc
        This allows you to separate custom compiled bytecode
        from normal python bytecode.
    """
    
    _size = None
    _compiler = None
    _code_object = None
    
    def __init__(self, *args, compiler, **kwargs):
        super().__init__(*args, **kwargs)
        self._compiler_cls = compiler
    
    @classmethod
    def from_compiler(cls, compiler):
        """
        Return a Loader factory for @compiler
        """
        
        return functools.partial(Loader, compiler = compiler)
    
    @property
    def compiler(self):
        if self._compiler is None:
            self._compiler = self._compiler_cls(self.path)
        return self._compiler
    
    def get_data(self, path):
        if path != self.path:
            # return bytecode but set the size to the original file size
            path = self.apply_compiler_magic_tag(path)
            data = super().get_data(path)
            
            magic = data[:4]
            mtime = data[4:8]
            size = data[8:12]
            code = data[12:]
            
            magic = self.apply_compiler_magic(magic)
            size = self._size.to_bytes(4, 'little')
            
            data = magic + mtime + size + code
            return data
        
        # return the translated source
        return self.compiler.data
    
    def source_to_code(self, data, path, *args, original_code=None, **kwargs):
        if self._code_object is None:
            if original_code:
                self._code_object = original_code
            else:
                # modify the line numbers in the AST
                tree = self.compiler.make_ast_tree()
                self._code_object = compile(tree, path, 'exec', *args, **kwargs)
        return self._code_object
    
    def get_code(self, fullname):
        code_object = super().get_code(fullname)
        return self.source_to_code(None, self.path, original_code=code_object)
    
    def set_data(self, path, data, *args, **kwargs):
        # use the code with modified line numbers
        code_object = self.source_to_code(None, self.path)
        
        magic = data[:4]
        mtime = data[4:8]
        size = data[8:12]
        code = data[12:]
        
        magic = self.apply_compiler_magic(magic)
        code = marshal.dumps(code_object)
        
        data = magic + mtime + size + code
        path = self.apply_compiler_magic_tag(path)
        return super().set_data(path, data, *args, **kwargs)
    
    def path_stats(self, path):
        result = super().path_stats(path)
        # store the original file size for later
        self._size = result['size']
        return result
    
    def apply_compiler_magic(self, magic):
        """
        XOR the (bit flipped) compiler magic with @magic
        Only applied to the first 2 bytes
        """
        
        if self._compiler_cls.MAGIC is None:
            return magic
        
        tail = magic[2:]
        magic = int.from_bytes(magic[:2], 'little') ^ self._compiler_cls.MAGIC
        magic = ctypes.c_uint16(magic).value.to_bytes(2, 'little')
        
        return magic + tail
    
    def apply_compiler_magic_tag(self, path):
        """
        Insert the compiler magic tag into @path
        
        '/abc/def/xyz.cpython.pyc' -> '/abc/def/xyz.cpython.{magic-tag}.pyc'
        
        If compiler has no MAGIC_TAG, returns @path unmodified
        """
        
        if self._compiler_cls.MAGIC_TAG is None:
            return path
        
        head, sep, tail = path.rpartition('.')
        if not sep:
            head = tail
        
        return ''.join((head, '.', self._compiler_cls.MAGIC_TAG, sep, tail))
