# -*- coding: utf-8 -*-
from plone.app.blocks.interfaces import IBlocksLayer
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING
from plone.transformchain.zpublisher import applyTransform
from zope.interface import alsoProvides
from zope.interface import implementer

import unittest


@implementer(IBlocksTransformEnabled)
class TransformedView(object):
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
