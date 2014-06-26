# -*- coding: utf-8 -*-
from OFS.Image import File
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CMFPlone.utils import getToolByName
from StringIO import StringIO
from plone.transformchain.zpublisher import applyTransform
from repoze.xmliter.utils import getHTMLSerializer
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY, \
    IBlocksTransformEnabled
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING
from plone.app.testing import setRoles, TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.memoize.volatile import ATTR
from zExceptions import NotFound
from zope.component import adapts
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.interface import implements

import transaction
import unittest2 as unittest
from plone.app.blocks.utils import resolveResource


class TestTransforms(unittest.TestCase):

    layer = BLOCKS_INTEGRATION_TESTING

    def test_transforms_with_crlf(self):
        """Test issues where layouts with CR+LF line-endings are somehow
        turned into having &#13; line-endings and gettind their heads
        being dropped.
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
        result = applyTransform(request)
        self.assertIn('<head>', ''.join(result))