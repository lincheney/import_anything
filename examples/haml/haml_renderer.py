import contextlib

class Stack:
    _indent = ' ' * 2
    VOID_ELEMENTS = {'meta', 'img', 'link', 'br', 'hr', 'input', 'area', 'param', 'col', 'base'}
    
    def __init__(self):
        self.text = []
        self.indent = 0
    
    def is_tag(self, index):
        # its a tag if None (if it were text it would have been assigned)
        if self.text[index] is None:
            return True
        # tag if angled bracket
        if self.text[index].lstrip().startswith('<'):
            return True
        return False
    
    def indented(self, string):
        return '{}{}'.format(self.indent * self._indent, string)
    
    def add_text(self, text):
        self.text.append(self.indented(text))
    
    @contextlib.contextmanager
    def add_tag(self, name, text, classes, ids, attributes):
        attributes = attributes or {}
        
        if classes:
            class_ = attributes.get('class')
            if class_:
                classes += (class_,)
            attributes['class'] = ' '.join(classes)
        
        if ids:
            id = attributes.get('id')
            if id:
                ids += (id_,)
            attributes['id'] = '_'.join(ids)
        
        attributes_string = ''.join(' {}={!r}'.format(k, str(v)) for k, v in attributes.items())
        
        # place holder for open tag
        index = len(self.text)
        self.text.append(None)
        
        self.indent += 1
        if text != '':
            self.text.append(self.indented(text))
        
        yield
        
        self.indent -= 1
        
        if len(self.text) == index + 1:
            if name in self.VOID_ELEMENTS:
                self.text[index] = self.indented('<{}{}>'.format(name, attributes_string))
            else:
                self.text[index] = self.indented('<{}{}></{}>'.format(name, attributes_string, name))
            return
        
        open_tag = self.indented('<{}{}>'.format(name, attributes_string))
        close_tag = '</{}>'.format(name)
        
        if len(self.text) == index + 2 and not self.is_tag(index + 1):
            # only one text child
            self.text[index + 1] = '{}{}{}'.format(open_tag, self.text[index + 1].lstrip(), close_tag)
        
        else:
            # some child is a tag
            # put open tag in placeholder
            self.text[index] = open_tag
            self.text.append(self.indented(close_tag))
    
    def render(self):
        return '\n'.join(i for i in self.text if i is not None)
