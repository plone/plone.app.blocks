import unittest2 as unittest
import doctest
from plone.testing import layered

from plone.app.blocks.testing import PABLOCKS_FUNCTIONAL_TESTING

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite('rendering.txt', 'context.txt', 'esi.txt',
                                     optionflags=optionflags),
                layer=PABLOCKS_FUNCTIONAL_TESTING),
        ])
    return suite
