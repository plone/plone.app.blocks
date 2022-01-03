from plone.app.blocks.interfaces import IBlocksLayer
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING
from plone.app.blocks.transform import ParseXML
from plone.transformchain.zpublisher import applyTransform
from zope.interface import alsoProvides
from zope.interface import implementer

import unittest


@implementer(IBlocksTransformEnabled)
class TransformedView:
    def __init__(self, ret_body):
        self.body = ret_body

    def __call__(self):
        return self.body


class BaseTestCase(unittest.TestCase):
    layer = BLOCKS_INTEGRATION_TESTING

    def prepare_request(self, body=None):
        if body is None:
            body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Empty</title></head>
<body></body>
</html>"""
        request = self.layer["request"]
        request.set("PUBLISHED", TransformedView(body))
        request.response.setBase(request.getURL())
        request.response.setHeader("content-type", "text/html")
        request.response.setBody(body)
        alsoProvides(request, IBlocksLayer)
        return request


class TestTransforms(BaseTestCase):
    def test_transforms_with_crlf(self):
        """Test fix for issue where layouts with CR[+LF] line-endings are
        somehow turned into having &#13; line-endings and getting their heads
        being dropped
        """
        body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">&#13;
<head></head>&#13;
<body></body>&#13;
</html>"""
        request = self.prepare_request(body)
        result = applyTransform(request)
        self.assertIn("<head>", "".join(str(result)))

    def test_transforms_with_cdata(self):
        """Test fix for issue where layouts with inline js got rendered with
        quoted (and therefore broken) <![CDATA[...]]> block
        """
        body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><script type="text/javascript"><![CDATA[]]></script></head>
<body></body>
</html>"""
        request = self.prepare_request(body)
        result = applyTransform(request)
        self.assertIn("<![CDATA[]]>", "".join(str(result)))


class TestParseXML(BaseTestCase):
    """Test our XMLParser transform with only bytes.

    Things can go wrong when there is more than one item in the iterable,
    especially when one item is bytes and the other is text.
    Or at least that is a way that I can more or less reproduce some problems.
    See https://github.com/plone/plone.app.mosaic/issues/480

    I test various combinations in this and the next test methods.
    """

    def test_transformBytes_method(self):
        one = b"<p>one</p>"
        request = self.prepare_request()
        parser = ParseXML(request.get("PUBLISHED"), request)
        result = parser.transformBytes(one, encoding="utf-8")
        html = result.serialize()
        self.assertIn(one, html)

    def test_transformUnicode_method(self):
        one = b"<p>one</p>"
        request = self.prepare_request()
        parser = ParseXML(request.get("PUBLISHED"), request)
        result = parser.transformBytes(one.decode("utf-8"), encoding="utf-8")
        html = result.serialize()
        self.assertIn(one, html)

    # The rest of the tests use the transformIterable method.
    # We use a helper method 'transform' to make this easier.

    def transform(self, iterable):
        request = self.prepare_request()
        parser = ParseXML(request.get("PUBLISHED"), request)
        result = parser.transformIterable(iterable, encoding="utf-8")
        return result.serialize()

    def test_transform_one_byte(self):
        one = b"<p>one</p>"
        html = self.transform([one])
        self.assertIn(one, html)

    def test_transform_one_unicode(self):
        one = b"<p>one</p>"
        # Note: decoding creates a unicode (string on PY3).
        html = self.transform([one.decode("utf-8")])
        # Note: the html result is always bytes, so we must compare with bytes.
        self.assertIn(one, html)

    def test_transform_two_bytes(self):
        one = b"<p>one</p>"
        two = b"<p>two</p>"
        html = self.transform([one, two])
        self.assertIn(one, html)
        self.assertIn(two, html)

    def test_transform_two_unicodes(self):
        one = b"<p>one</p>"
        two = b"<p>two</p>"
        html = self.transform([one.decode("utf-8"), two.decode("utf-8")])
        self.assertIn(one, html)
        self.assertIn(two, html)

    def test_transform_byte_unicode(self):
        one = b"<p>one</p>"
        two = b"<p>two</p>"
        html = self.transform([one, two.decode("utf-8")])
        self.assertIn(one, html)
        self.assertIn(two, html)

    def test_transform_unicode_byte(self):
        one = b"<p>one</p>"
        two = b"<p>two</p>"
        html = self.transform([one.decode("utf-8"), two])
        self.assertIn(one, html)
        self.assertIn(two, html)
