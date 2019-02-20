# -*- coding: utf-8 -*-
import unittest

from plone.app.blocks.resource import getLayoutsFromResources
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.blocks.interfaces import SITE_LAYOUT_MANIFEST_FORMAT
from plone.app.blocks.interfaces import CONTENT_LAYOUT_MANIFEST_FORMAT


class TestResource(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_contentlayout_manifest(self):
        layouts = getLayoutsFromResources(CONTENT_LAYOUT_MANIFEST_FORMAT)
        self.assertTrue('testlayout1/content.html' in layouts)
        self.assertTrue('testlayout2/mylayout.html' in layouts)
        self.assertTrue('testlayout2/mylayout2.html' in layouts)

        self.assertTrue(layouts['testlayout1/content.html']['title'] == 'Testlayout1')  # noqa
        self.assertTrue(layouts['testlayout2/mylayout.html']['title'] == 'My content layout')  # noqa
        self.assertTrue(layouts['testlayout2/mylayout2.html']['title'] == 'My content layout 2')  # noqa

    def test_sitelayout_manifest(self):
        layouts = getLayoutsFromResources(SITE_LAYOUT_MANIFEST_FORMAT)
        self.assertTrue('testlayout1/site.html' in layouts)
        self.assertTrue('testlayout2/mylayout.html' in layouts)
        self.assertTrue('testlayout2/mylayout2.html' in layouts)

        self.assertTrue(layouts['testlayout1/site.html']['title'] == 'Testlayout1')  # noqa
        self.assertTrue(layouts['testlayout2/mylayout.html']['title'] == 'My site layout')  # noqa
        self.assertTrue(layouts['testlayout2/mylayout2.html']['title'] == 'My site layout 2')  # noqa
