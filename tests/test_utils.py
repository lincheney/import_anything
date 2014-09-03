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
    
    def test_complete_blocks(self):
        """
        .complete_blocks should append 'pass' to all empty
        code blocks (i.e. if,while,for,def,class,with etc.)
        """
        
        indent = 2
        body = 'abc'
        @Utils.complete_blocks(indent_by = indent, body = body)
        def source(block):
            yield 1, 'line #1'
            yield 2, block('block:')
            yield 3, '  block body'
            yield 4, block('empty block:')
        
        result = list(source())
        self.assertEqual(len(result), 5)
        
        lineno, strings = zip(*result)
        self.assertEqual(lineno, (1, 2, 3, 4, 4))
        self.assertEqual(strings, ('line #1', 'block:', '  block body', 'empty block:', ' ' * indent + 'abc'))
