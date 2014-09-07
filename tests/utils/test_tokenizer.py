import unittest
import unittest.mock as mock
import doctest
from unittest.mock import sentinel
from import_anything import utils as Utils

from . import tokenizer_doctest
def load_tests(loader, tests, ignore):
    flags = doctest.REPORT_NDIFF
    tests.addTests(doctest.DocTestSuite(tokenizer_doctest, optionflags = flags))
    return tests

class TestTokenizer(unittest.TestCase):
    def test_extract_structure(self):
        """
        extract_structure() returns the string/list/dict/tuple etc. at
        the start of the string and the rest of the remaining line
        Any lines starting after aren't returned
        """
        
        tests = [
            ('{} + 1', '{} '),
            ('[] + 1', '[] '),
            ('() + 1', '() '),
            ('(x)', '(x)'),
            ('"string" - 4', '"string" '),
            ("'str' * 3", "'str' "),
            ('{nested: ["structures", ()]} + other_stuff', '{nested: ["structures", ()]} '),
            ('r"raw string" + None', 'r"raw string" '),
            ('"""multiline\ntriple\nquotes""" + 0', '"""multiline\ntriple\nquotes""" '),
            ("'''backslashes \\'''' ", "'''backslashes \\'''' "),
            ('b"bytes" #comment', 'b"bytes" '),
            ('u"unicode" "another string"', 'u"unicode" '),
            ('variable_name', 'variable_name'),
            ('function_call()', 'function_call'),
            ('1 + 2', '1 '),
            ('@decorator', '@'),
            ('"unclosed quotes', '"'),
            ('(unclosed bracket', '(unclosed bracket'),
            ]
        
        for string, struct in tests:
            result = Utils.extract_structure(string)
            self.assertEqual(result[0], struct)
            self.assertEqual(''.join(result), string)
        
        string = '[] + 1\nnext line'
        struct = '[] '
        remainder = '+ 1'
        result = Utils.extract_structure(string)
        self.assertEqual(result[0], struct)
        self.assertEqual(result[1], remainder)

