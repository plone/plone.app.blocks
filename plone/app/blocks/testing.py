from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.registry.interfaces import IRegistry
from plone.testing import Layer
from zope.component import getUtility
from zope.configuration import xmlconfig


class BlocksLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.blocks
        import plone.app.contenttypes
        import plone.app.tiles

        self.loadZCML(package=plone.app.tiles, name="demo.zcml")
        self.loadZCML(package=plone.app.blocks)
        self.loadZCML(package=plone.app.contenttypes)

        # Register directory for testing
        xmlconfig.string(
            """\
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

    <plone:static
        type="contentlayout"
        name="testlayout1"
        directory="resources/contentlayout/testlayout1"
        />

    <plone:static
        type="contentlayout"
        name="testlayout2"
        directory="resources/contentlayout/testlayout2"
        />

</configure>
""",
            context=configurationContext,
        )
        if "virtual_hosting" not in app.objectIds():
            # If ZopeLite was imported, we have no default virtual
            # host monster
            from Products.SiteAccess.VirtualHostMonster import (
                manage_addVirtualHostMonster,
            )

            manage_addVirtualHostMonster(app, "virtual_hosting")

    def setUpPloneSite(self, portal):
        # ensure plone.app.theming disabled
        registry = getUtility(IRegistry)
        key = "plone.app.theming.interfaces.IThemeSettings.enabled"
        if key in registry:
            registry[key] = False
        # install plone.app.contenttypes on Plone 5
        self.applyProfile(portal, "plone.app.contenttypes:default")
        # install into the Plone site
        self.applyProfile(portal, "plone.app.blocks:default")


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
    bases=(BLOCKS_FIXTURE,), name="Blocks:Integration"
)
BLOCKS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BLOCKS_FIXTURE,), name="Blocks:Functional"
)
BLOCKS_FUNCTIONAL_TESTING_PRETTY_PRINT = FunctionalTesting(
    bases=(
        PRETTY_PRINT_FIXTURE,
        BLOCKS_FIXTURE,
    ),
    name="Blocks:FunctionalPrettyPrinting",
)
