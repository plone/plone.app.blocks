import unittest2 as unittest
import doctest
from plone.testing import layered

from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite(
                    'rendering.txt',
                    'esi.txt',
                    'context.txt',
                    optionflags=optionflags),
                layer=BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT),
        ])
    return suite
