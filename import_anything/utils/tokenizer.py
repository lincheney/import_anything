import re
import itertools
import tokenize

def line_generator(lines):
    """
    except for the last line, ensures each line has a \n
    """
    
    lines = iter(lines)
    prev = next(lines, None)
    while prev is not None:
        l = next(lines, None)
        # don't tack on a \n if it has one or is last line
        if l is None or prev.endswith('\n'):
            yield prev
        else:
            yield prev + '\n'
        prev = l

def get_until_eol(tokens):
    """
    Yields tokens until it hits EOF, newlines etc.
    """
    end_types = (tokenize.ENDMARKER, tokenize.NL, tokenize.NEWLINE)
    return itertools.takewhile(lambda t: t.type not in end_types, tokens)

def full_tokenize(lines):
    """
    Same as tokenize.generate_tokens() but non-trailing whitespace is preserved so that
    ''.join(t.string for t in full_tokenize(line)) == ''.join(lines).rstrip()
    
    Trailing whitespace WILL be removed
    """
    
    line_store = []
    readline = line_generator(lines)
    readline = iter(readline).__next__
    
    tokens = tokenize.generate_tokens(readline)
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
            
            tail = token.line[len(token.string):]
            if tail.isspace():
                token = token._replace(string = string + tail, end = (token.end[0], token.end[1] + len(tail)))
            
            yield token
            prev_pos = token.end
    except tokenize.TokenError as e:
        if e.args[0] == 'EOF in multi-line statement':
            return
        
        if e.args[0] == 'EOF in multi-line string':
            #vars = inspect.trace()[-1][0].f_locals
            #print(vars)
            #t = tokenize.TokenInfo(tokenize.ERRORTOKEN, vars['contstr'],
                #prev_pos, (vars['lnum'] - 1, vars['end']), vars['contline'])
            #print(t)
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

__all__ = ['extract_structure', 'full_tokenize']
