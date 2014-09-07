"""
Tokenisation utilities

full_tokenize() is a modified version of tokenize() available
in the tokenize module

full_tokenize() behaves almost exactly the same as
tokenize.tokenize() except:
    - it preserves whitespace
    
    - it ignores identation (so no all IndentationError,
        any 'indents' are just treated like the
        whitespace in the above point and
        no INDENT/DEDENT tokens)
    
    - no EOF errors from missing closing brackets
        or missing closing string-quotes
    
    - no ENCODING token

Original code from: Lib/tokenize.py
    http://hg.python.org/cpython/file/3.4/Lib/tokenize.py
    See original code for authors and credits


"""

import re
import io
import itertools
import tokenize

def get_until_eol(tokens):
    """
    Yields tokens until it hits EOF, newlines etc.
    """
    end_types = (tokenize.ENDMARKER, tokenize.NL, tokenize.NEWLINE)
    return itertools.takewhile(lambda t: t.type not in end_types, tokens)

__delim_map = {'{': '}', '[': ']', '(': ')'}
def extract_structure(lines):
    """
    Extract the next token in lines or, 
    if beginning with a bracket ([{, extract the string until
    the matching closing bracket }])
    
    lines can be a string
    or an iterable yield lines (remember to keep trailing line endings)
    
    Returns (structure, remainder of last extracted line)
    
    e.g.
    >>> extract_structure('[1, 2, 3] + [4]\\nprint()')
    ('[1, 2, 3] ', '+ [4]')
    
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

def full_tokenize(lines):
    """
    Behaves like tokenize.tokenize()
    
    lines can be any iterable (instead of a readline() method)
    but you should make sure that the line endings are preserved
    If lines is a string, it is automatically wrapped in a
    io.StringIO
    
    Where tokenize.tokenize() raises an error for unterminated
    multi line strings, full_tokenize() just returns the string
    so far in one ERRORTOKEN token
    """
    
    TokenInfo = tokenize.TokenInfo
    
    parenlev = 0
    continued = needcont = False
    numchars = '0123456789'
    contstr = None
    contline = None
    
    lnum = 1
    if isinstance(lines, str):
        lines = io.StringIO(lines)
    for lnum, line in enumerate(lines, 1):
        if not line:
            break
        pos, max = 0, len(line)

        if contstr:                            # continued string
            endmatch = endprog.match(line)
            if endmatch:
                pos = end = endmatch.end(0)
                yield TokenInfo(tokenize.STRING, contstr + line[:end], strstart, (lnum, end), contline + line)
                contstr = contline = None
                needcont = False
            
            elif needcont and line[-2:] != '\\\n' and line[-3:] != '\\\r\n':
                yield TokenInfo(tokenize.ERRORTOKEN, contstr + line, strstart, (lnum, max), contline)
                contstr = contline = None
                continue
            
            else:
                contstr += line
                contline += line
                continue

        elif parenlev == 0 and not continued:  # new statement
            start = (lnum, pos)
            pos = re.search(r'[^ \f\t]|$', line).start()
            if pos == max:
                break

            if line[pos] in '#\r\n':           # skip comments or blank lines
                if line[pos] == '#':
                    comment_token = line[start[1]:].rstrip('\r\n')
                    nl_pos = len(comment_token)
                    yield TokenInfo(tokenize.COMMENT, comment_token, start, (lnum, nl_pos), line)
                    yield TokenInfo(tokenize.NL, line[nl_pos:], (lnum, nl_pos), (lnum, len(line)), line)
                else:
                    yield TokenInfo(tokenize.NL, line[start[1]:], start, (lnum, len(line)), line)
                continue
            pos = 0

        else:                                  # continued statement
            continued = False

        while pos < max:
            pseudomatch = tokenize._compile(tokenize.PseudoToken + r'[ \f\t]*').match(line, pos)
            if pseudomatch:                                # scan for tokens
                start, end = pseudomatch.span(0)
                spos, epos, pos = (lnum, start), (lnum, end), end
                if start == end:
                    continue
                token = pseudomatch.group(0)
                token_stripped = pseudomatch.group(1)
                initial = token_stripped[0]

                if (initial in numchars or                  # ordinary number
                    (initial == '.' and token != '.' and token != '...')):
                    yield TokenInfo(tokenize.NUMBER, token, spos, epos, line)
                
                elif initial in '\r\n':
                    yield TokenInfo((tokenize.NEWLINE, tokenize.NL)[parenlev > 0], token, spos, epos, line)
                
                elif initial == '#':
                    assert not token.endswith("\n")
                    yield TokenInfo(tokenize.COMMENT, token, spos, epos, line)
                
                elif token_stripped in tokenize.triple_quoted:
                    endprog = tokenize._compile(tokenize.endpats[token_stripped] + r'[ \f\t]*')
                    endmatch = endprog.match(line, pos)
                    if endmatch:                           # all on one line
                        pos = endmatch.end(0)
                        token = line[start:pos]
                        yield TokenInfo(tokenize.STRING, token, spos, (lnum, pos), line)
                    else:
                        strstart = (lnum, start)           # multiple lines
                        contstr = line[start:]
                        contline = line
                        break
                
                elif any(i in tokenize.single_quoted for i in (initial, token_stripped[:2], token_stripped[:3])):
                    if token[-1] == '\n':                  # continued string
                        strstart = (lnum, start)
                        endprog = tokenize._compile(tokenize.endpats[initial] or
                                           tokenize.endpats[token[1]] or
                                           tokenize.endpats[token[2]])
                        contstr, needcont = line[start:], True
                        contline = line
                        break
                    
                    # ordinary string
                    yield TokenInfo(tokenize.STRING, token, spos, epos, line)
                
                elif initial.isidentifier():               # ordinary name
                    yield TokenInfo(tokenize.NAME, token, spos, epos, line)
                
                elif initial == '\\':                      # continued stmt
                    continued = True
                
                else:
                    if initial in '([{':
                        parenlev += 1
                    elif initial in ')]}':
                        parenlev -= 1
                    yield TokenInfo(tokenize.OP, token, spos, epos, line)
            
            else:
                yield TokenInfo(tokenize.ERRORTOKEN, line[pos], (lnum, pos), (lnum, pos+1), line)
                pos += 1
    
    if contstr:                            # continued string
        yield TokenInfo(tokenize.ERRORTOKEN, contstr, strstart, (lnum, max), contline)

__all__ = ['extract_structure', 'full_tokenize']
