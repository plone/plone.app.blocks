import unittest
from zope.testing import doctest

from Testing import ZopeTestCase as ztc
from Products.PloneTestCase import ptc
from Products.Five import zcml

import collective.testcaselayer.ptc

import plone.app.blocks
import plone.tiles

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

class IntegrationTestLayer(collective.testcaselayer.ptc.BasePTCLayer):

    def afterSetUp(self):
        zcml.load_config('configure.zcml', plone.app.blocks)
        self.addProfile('plone.app.blocks:default')

Layer = IntegrationTestLayer([collective.testcaselayer.ptc.ptc_layer])

class FunctionalTestCase(ptc.FunctionalTestCase):
    layer = Layer

def test_suite():
    return unittest.TestSuite((
        ztc.FunctionalDocFileSuite(
            'rendering.txt',
            package='plone.app.blocks',
            test_class=FunctionalTestCase,
            optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
            'context.txt',
            package='plone.app.blocks',
            test_class=FunctionalTestCase,
            optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
            'esi.txt',
            package='plone.app.blocks',
            test_class=FunctionalTestCase,
            optionflags=optionflags),
        ))
