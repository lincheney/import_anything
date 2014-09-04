import import_anything
from import_anything import utils
import re

class HamlCompiler(import_anything.Compiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.get_source(original_numbers = True))
    
    @utils.complete_blocks()
    def translate(self, file, block):
        lineno = 0
        yield lineno, 'import haml_renderer'
        yield lineno, block('def render():')
        yield lineno, utils.indent(2, 'stack = haml_renderer.Stack()')
        
        for lineno, line in enumerate(file, 1):
            indent, line = utils.strip_indents(line.rstrip('\n'))
            indent += 2
            
            if line.startswith('%'):
                for l in self.handle_tag(line[1:].lstrip(), block):
                    yield lineno, utils.indent(indent, l)
        
        yield lineno, utils.indent(2, 'return stack.render()')
    
    def handle_tag(self, string, block):
        tag, string = re.match(r'([\w.#]*)(.*)', string).groups()
        
        classes = []
        ids = []
        tag, *rest = re.split(r'([#.])', tag)
        tag = tag or 'div'
        for prefix, name in zip(rest[::2], rest[1::2]):
            if prefix == '.':
                classes.append(name)
            elif prefix == '#':
                ids.append(name)
        
        string = repr(string)
        yield block('with stack.add_tag({!r}, {}, {!r}, {!r}):'.format(tag, string, tuple(classes), tuple(ids)))

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = True)
import_anything.Finder.register(loader, ['.haml'])

import main_haml
print(main_haml.render())
