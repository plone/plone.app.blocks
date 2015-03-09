# -*- coding: utf-8 -*-
from plone.transformchain.zpublisher import applyTransform
from plone.app.blocks.interfaces import IBlocksLayer
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING
from zope.interface import alsoProvides
from zope.interface import implements

import unittest


class TestTransforms(unittest.TestCase):

    layer = BLOCKS_INTEGRATION_TESTING

    def test_transforms_with_crlf(self):
        """Test fix for issue where layouts with CR[+LF] line-endings are
        somehow turned into having &#13; line-endings and getting their heads
        being dropped
        """

        class TransformedView(object):
            implements(IBlocksTransformEnabled)

            def __init__(self, ret_body):
                self.__call__ = lambda b=ret_body: b

        body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">&#13;
<head></head>&#13;
<body></body>&#13;
</html>"""
        request = self.layer['request']
        request.set('PUBLISHED', TransformedView(body))
        request.response.setBase(request.getURL())
        request.response.setHeader('content-type', 'text/html')
        request.response.setBody(body)

        alsoProvides(request, IBlocksLayer)
        result = applyTransform(request)
        self.assertIn('<head>', ''.join(result))

    def test_transforms_with_cdata(self):
        """Test fix for issue where layouts with inline js got rendered with
        quoted (and therefore broken) <![CDATA[...]]> block
        """

        class TransformedView(object):
            implements(IBlocksTransformEnabled)

            def __init__(self, ret_body):
                self.__call__ = lambda b=ret_body: b

        body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><script type="text/javascript"><![CDATA[]]></script></head>
<body></body>
</html>"""
        request = self.layer['request']
        request.set('PUBLISHED', TransformedView(body))
        request.response.setBase(request.getURL())
        request.response.setHeader('content-type', 'text/html')
        request.response.setBody(body)

        alsoProvides(request, IBlocksLayer)
        result = applyTransform(request)
        self.assertIn('<![CDATA[]]>', ''.join(result))
