import contextlib

class Stack:
    _indent = ' ' * 2
    
    def __init__(self):
        self.text = []
        self.indent = 0
    
    def indented(self, string):
        return '{}{}'.format(self.indent * self._indent, string)
    
    def add_text(self, text):
        self.text.append(self.indented(text))
    
    @contextlib.contextmanager
    def add_tag(self, name, text):
        self.text.append(self.indented('<{}>'.format(name)))
        
        self.indent += 1
        if text != '':
            self.text.append(self.indented(text))
        
        yield
        
        self.indent -= 1
        
        self.text.append(self.indented('</{}>'.format(name)))
    
    def render(self):
        return '\n'.join(self.text)
