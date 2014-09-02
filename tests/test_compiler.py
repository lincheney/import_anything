import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything import Compiler

class TestCompiler(unittest.TestCase):
    def test_indent(self):
        """
        .indent should indent a string
        """
        
        string = 'abcdef'
        result = Compiler.indent(10, string)
        self.assertEqual(result, ' ' * 10 + string)
    
    def test_strip_indents(self):
        """
        .strip_indents should strip leading whitespace
        and return the length of the whitespace and the
        remaining string
        """
        
        indent = ' ' * 50
        rest = 'abcdef'
        result = Compiler.strip_indents(indent + rest)
        self.assertEqual(result, (len(indent), rest))
    
    @mock.patch.object(Compiler, 'translate')
    @mock.patch.object(Compiler, 'open', return_value = sentinel.file)
    def test__init__(self, open, translate):
        """
        the constructor should perform and store the translation
        """
        
        lines = ['line #1', 'line #2']
        lineno = [1, 2]
        translate.return_value = zip(lineno, lines)
        
        compiler = Compiler('path')
        
        translate.assert_called_once_with(sentinel.file)
        self.assertEqual(compiler.data, '\n'.join(lines))
        self.assertEqual(compiler.line_numbers, [0] + lineno)
    
    @mock.patch.object(Compiler, 'translate')
    @mock.patch.object(Compiler, 'open')
    def test__init__multiline(self, open, translate):
        """
        the constructor should assign extra line numbers to multiline translations
        """
        
        lines = ['line #1', 'line #2\nline #3']
        lineno = [1, 2]
        translate.return_value = zip(lineno, lines)
        
        compiler = Compiler('path')
        
        self.assertEqual(compiler.data, '\n'.join(lines))
        self.assertEqual(compiler.line_numbers, [0] + lineno + [3])
