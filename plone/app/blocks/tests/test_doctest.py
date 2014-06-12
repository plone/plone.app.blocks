# -*- coding: utf-8 -*-
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT
from plone.testing import layered

import doctest
import unittest2 as unittest


optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_NDIFF)

doc_tests = [
    'context.rst',
    'esi.rst',
    'rendering.rst',
]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([layered(
        doctest.DocFileSuite(doc_tests,
                             optionflags=optionflags),
        layer=BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT),
    ])
    return suite
