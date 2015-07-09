# -*- coding: utf-8 -*-
import unittest

from plone.app.blocks.interfaces import IBlocksLayer
from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from plone.transformchain.zpublisher import applyTransform
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.interface import implements


gridsystem_test_body = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><script type="text/javascript"><![CDATA[]]></script></head>
<body>
<div class="mosaic-grid-row" data-grid='{"type": "row"}'>
    <div class="mosaic-grid-cell mosaic-width-full mosaic-position-leftmost"
         data-grid='{"type": "cell", "info":{"xs": "true", "sm": "true", "lg": "true", "pos": {"x": 1, "width": 12}}}'>
        <div class="movable mosaic-tile mosaic-IDublinCore-title-tile">
            <div class="mosaic-tile-content"><h1 class="documentFirstHeading">some page</h1>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""


class TestTransformedView(object):
    implements(IBlocksTransformEnabled)

    def __init__(self, ret_body):
        self.__call__ = lambda b=ret_body: b


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

    def test_transform_gridsystem_default_deco(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IBlocksSettings)
        settings.default_grid_system = 'deco'

        request = self.layer['request']
        request.set('PUBLISHED', TestTransformedView(gridsystem_test_body))
        request.response.setBase(request.getURL())
        request.response.setHeader('content-type', 'text/html')
        request.response.setBody(gridsystem_test_body)

        alsoProvides(request, IBlocksLayer)
        result = ''.join(applyTransform(request))
        self.assertIn('cell position-0 width-12', result)
        self.assertIn('mosaic-grid-row row', result)

    def test_transform_gridsystem_default_bs3(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IBlocksSettings)
        settings.default_grid_system = 'bs3'

        request = self.layer['request']
        request.set('PUBLISHED', TestTransformedView(gridsystem_test_body))
        request.response.setBase(request.getURL())
        request.response.setHeader('content-type', 'text/html')
        request.response.setBody(gridsystem_test_body)

        alsoProvides(request, IBlocksLayer)
        result = ''.join(applyTransform(request))
        self.assertIn('col-md-12', result)
        self.assertIn('mosaic-grid-row row', result)
