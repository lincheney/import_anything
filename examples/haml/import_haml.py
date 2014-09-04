import import_anything
from import_anything import utils

class HamlCompiler(import_anything.Compiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(self.get_source())
    
    @utils.complete_blocks()
    def translate(self, file, block):
        lineno = 0
        yield lineno, 'import haml_renderer'
        yield lineno, block('def render():')
        yield lineno, utils.indent(2, 'stack = haml_renderer.Stack()')
        
        for lineno, line in enumerate(file):
            indent, line = utils.strip_indents(line.rstrip('\n'))
            indent += 2
            
            if line.startswith('%'):
                line = utils.indent(indent, 'with stack.add_tag({!r}, ""):', line[1:].lstrip())
                yield lineno, block(line)
        
        yield lineno, utils.indent(2, 'return stack.render()')

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = True)
import_anything.Finder.register(loader, ['.haml'])

import main_haml
print(main_haml.render())
