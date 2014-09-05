"""
Utilities for parsing
"""

import functools
import itertools
import re
import tokenize
from io import StringIO

def indent(indent, string, *args, **kwargs):
    if args or kwargs:
        string = string.format(*args, **kwargs)
    output = (' ' * indent) + string
    if isinstance(string, Block):
        return Block(output)
    return output

def strip_indents(string):
    """
    Returns ( len(leading whitespace), rest of string )
    """
    
    rest = string.lstrip()
    return (len(string) - len(rest)), rest


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
    try:
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
    except tokenize.TokenError as e:
        if e.args[0] == 'EOF in multi-line statement':
            return
        raise


__delim_map = {'{': '}', '[': ']', '(': ')'}
def extract_structure(lines):
    """
    Extract the next token in lines
    If the next token is an opening bracket, it extracts up to the next matching
    bracket
    @lines should be a callable returning lines
    Returns (structure, remainder of last extracted line)
    
    e.g.
    extract_structure('[1, 2, 3] + [4]\nprint()') == ('[1, 2, 3]', ' + [4]')
    
    Note that the last line, print(), wasn't returned since the structure
    ended on the previous line
    """
    
    stack = []
    struct = []
    tokens = full_tokenize(lines)
    
    for token in tokens:
        struct.append(token.string)
        stripped = token.string.strip()
        
        if stripped in __delim_map:
            stack.append(__delim_map[stripped])
        elif stack and stripped == stack[-1]:
            stack.pop()
        
        if not stack:
            break
    
    struct = ''.join(struct)
    remainder = ''.join(i.string for i in get_until_eol(tokens))
    return struct, remainder

def get_until_eol(tokens):
    """
    Yields tokens until it hits EOF, newlines etc.
    """
    end_types = (tokenize.ENDMARKER, tokenize.NL, tokenize.NEWLINE)
    return itertools.takewhile(lambda t: t.type not in end_types, tokens)
