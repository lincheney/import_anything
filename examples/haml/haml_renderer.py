import contextlib
import itertools
import collections

class Stack:
    _indent = ' ' * 2
    VOID_ELEMENTS = {'meta', 'img', 'link', 'br', 'hr', 'input', 'area', 'param', 'col', 'base'}
    
    def __init__(self):
        self.text = []
        self.indent = 0
    
    @classmethod
    def combine_attribute(cls, key, values, attributes):
        if values:
            yield from map(str, values)
        
        new_values = attributes.get(key)
        yield from cls.filter_attribute((new_values,))
    
    @classmethod
    def filter_attribute(cls, values):
        """
        attempt to emulate ruby-style haml as best as possible
        flatten, stringify but don't yield None,False
        """
        for v in values:
            if v is None or v is False:
                continue
            elif isinstance(v, str):
                yield v
            elif isinstance(v, (list, tuple)):
                yield from cls.filter_attribute(v)
            else:
                yield str(v)
    
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
    
    def add_comment(self, comment):
        self.text.append(self.indented('<!--{} -->'.format(comment)))
    
    @contextlib.contextmanager
    def add_comment_tag(self):
        self.text.append(self.indented('<!--'))
        self.indent += 1
        yield
        self.indent -= 1
        self.text.append(self.indented('-->'))
    
    @contextlib.contextmanager
    def add_tag(self, name, text, classes, ids, attributes, void):
        attributes = attributes or {}
        
        cls = ' '.join(self.combine_attribute('class', classes, attributes))
        if cls:
            attributes['class'] = cls
        id = '_'.join(self.combine_attribute('id', ids, attributes))
        if id:
            attributes['id'] = id
        
        attributes_list = []
        for k, v in attributes.items():
            if v is False:
                continue
            elif v is True:
                attributes_list.append(' {}'.format(k))
            elif k == 'data' and isinstance(v, dict):
                for suffix, value in v.items():
                    attributes_list.append(' data-{}={!r}'.format(suffix.replace('_', '-'), str(value)))
            else:
                attributes_list.append(' {}={!r}'.format(k, str(v)))
        attributes_string = ''.join(attributes_list)
        
        # place holder for open tag
        index = len(self.text)
        self.text.append(None)
        
        self.indent += 1
        if text != '':
            self.text.append(self.indented(text))
        
        yield
        
        self.indent -= 1
        
        if len(self.text) == index + 1:
            if void or name in self.VOID_ELEMENTS:
                self.text[index] = self.indented('<{}{}>'.format(name, attributes_string))
            else:
                self.text[index] = self.indented('<{}{}></{}>'.format(name, attributes_string, name))
            return
        
        open_tag = self.indented('<{}{}>'.format(name, attributes_string))
        close_tag = '</{}>'.format(name)
        
        if len(self.text) == index + 2 and text != '' and not self.is_tag(index + 1):
            # only one text child
            self.text[index + 1] = '{}{}{}'.format(open_tag, self.text[index + 1].lstrip(), close_tag)
        
        else:
            # some child is a tag
            # put open tag in placeholder
            self.text[index] = open_tag
            self.text.append(self.indented(close_tag))
    
    def render(self):
        return '\n'.join(i for i in self.text if i is not None)
