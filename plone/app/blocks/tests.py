import unittest2 as unittest
import doctest
from plone.testing import layered

from plone.app.testing.layers import IntegrationTesting
from plone.app.testing.layers import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import quickInstallProduct

from zope.configuration import xmlconfig

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

class PABlocks(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.blocks
        import plone.tiles
        xmlconfig.file('configure.zcml', plone.app.blocks,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        quickInstallProduct(portal, 'plone.app.blocks')

PABLOCKS_FIXTURE = PABlocks()

PABLOCKS_INTEGRATION_TESTING = IntegrationTesting(bases=(PABLOCKS_FIXTURE,), name="PABlocks:Integration")
PABLOCKS_FUNCTIONAL_TESTING = FunctionalTesting(bases=(PABLOCKS_FIXTURE,), name="PABlocks:Functional")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite('rendering.txt', 'esi.txt', 'context.txt',
                                     optionflags=optionflags),
                layer=PABLOCKS_FUNCTIONAL_TESTING)
        ])
    return suite
        
