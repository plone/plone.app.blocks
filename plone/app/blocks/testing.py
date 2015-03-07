# -*- coding: utf-8 -*-
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import Layer
from zope.configuration import xmlconfig
import pkg_resources

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True

try:
    pkg_resources.get_distribution('plone.app.theming')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_THEMING = False
else:
    HAS_PLONE_APP_THEMING = True


class BlocksLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        if HAS_PLONE_APP_CONTENTTYPES:
            import plone.app.contenttypes
            self.loadZCML(package=plone.app.contenttypes)
        import plone.app.blocks
        self.loadZCML(package=plone.app.blocks)

        # Register directory for testing
        xmlconfig.string("""\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="plone"
    package="plone.app.blocks.tests">

    <plone:static
        type="sitelayout"
        name="testlayout1"
        directory="resources/sitelayout/testlayout1"
        />

    <plone:static
        type="sitelayout"
        name="testlayout2"
        directory="resources/sitelayout/testlayout2"
        />

</configure>
""", context=configurationContext)
        if 'virtual_hosting' not in app.objectIds():
            # If ZopeLite was imported, we have no default virtual
            # host monster
            from Products.SiteAccess.VirtualHostMonster \
                import manage_addVirtualHostMonster
            manage_addVirtualHostMonster(app, 'virtual_hosting')

    def setUpPloneSite(self, portal):
        # ensure plone.app.theming disabled
        if HAS_PLONE_APP_THEMING:
            from plone.registry.interfaces import IRegistry
            from zope.component import getUtility
            registry = getUtility(IRegistry)
            key = 'plone.app.theming.interfaces.IThemeSettings.enabled'
            if key in registry:
                registry[key] = False
        # install plone.app.contenttypes on Plone 5
        if HAS_PLONE_APP_CONTENTTYPES:
            self.applyProfile(portal, 'plone.app.contenttypes:default')
        # install into the Plone site
        self.applyProfile(portal, 'plone.app.blocks:default')


class PrettyPrintLayer(Layer):

    def setUp(self):
        from plone.app.blocks.transform import ParseXML
        ParseXML.pretty_print = True

    def tearDown(self):
        from plone.app.blocks.transform import ParseXML
        ParseXML.pretty_print = False

BLOCKS_FIXTURE = BlocksLayer()
PRETTY_PRINT_FIXTURE = PrettyPrintLayer()
BLOCKS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BLOCKS_FIXTURE,), name="Blocks:Integration")
BLOCKS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BLOCKS_FIXTURE,), name="Blocks:Functional")
BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT = FunctionalTesting(
    bases=(PRETTY_PRINT_FIXTURE, BLOCKS_FIXTURE,),
    name="Blocks:Functional Pretty Printing")
