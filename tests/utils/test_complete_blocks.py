import unittest
import unittest.mock as mock
from unittest.mock import sentinel
from import_anything.utils import complete_blocks

class TestCompleteBlocks(unittest.TestCase):
    def test_empty_block(self):
        """
        complete_blocks() should append 'pass' to empty blocks
        """
        
        @complete_blocks(indent_by = 2, body = 'pass')
        def source(block):
            yield 1, block('empty block:')
        
        result = list(source())
        self.assertEqual(result, [(1, 'empty block:'), (1, '  pass')])
    
    def test_filled_block(self):
        """
        complete_blocks() should leave 'filled' blocks alone
        """
        
        @complete_blocks(indent_by = 2, body = 'pass')
        def source(block):
            yield 1, block('block:')
            yield 2, '  block body'
        
        result = list(source())
        self.assertEqual(result, [(1, 'block:'), (2, '  block body')])
