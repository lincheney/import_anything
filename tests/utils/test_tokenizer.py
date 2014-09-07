import unittest
import unittest.mock as mock
import doctest
from unittest.mock import sentinel
from import_anything import utils as Utils

from . import tokenizer_doctest
from . import extract_structure_doctest
def load_tests(loader, tests, ignore):
    flags = doctest.REPORT_NDIFF
    tests.addTests(doctest.DocTestSuite(tokenizer_doctest, optionflags = flags))
    tests.addTests(doctest.DocTestSuite(extract_structure_doctest, optionflags = flags))
    return tests

class TestTokenizer(unittest.TestCase):
    pass
