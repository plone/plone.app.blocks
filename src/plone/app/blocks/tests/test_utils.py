from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.blocks.utils import resolve
from plone.app.blocks.utils import resolveResource
from plone.app.blocks.utils import schema_compatible

import unittest
import zope.schema
from zope.interface import Interface


class TestUtils(unittest.TestCase):
    def test_resolve_utf8_unicode(self):
        content_layout = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
  <body>
    <h1>Ä</h1>
  </body>
</html>"""
        text = resolve("", content_layout).xpath("//h1")[0].text
        self.assertEqual("Ä", text)

    def test_resolve_utf8_bytestring(self):
        """Test fix for issue where layouts with non-ascii characters were
        not properly parsed resulting in double encoding
        """
        content_layout = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
  <body>
    <h1>Ä</h1>
  </body>
</html>""".encode()
        text = resolve("", content_layout).xpath("//h1")[0].text
        self.assertEqual("Ä", text)


class TestUtilsFunctional(unittest.TestCase):
    layer = BLOCKS_FUNCTIONAL_TESTING

    def test_resolve_resource(self):
        layout = resolveResource("/++sitelayout++testlayout1/site.html")
        self.assertIn("Layout panel 1", layout)

    def test_resolve_resource_with_query(self):
        layout = resolveResource("/++sitelayout++testlayout1/site.html?ajax_load=1")
        self.assertIn("Layout panel 1", layout)

    def test_resolve_resource_with_html_content(self):
        # make sure we can handle content containing other ++ urls
        layout = resolveResource(
            "/?content=%3Cp%3ELorem%20ipsum%20dolor%20sit%20amet,%20consectetuer%20adipiscing%20elit.%20Sed%20posuere%20interdum%20sem.%20Quisque%20ligula%20eros%20ullamcorper%20quis,%20lacinia%20quis%20facilisis%20sed%20sapien.%3C/p%3E%0A%3Cscript%20type=%22application/javascript%22%20id=%22protect-script%22%20src=%22../../../++resource++protect.js"
        )
        self.assertIn("Plone Open Source CMS", layout)


