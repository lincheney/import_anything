import functools
from . import strip_indents, indent

def complete_blocks(indent_by = 4, body = 'pass'):
    """
    Decorator to wrap Compiler.translate. Use like this:

    class Compiler:
        @complete_blocks(indent_by = 2)
        def translate(self, file, block):
            yield 1, 'normal_line'
            yield 2, block('def start_a_block():')
            yield 3, 'unexpected_dedent'
            ...

    complete_blocks will notice you had an empty block after
    line #2 and insert a pass statement there, so you end up with:

    normal_line
    def start_a_block():
    pass
    unexpected_dedent

    """
    return functools.partial(Block.decorator, indent_by = indent_by, body = body)

class Block(str):
    @staticmethod
    def decorator(function, indent_by, body):
        @functools.wraps(function)
        def wrapped_fn(*args, **kwargs):
            call = function(*(args + (Block,)), **kwargs)
            
            block_indent = -1
            line_indent = 0
            last_lineno = 0
            for lineno, string in call:
                line_indent = strip_indents(string)[0]
                
                if block_indent >= line_indent:
                    yield last_lineno, indent(block_indent + indent_by, body)
                block_indent = -1
                
                if isinstance(string, Block):
                    block_indent = line_indent
                yield lineno, str(string)
                last_lineno = lineno
            
            if block_indent >= line_indent:
                yield lineno, indent(block_indent + indent_by, body)
        
        return wrapped_fn

__all__ = ['complete_blocks', 'Block']
