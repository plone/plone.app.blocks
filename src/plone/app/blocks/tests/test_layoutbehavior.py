from importlib.metadata import distribution
from importlib.metadata import PackageNotFoundError
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LAYOUT_STORAGE_CACHE_KEY
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield import RichText
from plone.app.textfield import RichTextValue
from plone.dexterity.fti import DexterityFTI
from plone.registry.interfaces import IRegistry
from plone.rfc822.interfaces import IPrimaryField
from plone.supermodel.model import Schema
from plone.tiles.interfaces import ITileType
from plone.tiles.type import TileType
from plone.uuid.interfaces import IUUID
from zope.component import getUtility
from zope.component import provideUtility
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from zope.interface import alsoProvides

import unittest

try:
    distribution("plone.app.contenttypes")
except PackageNotFoundError:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True


class TestLayoutBehavior(unittest.TestCase):
    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.registry = getUtility(IRegistry)
        self.maxDiff = None

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
        self.portal["f1"].invokeFactory("MyDocument", "d1", title="Document 1")
        setRoles(self.portal, TEST_USER_ID, ("Member",))

        self.behavior = ILayoutAware(self.portal["f1"]["d1"])
        self.assertTrue(ILayoutBehaviorAdaptable.providedBy(self.behavior.context))

    def test_custom_content_layout(self):
        from plone.app.blocks.layoutviews import ContentLayoutView

        self.behavior.customContentLayout = (
            '<html><body><a href="{:s}"></a></body></html>'.format(
                "resolveuid/{:s}".format(IUUID(self.portal["f1"]))
            )
        )
        rendered = ContentLayoutView(self.portal["f1"]["d1"], self.request)()

        # Test that UUID is resolved by outputfilters
        self.assertNotIn(IUUID(self.portal["f1"]), rendered)
        self.assertIn(self.portal["f1"].absolute_url(), rendered)

    def test_content(self):
        tile = "plone.app.tiles.demo.transient/demo"
        self.behavior.content = """\
<html>
<body>
<div data-tile="@@plone.app.tiles.demo.transient/demo"
data-tiledata='{"message": "Hello World!"}' />
</body>
</html>
"""
        view = self.portal["f1"]["d1"].restrictedTraverse(tile)()
        self.assertEqual(
            view, "<html><body><b>Transient tile Hello World!</b></body></html>"
        )

        storage = LayoutAwareTileDataStorage(
            self.portal["f1"]["d1"], self.layer["request"]
        )
        self.assertEqual(len(storage), 1)
        self.assertEqual(list(storage), [tile])
        self.assertEqual(storage[tile]["message"], "Hello World!")

        data = storage[tile]
        data["message"] = "Foo bar!"
        storage[tile] = data

        view = self.portal["f1"]["d1"].restrictedTraverse(tile)()
        self.assertEqual(
            view, "<html><body><b>Transient tile Foo bar!</b></body></html>"
        )

    def test_content_richtext(self):
        class IRichTextTile(Schema):
            html = RichText()

        alsoProvides(IRichTextTile["html"], IPrimaryField)

        provideUtility(
            TileType(
                name="plone.app.blocks.richtext",
                title="plone.app.blocks.richtext",
                add_permission="cmf.ModifyPortalContent",
                view_permission="zope2.View",
                schema=IRichTextTile,
            ),
            provides=ITileType,
            name="plone.app.blocks.richtext",
        )

        self.behavior.content = """\
<html>
<body>
<div data-tile="@@plone.app.blocks.richtext/demo"
data-tiledata='{"content-type": "text/html"}'>
<div><p>Hello World!</p></div>
</div>
</body>
</html>
"""
        storage = LayoutAwareTileDataStorage(
            self.portal["f1"]["d1"], self.layer["request"]
        )
        data = storage["@@plone.app.blocks.richtext/demo"]

        self.assertIn("html", data)
        self.assertIsInstance(data["html"], RichTextValue)
        self.assertEqual(data["html"].output, "<p>Hello World!</p>")

        storage["@@plone.app.blocks.richtext/demo"] = {
            "html": RichTextValue(
                "<p>Foo bar!</p>",
                mimeType="text/html",
                outputMimeType="text/x-html-safe",
                encoding="utf-8",
            )
        }

        output = str(storage.storage).replace("\n", "")
        self.assertIn('"html-content-type": "text/html"', output)
        self.assertIn('"html-output-content-type": "text/x-html-safe"', output)
        self.assertIn("<p>Foo bar!</p>", output)

    def test_content_richtext_without_request(self):
        """Without a global request, schema_compatible returns the raw value.

        This documents the fallback behaviour for contexts such as migration
        scripts that use LayoutAwareTileDataStorage without an HTTP request.
        In that case plone.restapi cannot provide a deserializer and the raw
        value is returned unchanged.
        """

        class IRichTextTile(Schema):
            html = RichText()

        alsoProvides(IRichTextTile["html"], IPrimaryField)

        provideUtility(
            TileType(
                name="plone.app.blocks.richtext.norequest",
                title="plone.app.blocks.richtext.norequest",
                add_permission="cmf.ModifyPortalContent",
                view_permission="zope2.View",
                schema=IRichTextTile,
            ),
            provides=ITileType,
            name="plone.app.blocks.richtext.norequest",
        )

        self.behavior.content = """\
<html>
<body>
<div data-tile="@@plone.app.blocks.richtext.norequest/demo"
data-tiledata='{"content-type": "text/html"}'>
<div><p>Hello World!</p></div>
</div>
</body>
</html>
"""
        # Remove the global request to simulate a context without an HTTP request
        saved_request = self.layer["request"]
        clearRequest()
        try:
            storage = LayoutAwareTileDataStorage(self.portal["f1"]["d1"], saved_request)
            data = storage["@@plone.app.blocks.richtext.norequest/demo"]
        finally:
            setRequest(saved_request)

        # Without a request, schema_compatible cannot find a deserializer and
        # returns the raw value instead of a RichTextValue.
        # The primary field is read as a plain string from the HTML element.
        self.assertIn("html", data)
        self.assertNotIsInstance(data["html"], RichTextValue)
        self.assertIsInstance(data["html"], str)
        self.assertIn("Hello World!", data["html"])

    def test_storage_cache_reuses_parsed_html(self):
        """Test that multiple LayoutAwareTileDataStorage instances for the
        same context reuse the same parsed HTML storage object."""
        self.behavior.content = """\
<html>
<body>
<div data-tile="@@plone.app.tiles.demo.transient/demo"
data-tiledata='{"message": "Hello World!"}' />
</body>
</html>
"""
        request = self.layer["request"]
        # Clear existing cache
        request.environ.pop(LAYOUT_STORAGE_CACHE_KEY, None)

        context = self.portal["f1"]["d1"]
        storage1 = LayoutAwareTileDataStorage(context, request)
        storage2 = LayoutAwareTileDataStorage(context, request)

        # Both instances should share the same storage object
        self.assertIs(storage1.storage, storage2.storage)

    def test_storage_cache_invalidated_on_sync(self):
        """Test that the per-request storage cache is invalidated when
        sync() writes changes back."""
        tile = "plone.app.tiles.demo.transient/demo"
        self.behavior.content = """\
<html>
<body>
<div data-tile="@@plone.app.tiles.demo.transient/demo"
data-tiledata='{"message": "Hello World!"}' />
</body>
</html>
"""
        request = self.layer["request"]
        request.environ.pop(LAYOUT_STORAGE_CACHE_KEY, None)

        context = self.portal["f1"]["d1"]
        storage = LayoutAwareTileDataStorage(context, request)
        data = storage[tile]
        data["message"] = "Changed!"
        storage[tile] = data  # triggers sync()

        # After sync, the cache should no longer contain the old entry
        from Acquisition import aq_base

        context_id = id(aq_base(context))
        cache = request.environ.get(LAYOUT_STORAGE_CACHE_KEY, {})
        self.assertNotIn(context_id, cache)