class TestSchemaCompatible(unittest.TestCase):
    """Tests für schema_compatible aus plone.app.blocks.utils."""

    def test_none_returns_none(self):
        self.assertIsNone(schema_compatible(None, zope.schema.TextLine()))

    def test_dict_with_schema_interface_filters_unknown_keys(self):
        class IMySchema(Interface):
            title = zope.schema.TextLine(title="Title")
            count = zope.schema.Int(title="Count")

        result = schema_compatible(
            {"title": "foo", "count": 42, "extra": "ignored"}, IMySchema
        )
        self.assertEqual(result, {"title": "foo", "count": 42})

    def test_empty_dict_with_schema_interface_returns_empty_dict(self):
        class IMySchema(Interface):
            title = zope.schema.TextLine(title="Title")

        self.assertEqual(schema_compatible({}, IMySchema), {})

    def test_dict_with_idict_field_converts_keys_and_values(self):
        field = zope.schema.Dict(
            key_type=zope.schema.TextLine(),
            value_type=zope.schema.Int(),
        )
        result = schema_compatible({"a": 1, "b": 2}, field)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_empty_dict_with_idict_field_returns_empty_dict(self):
        field = zope.schema.Dict(
            key_type=zope.schema.TextLine(),
            value_type=zope.schema.Int(),
        )
        self.assertEqual(schema_compatible({}, field), {})

    def test_list_with_ilist_field_returns_list(self):
        field = zope.schema.List(value_type=zope.schema.TextLine())
        result = schema_compatible(["a", "b"], field)
        self.assertEqual(result, ["a", "b"])
        self.assertIsInstance(result, list)

    def test_list_with_ituple_field_returns_tuple(self):
        field = zope.schema.Tuple(value_type=zope.schema.TextLine())
        result = schema_compatible(["a", "b"], field)
        self.assertEqual(result, ("a", "b"))
        self.assertIsInstance(result, tuple)

    def test_list_with_iset_field_returns_set(self):
        field = zope.schema.Set(value_type=zope.schema.TextLine())
        result = schema_compatible(["a", "b"], field)
        self.assertEqual(result, {"a", "b"})
        self.assertIsInstance(result, set)

    def test_list_with_ifrozenset_field_returns_frozenset(self):
        field = zope.schema.FrozenSet(value_type=zope.schema.TextLine())
        result = schema_compatible(["a", "b"], field)
        self.assertEqual(result, frozenset({"a", "b"}))
        self.assertIsInstance(result, frozenset)

    def test_bool_field_returns_bool(self):
        field = zope.schema.Bool()
        self.assertIs(schema_compatible(1, field), True)
        self.assertIs(schema_compatible(0, field), False)
        self.assertIs(schema_compatible(True, field), True)

    def test_string_with_ifromunicode_field_uses_from_unicode(self):
        field = zope.schema.Int()
        result = schema_compatible("42", field)
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_non_matching_value_returned_unchanged(self):
        field = zope.schema.TextLine()
        result = schema_compatible(42, field)
        self.assertEqual(result, 42)

    def test_richtext_field_creates_richtext_value(self):
        try:
            from plone.app.textfield import RichText
            from plone.app.textfield import RichTextValue
        except ImportError:
            self.skipTest("plone.app.textfield not available")

        field = RichText()
        data = {
            "data": "<p>Hello</p>",
            "content-type": "text/html",
            "output-content-type": "text/x-html-safe",
            "encoding": "utf-8",
        }
        result = schema_compatible(data, field)
        self.assertIsInstance(result, RichTextValue)
        self.assertEqual(result.raw, "<p>Hello</p>")
        self.assertEqual(result.mimeType, "text/html")
        self.assertEqual(result.outputMimeType, "text/x-html-safe")
        self.assertEqual(result.encoding, "utf-8")

    def test_richtext_field_uses_defaults_for_missing_keys(self):
        try:
            from plone.app.textfield import RichText
            from plone.app.textfield import RichTextValue
        except ImportError:
            self.skipTest("plone.app.textfield not available")

        field = RichText()
        result = schema_compatible({"data": "<p>Hi</p>"}, field)
        self.assertIsInstance(result, RichTextValue)
        self.assertEqual(result.raw, "<p>Hi</p>")
        self.assertEqual(result.mimeType, "text/html")
        self.assertEqual(result.encoding, "utf-8")


class TestRichtextJsonCompatible(unittest.TestCase):
    """Tests für richtext_json_compatible aus plone.app.blocks.utils."""

    def setUp(self):
        try:
            from plone.app.textfield import RichTextValue

            self.RichTextValue = RichTextValue
        except ImportError:
            self.skipTest("plone.app.textfield not available")

    def test_converts_richtext_value_to_dict(self):
        from plone.app.blocks.utils import richtext_json_compatible

        value = self.RichTextValue(
            raw="<p>Hello</p>",
            mimeType="text/html",
            outputMimeType="text/x-html-safe",
            encoding="utf-8",
        )
        result = richtext_json_compatible(value)
        self.assertEqual(
            result,
            {
                "data": "<p>Hello</p>",
                "content-type": "text/html",
                "output-content-type": "text/x-html-safe",
                "encoding": "utf-8",
            },
        )

    def test_preserves_custom_mime_type(self):
        from plone.app.blocks.utils import richtext_json_compatible

        value = self.RichTextValue(
            raw="**bold**",
            mimeType="text/x-rst",
            outputMimeType="text/html",
            encoding="utf-8",
        )
        result = richtext_json_compatible(value)
        self.assertEqual(result["content-type"], "text/x-rst")
        self.assertEqual(result["output-content-type"], "text/html")
        self.assertEqual(result["data"], "**bold**")
