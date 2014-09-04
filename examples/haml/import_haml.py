"""
Compiles (python-style) Haml into (basic) Python that
renders the appropriate html

Just do:
    import haml_module
    output = haml_module.render(text = 'Some text', title = 'The Title')
    print(output)
"""

import import_anything
from import_anything import utils
import itertools
import re

class HamlCompiler(import_anything.Compiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.get_source(original_numbers = True))
    
    @utils.complete_blocks()
    def translate(self, file, block):
        lineno = 0
        # wrap all the code in a _render function
        yield lineno, block('def _render():')
        yield lineno, utils.indent(2, 'import haml_renderer')
        yield lineno, utils.indent(2, 'stack = haml_renderer.Stack()')
        
        for lineno, line in enumerate(file, 1):
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
                
                tag = tag or 'div'
                
                attributes = None
                if string.startswith('{'):
                    # grab the dict-style attributes
                    # since it may be multiline, we need to give it the
                    # other lines from the file too
                    gen = iter(itertools.chain([string + '\n'], file))
                    attributes, string = utils.extract_structure(gen.__next__)
                
                # the text
                if string.startswith('='):
                    string = string[1:]
                else:
                    string = repr(string)
                
                line = utils.indent(indent, 'with stack.add_tag({!r}, {}, {!r}, {!r}, {}):', tag, string, tuple(classes), tuple(ids), attributes)
                yield lineno, block(line)
            
            else:
                # text line
                if line.startswith('='):
                    line = line[1:]
                elif line.startswith('\\'):
                    line = repr(line[1:])
                else:
                    line = repr(line)
                
                yield lineno, utils.indent(indent, 'stack.add_text({})', line)
        
        # render the tags
        yield lineno, utils.indent(2, 'return stack.render()')
        # magic to allow using **kwargs as if they were locals
        yield lineno, 'render = lambda **kwa: eval(_render.__code__, kwa)'

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = True)
import_anything.Finder.register(loader, ['.haml'])

if __name__ == '__main__':
    import main_haml
    haml = main_haml.render(
        title = 'MyPage',
        item = dict(type = 'massive', number = 4, urgency = 'urgent'),
        sortcol = None,
        sortdir = '/tmp',
    )
    print(haml)
