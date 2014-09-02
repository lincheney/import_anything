import ast
import re

class Compiler:
    """
    Source-to-python compiler
    
    Subclasses should reimplement the .translate method
    """
    
    def __init__(self, path):
        """
        Performs the translation on __init__
        
        @path:      the path to the file to translate
        """
        
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
        
        return open(path, 'r')
    
    def make_ast_tree(self):
        """
        Returns a modified AST
        
        All it does is modify the line numbers
        so that tracebacks work nicely
        """
        
        line_numbers = self.line_numbers
        
        tree = ast.parse(self.data)
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
    
    @staticmethod
    def indent(indent, string, *args, **kwargs):
        return (" " * indent) + string.format(*args, **kwargs)
    
    @staticmethod
    def strip_indents(string):
        """
        Returns ( len(leading whitespace), rest of string )
        """
        
        match = re.match(r"^(\s*)(.*)$", string, re.S)
        return len(match.group(1)), match.group(2)
