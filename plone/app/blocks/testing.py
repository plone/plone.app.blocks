from plone.app.testing.layers import FunctionalTesting

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile

from plone.testing import z2

from zope.configuration import xmlconfig

class PABlocks(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.blocks
        xmlconfig.file('configure.zcml', plone.app.blocks, context=configurationContext)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'plone.app.blocks:default')

PABLOCKS_FIXTURE = PABlocks()
PABLOCKS_FUNCTIONAL_TESTING = FunctionalTesting(bases=(PABLOCKS_FIXTURE,),
                                                name="PABlocks:Functional")
