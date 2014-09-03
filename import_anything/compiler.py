import ast
import re
import linecache
import tokenize

class Compiler:
    """
    Source-to-python compiler
    
    Subclasses should reimplement the .translate method
    and possibly set the MAGIC and MAGIC_TAG values
    """
    
    MAGIC = None
    MAGIC_TAG = None
    
    def __init__(self, path):
        """
        Performs the translation on __init__
        
        @path:      the path to the file to translate
        """
        
        self.path = path
        file = self.open(path)
        
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
            args[3] = linecache.getline(e.filename, args[1])
            e.__init__(descr, args)
            raise
        
        for node in ast.walk(tree):
            try:
                node.lineno = line_numbers[node.lineno]
            except AttributeError:
                pass
        return tree
    
    def dump_source(self):
        """
        Print the translated source with line numbers
        """
        
        for lineno, line in enumerate(self.data.split('\n'), 1):
            print('{:2} {}'.format(lineno, line) )
    
    def translate(self, file):
        """
        Translate the contents of file to python
        
        Yields ( line number, line ), where:
            line number refers to the original/untranslated source
            line is the translated python string
        """
        
        for lineno, line in enumerate(file, 1):
            yield lineno, line
