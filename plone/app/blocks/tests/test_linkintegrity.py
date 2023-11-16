from plone.app.blocks.testing import BLOCKS_FIXTURE
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.parser import extractLinks
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.fti import DexterityFTI
from plone.registry.interfaces import IRegistry
from plone.tiles import Tile
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces import IEditingSchema
from zope.component import adapter
from zope.component import getUtility
from zope.configuration import xmlconfig
from zope.interface import implementer
from zope.interface import Interface

import pkg_resources
import unittest


try:
    pkg_resources.get_distribution("plone.app.contenttypes")
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True


class ITestTile(Interface):
    """test marker"""


class TestTile(Tile):
    def __call__(self):
        return (
            "<a href=\"resolveuid/{}\">internal link</a>".format(
                self.request.form.get('uid')
            )
        )


@implementer(IRetriever)
@adapter(TestTile)
class TestTileRetriever:
    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        content = self.context()
        return set(extractLinks(content))


class TestTilesLayer(PloneSandboxLayer):
    defaultBases = (BLOCKS_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            """\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="plone.app.blocks">

  <include package="plone.tiles" file="meta.zcml" />

  <plone:tile
      name="test.tile"
      title="Test Tile"
      add_permission="cmf.ModifyPortalContent"
      class="plone.app.blocks.tests.test_linkintegrity.TestTile"
      permission="zope2.View"
      for="*"
      />

  <adapter
      factory="plone.app.blocks.tests.test_linkintegrity.TestTileRetriever"
      />

</configure>
""",
            context=configurationContext,
        )


BLOCKS_TILES_LINKINTEGRITY_FIXTURE = TestTilesLayer()
BLOCKS_TILES_LINKINTEGRITY_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BLOCKS_TILES_LINKINTEGRITY_FIXTURE,),
    name="Blocks:Tiles:LinkIntegrity:Integration",
)


class TestLinkIntegrity(unittest.TestCase):
    layer = BLOCKS_TILES_LINKINTEGRITY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.registry = getUtility(IRegistry)
        self.maxDiff = None

        editing_settings = self.registry.forInterface(IEditingSchema, prefix="plone")
        editing_settings.enable_link_integrity_checks = True

        fti = DexterityFTI(
            "MyDocument",
            global_allow=True,
            behaviors=(
                "plone.app.dexterity.behaviors.metadata.IBasic",
                "plone.app.blocks.layoutbehavior.ILayoutAware",
            ),
        )
        self.portal.portal_types._setObject("MyDocument", fti)

        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        self.portal.invokeFactory("Folder", "f1", title="Folder 1")
        self.folder = self.portal["f1"]
        self.folder.invokeFactory("MyDocument", "d1", title="Document 1")
        self.doc1 = self.folder["d1"]
        self.folder.invokeFactory("MyDocument", "d2", title="Document 2")
        self.doc2 = self.folder["d2"]

        # set customContentLayout to @@test_tile with internal Link
        self.doc1.customContentLayout = """
            <html><body><div data-tile="./@@test.tile?uid={}"/></body></html>
            """.format(
            IUUID(self.doc2)
        )

    def test_copy_paste(self):
        # see
        _cp = self.folder.manage_copyObjects(
            [
                "d1",
            ]
        )
        self.folder.manage_pasteObjects(_cp)

        self.assertTrue("copy_of_d1" in self.folder)

        _cp = self.portal.manage_copyObjects(
            [
                "f1",
            ]
        )
        self.portal.manage_pasteObjects(_cp)

        self.assertTrue("copy_of_f1" in self.portal)
        self.assertTrue("d1" in self.portal["copy_of_f1"])
