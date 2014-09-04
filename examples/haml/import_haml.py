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
        yield lineno, block('def _render():')
        yield lineno, utils.indent(2, 'import haml_renderer')
        yield lineno, utils.indent(2, 'stack = haml_renderer.Stack()')
        
        for lineno, line in enumerate(file, 1):
            indent, line = utils.strip_indents(line.rstrip('\n'))
            indent += 2
            
            if line and line[0] in ('%', '#', '.'):
                if line.startswith('%'):
                    line = line[1:]
                
                tag, string = re.match(r'([\w.#]*)(.*)', line.lstrip()).groups()
                
                classes = []
                ids = []
                tag, *rest = re.split(r'([#.])', tag)
                tag = tag or 'div'
                for prefix, name in zip(rest[::2], rest[1::2]):
                    if prefix == '.':
                        classes.append(name)
                    elif prefix == '#':
                        ids.append(name)
                
                attributes = None
                if string.startswith('{'):
                    attributes, string = utils.extract_structure(string)
                
                if string.startswith('='):
                    string = string[1:]
                else:
                    string = repr(string)
                
                line = utils.indent(indent, 'with stack.add_tag({!r}, {}, {!r}, {!r}, {}):', tag, string, tuple(classes), tuple(ids), attributes)
                yield lineno, block(line)
            
            else:
                if line.startswith('='):
                    line = line[1:]
                elif line.startswith('\\'):
                    line = repr(line[1:])
                else:
                    line = repr(line)
                yield lineno, utils.indent(indent, 'stack.add_text({})', line)
        
        yield lineno, utils.indent(2, 'return stack.render()')
        yield lineno, 'render = lambda **kwa: eval(_render.__code__, kwa)'

loader = import_anything.Loader.factory(compiler = HamlCompiler, recompile = True)
import_anything.Finder.register(loader, ['.haml'])

import main_haml
haml = main_haml.render(
    post_title = 'Title',
    post_subtitle = 'subtitle',
    post_content = 'content',
    title = 'MyPage',
)
print(haml)
