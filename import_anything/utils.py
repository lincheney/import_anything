"""
Utilities for parsing
"""

import functools
import re
import tokenize
from io import StringIO

def indent(indent, string, *args, **kwargs):
    if args or kwargs:
        string = string.format(*args, **kwargs)
    return (' ' * indent) + string

def strip_indents(string):
    """
    Returns ( len(leading whitespace), rest of string )
    """
    
    match = re.match(r'^(\s*)(.*)$', string)
    return match.end(1), match.group(2)


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
            for lineno, string in call:
                line_indent = strip_indents(string)[0]
                
                if block_indent >= line_indent:
                    yield lineno - 1, indent(block_indent + indent_by, body)
                block_indent = -1
                
                if isinstance(string, Block):
                    block_indent = line_indent
                yield lineno, str(string)
            
            if block_indent >= line_indent:
                yield lineno, indent(block_indent + indent_by, body)
        
        return wrapped_fn


def full_tokenize(lines):
    """
    Same as tokenize.generate_tokens() but non-trailing whitespace is preserved so that
    ''.join(t.string for t in full_tokenize(line)) == ''.join(lines).rstrip()
    
    Trailing whitespace WILL be removed
    """
    
    tokens = tokenize.generate_tokens(lines)
    prev_pos = (-1, -1)
    for token in tokens:
        if prev_pos[0] != token.start[0]:
            # new line: extend to start of line
            string = token.line[ : token.start[1]] + token.string
            token = token._replace(string = string, start = (token.start[0], 0))
        
        elif prev_pos[1] != token.start[1]:
            # old line: extend to start of previous token
            string = token.line[prev_pos[1] : token.start[1]] + token.string
            token = token._replace(string = string, start = prev_pos)
        
        yield token
        prev_pos = token.end


__delim_map = {'{': '}', '[': ']', '(': ')'}
def extract_structure(string):
    """
    Extract the the structure (string/tuple/list/dict etc.) at the start of @string
    Returns (structure, rest of string)
    
    e.g.
    extract_structure('[1, 2, 3] + [4]') == ('[1, 2, 3]', ' + [4]')
    
    Raises an error if it doesn't start with a structure or some other
    tokenization error (e.g. no matching brackets, bad indentation)
    """
    
    stack = []
    tokens = full_tokenize(StringIO(string).readline)
    
    try:
        token = next(tokens)
    except StopIteration:
        pass
    else:
        if token.type == tokenize.STRING:
            rest = string[token.start[1] + len(token.string):]
            return token.string, rest
        stripped = token.string.strip()
        if stripped in __delim_map:
            stack.append(__delim_map[stripped])
    
    if not stack:
        raise ValueError('String did not start with structure: {}'.format(string))
    
    struct = [token.string]
    
    for token in tokens:
        struct.append(token.string)
        stripped = token.string.strip()
        
        if stripped in __delim_map:
            stack.append(__delim_map[stripped])
        elif stripped == stack[-1]:
            stack.pop()
            if not stack:
                struct = ''.join(struct)
                return struct, string[len(struct):]
    
    raise ValueError('String did not start with structure: {}'.format(string))
