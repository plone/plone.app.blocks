# -*- coding: utf-8 -*-
from lxml import html
from plone.app.blocks.layoutbehavior import ContentLayoutView
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.blocks.utils import bodyTileXPath
from plone.app.blocks.utils import tileAttrib
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.registry.interfaces import IRegistry
from zope.component import adapts
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
import pkg_resources
import unittest

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True


class TestContentLayout(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.registry = getUtility(IRegistry)

        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        self.portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(self.portal, TEST_USER_ID, ('Member',))

        if HAS_PLONE_APP_CONTENTTYPES:
            from plone.app.contenttypes.interfaces import IDocument
            iface = IDocument
        else:
            iface = self.portal['f1']['d1'].__class__

        class DocumentLayoutAware(object):
            implements(ILayoutAware)
            adapts(iface)

            def __init__(self, context):
                self.context = context

            content = None
            contentLayout = None
            sectionSiteLayout = None
            pageSiteLayout = None

        self.behavior = DocumentLayoutAware

        sm = getGlobalSiteManager()
        sm.registerAdapter(self.behavior)
        registrations = sm.getAdapters((self.portal['f1']['d1'],),
                                       ILayoutAware)
        self.assertEqual(len(list(registrations)), 1)

    def tearDown(self):
        sm = getGlobalSiteManager()
        sm.unregisterAdapter(self.behavior)
        registrations = sm.getAdapters((self.portal['f1']['d1'],),
                                       ILayoutAware)
        self.assertEqual(len(list(registrations)), 0)

    def test_content_layout_vocabulary(self):
        factory = getUtility(IVocabularyFactory,
                             name='plone.availableContentLayouts')
        vocab = factory(self.layer['portal'])
        self.assertEqual(len(vocab), 3)

        self.assertIn('testlayout1/content.html', vocab.by_token)
        self.assertEqual(
            vocab.getTermByToken('testlayout1/content.html').value,
            u'/++contentlayout++testlayout1/content.html')
        self.assertEqual(
            vocab.getTermByToken('testlayout1/content.html').title,
            'Testlayout1')

        self.assertIn('testlayout2/mylayout.html', vocab.by_token)
        self.assertEqual(
            vocab.getTermByToken('testlayout2/mylayout.html').value,
            u'/++contentlayout++testlayout2/mylayout.html')
        self.assertEqual(
            vocab.getTermByToken('testlayout2/mylayout.html').title,
            'My content layout')

        self.assertIn('testlayout2/mylayout2.html', vocab.by_token)
        self.assertEqual(
            vocab.getTermByToken('testlayout2/mylayout2.html').value,
            u'/++contentlayout++testlayout2/mylayout2.html')
        self.assertEqual(
            vocab.getTermByToken('testlayout2/mylayout2.html').title,
            'My content layout 2')

    def test_content_layout(self):
        self.behavior.contentLayout = \
            '/++contentlayout++testlayout1/content.html'
        rendered = ContentLayoutView(self.portal['f1']['d1'], self.request)()
        tree = html.fromstring(rendered)
        tiles = [node.attrib[tileAttrib] for node in bodyTileXPath(tree)]
        self.assertIn(
            './@@test.tile1/tile2?magicNumber:int=2&X-Tile-Persistent=yes',
            tiles)
        self.assertIn(
            './@@test.tile1/tile3?X-Tile-Persistent=yes',
            tiles)

    def test_error_layout(self):
        self.behavior.contentLayout = \
            '/++sitelayout++missing/missing.html'
        rendered = ContentLayoutView(self.portal['f1']['d1'], self.request)()
        self.assertIn('Could not find layout for content', rendered)
