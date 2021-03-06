import ast
import re
import io
import linecache
import tokenize

class Compiler:
    """
    Source-to-python compiler
    
    Subclasses should reimplement the .translate method
    and possibly set the MAGIC and MAGIC_TAG values
    
    MAGIC_TAG is used to differentiate between different
    compilers. The tag is used as part of the filename of
    the cached bytecode.
    It should be a string
    
    MAGIC is used to specify the 'version' of your compiler.
    If the MAGIC on your compiler changes, bytecode files
    with old MAGIC numbers will be recompiled.
    It should be a 16-bit unsigned integer (max 65535).
    
    In general, you should use both MAGIC and MAGIC_TAG.
    """
    
    MAGIC = None
    MAGIC_TAG = None
    
    def __init__(self, file):
        """
        Performs the translation on __init__
        
        @file:      either the path to a file to translate or a file-like
                    object, in which case the will be '<string>'
        """
        
        if isinstance(file, str):
            self.path = file
            file = self.open(self.path)
        else:
            self.path = '<string>'
        
        lines = []
        self.line_numbers = [0]
        for lineno, line in self.translate(file):
            for i, l in enumerate(line.split('\n'), lineno):
                self.line_numbers.append(i)
                lines.append(l)
        
        self.data = '\n'.join(lines)
    
    def open(self, path):
        """
        Open the file at @path
        """
        
        return tokenize.open(path)
    
    @classmethod
    def eval(cls, string):
        compiled = cls(io.StringIO(string))
        tree = compiled.make_ast_tree()
        code = compile(tree, compiled.path, 'exec')
        return eval(code)
    
    def make_ast_tree(self):
        """
        Returns a modified AST
        
        All it does is modify the line numbers
        so that tracebacks work nicely
        """
        
        line_numbers = self.line_numbers
        
        try:
            tree = ast.parse(self.data, filename = self.path)
        except SyntaxError as e:
            descr, args = e.args
            args = list(args)
            args[1] = line_numbers[e.lineno]
            args[2] = None
            args[3] = linecache.getline(e.filename, args[1]).strip('\n')
            e.__init__(descr, args)
            raise
        
        for node in ast.walk(tree):
            try:
                node.lineno = line_numbers[node.lineno]
            except AttributeError:
                pass
        return tree
    
    def get_source(self, line_numbers = True, original_numbers = False):
        """
        Returns the translated source
        
        If @original_numbers, then line numbers pointing to the original
        source file are used
        """
        
        source = []
        data = self.data.split('\n')
        
        if original_numbers:
            number_width = len(str(max(self.line_numbers)))
            data = zip(self.line_numbers[1:], data)
            template = '{lineno} {line}'
        elif line_numbers:
            number_width = len(str(len(data) - 1))
            data = enumerate(data, 1)
            template = '{lineno} {line}'
        else:
            data = enumerate(data, 1)
            template = '{line}'
            number_width = 0
        
        for lineno, line in data:
            lineno = str(lineno).rjust(number_width)
            source.append(template.format(lineno = lineno, line = line) )
        return '\n'.join(source)
    
    def translate(self, file):
        """
        Translate the contents of file to python
        
        Yields ( line number, line ), where:
            line number refers to the original/untranslated source
            line is the translated python string
        """
        
        for lineno, line in enumerate(file, 1):
            yield lineno, line
