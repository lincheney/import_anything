import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import utils as Utils

class TestUtils(unittest.TestCase):
    def test_indent(self):
        """
        .indent should indent a string
        """
        
        string = 'abcdef'
        result = Utils.indent(10, string)
        self.assertEqual(result, ' ' * 10 + string)
    
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
