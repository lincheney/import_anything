import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import utils as Utils

class TestUtils(unittest.TestCase):
    def test_indent(self):
        """
        indent() should indent a string and use args/kwargs
        as arguments to string.format
        """
        
        string = 'abc{}def'
        result = Utils.indent(10, string, 100)
        self.assertEqual(result, ' ' * 10 + string.format(100))
    
    def test_indent_no_format(self):
        """
        indent() should not attempt to format the string
        if there are no other args
        """
        
        result = Utils.indent(10, '{}')
        self.assertEqual(result, ' ' * 10 + '{}')
    
    def test_indent_block(self):
        """
        indent() should preserve Block
        """
        
        result = Utils.indent(4, Utils.Block(''))
        self.assertIsInstance(result, Utils.Block)
    
    def test_strip_indents(self):
        """
        strip_indents() should strip leading whitespace
        and return the length of the whitespace and the
        remaining string
        """
        
        indent = ' ' * 50
        rest = 'abcdef'
        result = Utils.strip_indents(indent + rest)
        self.assertEqual(result, (len(indent), rest))
    
    def test_complete_blocks_empty_block(self):
        """
        complete_blocks() should append 'pass' to empty blocks
        """
        
        @Utils.complete_blocks(indent_by = 2, body = 'pass')
        def source(block):
            yield 1, block('empty block:')
        
        result = list(source())
        self.assertEqual(result, [(1, 'empty block:'), (1, '  pass')])
    
    def test_complete_blocks_filled_block(self):
        """
        complete_blocks() should leave 'filled' blocks alone
        """
        
        @Utils.complete_blocks(indent_by = 2, body = 'pass')
        def source(block):
            yield 1, block('block:')
            yield 2, '  block body'
        
        result = list(source())
        self.assertEqual(result, [(1, 'block:'), (2, '  block body')])
    
    def test_full_tokenize(self):
        """
        full_tokenize() should tokenize the string but keep all whitespace
        """
        
        string = ''' 'string' + [nest, [lists, (tuple,)]] * function_call() + \n line_continuation '''
        result = Utils.full_tokenize(string.splitlines())
        result = ''.join(i.string for i in result)
        self.assertEqual(result, string)
    
    def test_extract_structure(self):
        """
        extract_structure() returns the string/list/dict/tuple etc. at
        the start of the string and the rest of the remaining line
        Any lines starting after aren't returned
        """
        
        tests = [
            ('{} + 1', '{}'),
            ('[] + 1', '[]'),
            ('() + 1', '()'),
            ('(x)', '(x)'),
            ('"string" - 4', '"string"'),
            ("'str' * 3", "'str'"),
            ('{nested: ["structures", ()]} + other_stuff', '{nested: ["structures", ()]}'),
            ('r"raw string" + None', 'r"raw string"'),
            ('"""multiline\ntriple\nquotes""" + 0', '"""multiline\ntriple\nquotes"""'),
            ("'''backslashes \\'''' ", "'''backslashes \\'''' "),
            ('b"bytes" #comment', 'b"bytes"'),
            ('u"unicode" "another string"', 'u"unicode"'),
            ('variable_name', 'variable_name'),
            ('function_call()', 'function_call'),
            ('1 + 2', '1'),
            ('@decorator', '@'),
            ('"unclosed quotes', '"'),
            ('(unclosed bracket', '(unclosed bracket'),
            ]
        
        for string, struct in tests:
            result = Utils.extract_structure(string.splitlines())
            self.assertEqual(result[0], struct)
            self.assertEqual(''.join(result), string)
        
        string = '[] + 1\nnext line'
        struct = '[]'
        remainder = ' + 1'
        result = Utils.extract_structure(string.splitlines())
        self.assertEqual(result[0], struct)
        self.assertEqual(result[1], remainder)
