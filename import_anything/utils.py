"""
Utilities for parsing
"""

import re

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
