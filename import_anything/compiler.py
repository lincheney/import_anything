import ast
import re

class Compiler:
    def __init__(self, path):
        file = self.open(path)
        
        lines = []
        self.line_numbers = [0]
        for lineno, line in self.translate(file):
            for i, l in enumerate(line.split('\n'), lineno):
                self.line_numbers.append(i)
                lines.append(l)
        
        self.data = '\n'.join(lines)
    
    def open(self, path):
        return open(path, 'rb')
    
    def make_ast_tree(self):
        tree = ast.parse(self.data)
        for node in ast.walk(tree):
            try:
                node.lineno = self.line_numbers[node.lineno]
            except AttributeError:
                pass
        return tree
    
    def dump_source(self):
        for lineno, line in enumerate(self.data.split('\n'), 1):
            print('{:2} {}'.format(lineno, line) )
    
    def translate(self, file):
        for lineno, line in enumerate(file, 1):
            yield lineno, line
    
    def indent(self, indent, string, *args, **kwargs):
        return (" " * indent) + string.format(*args, **kwargs)
    
    def strip_indents(self, string):
        match = re.match(r"^(\s*)(.*)$", string, re.S)
        return len(match.group(1)), match.group(2)
