"""
Utilities for parsing
"""

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

from .complete_blocks import *
from .tokenizer import *
