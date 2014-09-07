import contextlib
import itertools
import collections
from html import escape as escape_html

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
    
    def indent_text(self, text):
        return ''.join(self.indented(i) for i in text.splitlines(True))
    
    def add_text(self, text, escape = True):
        if escape:
            text = escape_html(str(text))
        self.text.append(self.indent_text(text))
    
    def add_comment(self, comment):
        self.text.append(self.indented('<!--{} -->'.format(comment)))
    
    @contextlib.contextmanager
    def add_comment_tag(self):
        self.text.append(self.indented('<!--'))
        self.indent += 1
        yield
        self.indent -= 1
        self.text.append(self.indented('-->'))
    
    def add_tag(self, name, text, classes, ids, attributes, void = False, escape = True, inline_text = False):
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
                    attributes_list.append(' data-{}={!r}'.format(suffix.replace('_', '-'), escape_html(str(value))))
            else:
                attributes_list.append(' {}={!r}'.format(k, escape_html(str(v))))
        attributes_string = ''.join(attributes_list)
        
        # place holder for open tag
        self.text.append(None)
        
        open_tag = self.indented('<{}{}>'.format(name, attributes_string))
        close_tag = '</{}>'.format(name)
        
        if inline_text:
            if escape:
                text = escape_html(str(text))
            text = self.indent_text(text).lstrip()
            self.text[-1] = '{}{}{}'.format(open_tag, text, close_tag)
        
        elif void or name in self.VOID_ELEMENTS:
            self.text[-1] = self.indented('<{}{}>'.format(name, attributes_string))
        
        return open_tag, close_tag
    
    @contextlib.contextmanager
    def add_tag_context(self, name, *args, **kwargs):
        open_tag, close_tag = self.add_tag(name, *args, **kwargs)
        index = len(self.text) - 1
        
        self.indent += 1
        yield
        self.indent -= 1
        
        if len(self.text) != index + 1:
            # put open tag in placeholder
            self.text[index] = open_tag
            self.text.append(self.indented(close_tag))
        
        elif name not in self.VOID_ELEMENTS:
            self.text[index] = '{}{}'.format(open_tag, close_tag)
    
    def render(self):
        return '\n'.join(i for i in self.text if i is not None)
