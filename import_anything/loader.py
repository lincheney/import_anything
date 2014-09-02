import importlib.machinery
import marshal

class Loader(importlib.machinery.SourceFileLoader):
    """
    Loader
    
    Loads/stores cached bytecode etc.
    Uses the compiler that is set in self.COMPILER
    """
    
    _size = None
    _compiler = None
    _code_object = None
    COMPILER = None
    
    @classmethod
    def from_compiler(cls, compiler):
        """
        Return a Loader factory for @compiler
        """
        
        class _loader(cls):
            COMPILER = compiler
        return _loader
    
    @property
    def compiler(self):
        if self._compiler is None:
            self._compiler = self.COMPILER(self.path)
        return self._compiler
    
    def get_data(self, path):
        if path != self.path:
            # return bytecode but set the size to the original file size
            data = super().get_data(path)
            data = data[:8] + int.to_bytes(self._size, 4, 'little') + data[12:]
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
        data = data[:12] + marshal.dumps(code_object)
        return super().set_data(path, data, *args, **kwargs)
    
    def path_stats(self, path):
        result = super().path_stats(path)
        # store the original file size for later
        self._size = result['size']
        return result
