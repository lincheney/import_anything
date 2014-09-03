import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import utils as Utils

class TestUtils(unittest.TestCase):
    def test_indent(self):
        """
        .indent should indent a string and use args/kwargs
        as arguments to string.format
        """
        
        string = 'abc{}def'
        result = Utils.indent(10, string, 100)
        self.assertEqual(result, ' ' * 10 + string.format(100))
    
    def test_indent_no_format(self):
        """
        .indent should not attempt to format the string
        if there are no other args
        """
        
        result = Utils.indent(10, '{}')
        self.assertEqual(result, ' ' * 10 + '{}')
    
    def test_strip_indents(self):
        """
        .strip_indents should strip leading whitespace
        and return the length of the whitespace and the
        remaining string
        """
        
        indent = ' ' * 50
        rest = 'abcdef'
        result = Utils.strip_indents(indent + rest)
        self.assertEqual(result, (len(indent), rest))
