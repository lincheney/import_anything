import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import utils as Utils

class TestTokenizer(unittest.TestCase):
    def test_full_tokenize(self):
        """
        full_tokenize() should tokenize the string but keep all whitespace
        """
        
        string = ''' 'string' + [nest, [lists, (tuple,)]] * function_call() + \n line_continuation '''
        result = Utils.full_tokenize(string.splitlines())
        result = ''.join(i.string for i in result)
        self.assertEqual(result, string)
    
    def test_full_tokenize_unexpected_eof(self):
        """
        full_tokenize() should ignore unexpected EOFs
        """
        
        tests = [
            '1 + [a, b',
            '1 + (a, b',
            '1 + {a, b',
            '1 + """a, b',
            ]
        
        for string in tests:
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

