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
            data = zip(self.line_numbers[1:], data)
            template = '{lineno} {line}'
            number_width = len(str(max(self.line_numbers)))
        elif line_numbers:
            data = enumerate(data, 1)
            template = '{lineno} {line}'
            number_width = len(str(len(data) - 1))
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
