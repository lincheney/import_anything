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

class HamlCompiler(import_anything.Compiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.get_source(original_numbers = True))
    
    def parse_html_attributes(self, string):
        """
        parse html style attributes
        e.g. (id=5 class=visible)
        Yields key,value pairs
        """
        
        string = string[1:-1]
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
            yield self.lineno, line
    
    def get_multiline(self, lines):
        eol = (tokenize.ENDMARKER, tokenize.NEWLINE)
        tokens = utils.get_until_eol(utils.full_tokenize(lines), eol)
        return ''.join(t.string for t in tokens)
    
    def _translate(self, _lines, block):
        # wrap all the code in a _render function
        yield block('def _render():')
        yield utils.indent(2, 'import haml_renderer')
        yield utils.indent(2, 'stack = haml_renderer.Stack()')
        
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
                attributes = []
                while string and string[0] in ('{', '('):
                    gen = itertools.chain([string + '\n'], _lines)
                    attrs, string = utils.extract_structure(gen)
                    
                    attrs = attrs.strip()
                    if attrs.startswith('('):
                        attrs = ', '.join('{!r}:{}'.format(k, v) for k, v in self.parse_html_attributes(attrs))
                        attrs = '{' + attrs + '}'
                    attributes.append(attrs)
                
                # void tag
                void = False
                if string.startswith('/'):
                    string = string[1:]
                    void = True
                
                # assign all the attributes
                if attributes:
                    yield utils.indent(indent, 'attributes = {}')
                    for a in attributes:
                        yield utils.indent(indent, 'attributes.update({})', a)
                else:
                    yield utils.indent(indent, 'attributes = None')
                
                # the text
                if string.startswith('='):
                    # make sure to handle multiline code
                    gen = itertools.chain([string[1:] + '\n'], _lines)
                    string = ''.join(self.get_multiline(gen))
                else:
                    string = repr(string)
                
                template = 'with stack.add_tag({tag!r}, {text}, {classes!r}, {ids!r}, void = {void!r}, attributes = attributes):'
                line = utils.indent(indent, template,
                    tag = tag,
                    text = string,
                    classes = tuple(classes),
                    ids = tuple(ids),
                    void = void,
                )
                yield block(line)
            
            elif line.startswith('/'):
                # comment
                if line[1:].strip():
                    # one line comment
                    yield utils.indent(indent, 'stack.add_comment({!r})', line[1:])
                else:
                    # comment with nested text
                    yield block(utils.indent(indent, 'with stack.add_comment_tag():'))
            
            elif line.startswith('=') or line.startswith('-'):
                # python code; make sure to handle multiline code
                gen = itertools.chain([line[1:].lstrip() + '\n'], _lines)
                line = ''.join(self.get_multiline(gen))
                if line.startswith('-'):
                    yield utils.indent(indent, 'stack.add_text({}, escape = True)', line)
                else:
                    yield utils.indent(indent, line)
            
            elif line:
                # text line
                if line.startswith('\\'):
                    line = line[1:]
                
                yield utils.indent(indent, 'stack.add_text({!r})', line)
        
        self.lineno += 1
        # render the tags
        yield utils.indent(2, 'return stack.render()')
        # magic to allow using **kwargs as if they were locals
        yield 'render = lambda **kwa: eval(_render.__code__, kwa)'

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = True)
import_anything.Finder.register(loader, ['.haml'])

if __name__ == '__main__':
    import main_haml
    
    haml = main_haml.render(
        title = 'MyPage',
        item = dict(type = 'massive', number = 4, urgency = 'urgent'),
        sortcol = None,
        sortdir = '/tmp',
        href = '/index.html#more-stuff',
        link = dict(href = '#'),
        article = dict(number = 27, visibility = 'visible'),
        link_to_remote = lambda *a, **kwa: None,
        product = dict(id = 3),
    )
    print(haml)
