"""
Compiles (python-style) Haml into (basic) Python that
renders the appropriate html

Just do:
    import haml_module
    output = haml_module.render(text = 'Some text', title = 'The Title', **other_variables)
    print(output)
"""

import import_anything
from import_anything import utils
import itertools
import re
import tokenize
from .haml_renderer import Stack

class HamlCompiler(import_anything.Compiler):
    MAGIC = 52
    MAGIC_TAG = 'haml'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.get_source(original_numbers = True))
    
    def parse_html_attributes(self, string):
        """
        parse html style attributes
        e.g. (id=5 class=visible)
        Yields key,value pairs
        """
        
        string = string[1:-1].replace('\n', ' ')
        while string:
            index = string.find('=')
            if index == -1:
                yield string, 'True'
                return
            
            key = string[:index]
            string = string[len(key) + 1:]
            key = key.strip()
            
            value = []
            while string:
                v, string = utils.extract_structure(string)
                value.append(v)
                if v.endswith(' '):
                    break
            value = ''.join(value)
            
            yield key, value
    
    @utils.complete_blocks()
    def translate(self, file, block):
        """
        keep track of line numbers automatically
        """
        
        self.lineno = 0
        def line_generator():
            for lineno, line in enumerate(file, 1):
                self.lineno = lineno
                yield line
        
        for line in self._translate(line_generator(), block):
            if isinstance(line, tuple):
                yield line
            else:
                yield self.lineno, line
    
    def get_multiline(self, lines):
        eol = (tokenize.ENDMARKER, tokenize.NEWLINE)
        tokens = utils.get_until_eol(utils.full_tokenize(lines), eol)
        return ''.join(t.string for t in tokens)
    
    def _translate(self, _lines, block):
        # wrap all the code in a _render function
        yield 'import sys'
        yield 'Stack = sys.modules[{!r}].Stack'.format(__name__)
        yield block('def _render():')
        
        for line in _lines:
            indent, line = utils.strip_indents(line.rstrip('\n'))
            indent += 2
            
            if line and line[0] in ('%', '#', '.'):
                # a tag; strip % if necessary
                if line.startswith('%'):
                    line = line[1:]
                
                tag, string = re.match(r'([\w.#]*)(.*)', line.lstrip()).groups()
                
                # extract the .class#id
                classes = []
                ids = []
                tag, *rest = re.split(r'([#.])', tag)
                for prefix, name in zip(rest[::2], rest[1::2]):
                    if prefix == '.':
                        classes.append(name)
                    elif prefix == '#':
                        ids.append(name)
                
                # default to div
                tag = tag or 'div'
                
                # extract the attributes, both dict- and html-style
                lineno = self.lineno
                attributes = []
                while string and string[0] in ('{', '('):
                    gen = itertools.chain([string + '\n'], _lines)
                    attrs, string = utils.extract_structure(gen)
                    
                    attrs = attrs.strip()
                    if attrs.startswith('('):
                        attrs = ', '.join('{!r}:{}'.format(k, v) for k, v in self.parse_html_attributes(attrs))
                        attrs = '{' + attrs + '}'
                    attributes.append(attrs)
                
                # assign all the attributes
                if attributes:
                    yield lineno, utils.indent(indent, '__attributes = {}')
                    for a in attributes:
                        yield lineno, utils.indent(indent, '__attributes.update({})', a)
                else:
                    yield lineno, utils.indent(indent, '__attributes = None')
                
                # void tag
                void = False
                if string.startswith('/'):
                    string = string[1:]
                    void = True
                
                # the text
                lineno = self.lineno
                escape = False
                inline_text = True
                if string.startswith('='):
                    # make sure to handle multiline code
                    gen = itertools.chain([string[1:] + '\n'], _lines)
                    string = ''.join(self.get_multiline(gen))
                    escape = True
                else:
                    string = string.lstrip()
                    inline_text = bool(string)
                    string = repr(string)
                
                if void or inline_text:
                    template = '__stack.add_tag({tag!r}, {text}, {classes!r}, {ids!r}, void = {void!r}, attributes = __attributes, escape = {escape}, inline_text = {inline_text!r})'
                
                else:
                    template = 'with __stack.add_tag_context({tag!r}, {text}, {classes!r}, {ids!r}, attributes = __attributes, escape = {escape}):'
                
                line = utils.indent(indent, template,
                    tag = tag,
                    text = string,
                    classes = tuple(classes),
                    ids = tuple(ids),
                    void = void,
                    escape = escape,
                    inline_text = inline_text,
                )
                if not (void or inline_text):
                    line = block(line)
                yield lineno, line
            
            elif line.startswith('/'):
                # comment
                if line[1:].strip():
                    # one line comment
                    yield utils.indent(indent, '__stack.add_comment({!r})', line[1:])
                else:
                    # comment with nested text
                    yield block(utils.indent(indent, 'with __stack.add_comment_tag():'))
            
            elif not line:
                pass
            
            else:
                match = re.match(r'[=-]|([&!]=)', line)
                if match:
                    lineno = self.lineno
                    initial = match.group(0)
                    # python code; make sure to handle multiline code
                    gen = itertools.chain([line[match.end(0):].lstrip() + '\n'], _lines)
                    line = ''.join(self.get_multiline(gen))
                    
                    if initial == '=':
                        yield lineno, utils.indent(indent, '__stack.add_text({})', line)
                    elif initial == '&=':
                        yield lineno, utils.indent(indent, '__stack.add_text({}, escape = True)', line)
                    elif initial == '!=':
                        yield lineno, utils.indent(indent, '__stack.add_text({}, escape = False)', line)
                    else:
                        yield lineno, utils.indent(indent, line)
                
                else:
                    # text line
                    if line.startswith('\\'):
                        line = line[1:]
                    
                    yield utils.indent(indent, '__stack.add_text({!r}, escape = False)', line)
        
        self.lineno += 1
        # render the tags
        yield utils.indent(2, 'return __stack')
        # magic to allow using **kwargs as if they were locals
        yield '''
def render(**kwargs):
    kwargs.setdefault('__stack', Stack())
    kwargs['__package__'] = __package__
    kwargs['__name__'] = __name__
    kwargs['__render__'] = lambda x: x.subrender(**kwargs)
    return eval(_render.__code__, kwargs).render()

def subrender(*, __stack, **kwargs):
    kwargs.setdefault('__stack', Stack())
    kwargs['__package__'] = __package__
    kwargs['__name__'] = __name__
    kwargs['__render__'] = lambda x: x.subrender(**kwargs)
    __stack.extend(eval(_render.__code__, kwargs))
'''

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = False)
import_anything.Finder.register(loader, ['.haml'])
