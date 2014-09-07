"""
Tests for import_anything.utils.extract_structure

Brackets
    >>> extract_structure('{} + 1')
    ('{} ', '+ 1')
    >>> extract_structure('[] + 1')
    ('[] ', '+ 1')
    >>> extract_structure('() + 1')
    ('() ', '+ 1')

Strings
    >>> extract_structure('"string" + 1')
    ('"string" ', '+ 1')
    >>> extract_structure('r"string" + 1')
    ('r"string" ', '+ 1')
    >>> extract_structure("''' multiline \\n string''' + other stuff")
    ("''' multiline \\n string''' ", '+ other stuff')

Other tokens
    >>> extract_structure('name thing')
    ('name ', 'thing')
    >>> extract_structure('1234.56 number')
    ('1234.56 ', 'number')
    >>> extract_structure('-operator')
    ('-', 'operator')
    >>> extract_structure('# comment')
    ('# comment', '')

Extra lines
    >>> extract_structure('line 1\\n line 2')
    ('line ', '1')

Nested brackets
    >>> extract_structure('(tuple, [list, {dict: value}, []], 123) * other')
    ('(tuple, [list, {dict: value}, []], 123) ', '* other')
"""

from import_anything.utils import extract_structure
