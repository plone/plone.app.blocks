# -*- coding: utf-8 -*-
from OFS.Image import File
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CMFPlone.utils import getToolByName
from StringIO import StringIO
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import SiteLayoutView
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
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
import unittest


class TestSiteLayout(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.registry = getUtility(IRegistry)
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        self.portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(self.portal, TEST_USER_ID, ('Member',))

    def test_default_site_layout_no_registry_key(self):
        # Clear cache if there
        if hasattr(self.portal, ATTR):
            delattr(self.portal, ATTR)

        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = None

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        self.assertRaises(NotFound, view.index)

        default_view = SiteLayoutView(self.portal, self.request)
        self.assertEqual(view().split(), default_view().split())

    def test_default_site_layout(self):
        # Clear cache if there
        if hasattr(self.portal, ATTR):
            delattr(self.portal, ATTR)

        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"Layout title" in rendered)

    def test_default_site_layout_section_override(self):
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout1/site.html'

        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(self.portal['f1'].__class__)

            def __init__(self, context):
                self.context = context

            content = u"<html><body>N/A</body></html>"
            sectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
            pageSiteLayout = None

        # Register a local adapter for easy rollback
        sm = getSiteManager()
        sm.registerAdapter(FolderLayoutAware)

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)

    def test_default_site_layout_section_no_override(self):
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertFalse(u"Layout 2 title" in rendered)
        self.assertTrue(u"Layout title" in rendered)

    def test_default_site_layout_cache(self):
        # Clear cache if there
        if hasattr(self.portal, ATTR):
            delattr(self.portal, ATTR)

        resources = getToolByName(self.portal, 'portal_resources')
        resources._setOb('sitelayout', BTreeFolder2('sitelayout'))
        resources['sitelayout']._setOb('testlayout3',
                                       BTreeFolder2('testlayout3'))
        resources['sitelayout']['testlayout3']._setOb(
            'site.html', File('site.html', 'site.html', StringIO(
                '<html><head><title>ZODB test</title></head></html>'))
        )

        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout3/site.html'

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"ZODB test" in rendered)

        resources['sitelayout']['testlayout3']._delOb('site.html')
        resources['sitelayout']['testlayout3']._setOb(
            'site.html', File('site.html', 'site.html', StringIO(
                '<html><head><title>Cache test</title></head></html>'))
        )

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertFalse(u"Cache test" in rendered)  # hidden by cache
        self.assertTrue(u"ZODB test" in rendered)

        self.assertEqual('/++sitelayout++testlayout3/site.html', view.layout)

        # Test cache is set
        self.assertTrue(hasattr(self.portal, ATTR))

        # Update cache
        for key in getattr(self.portal, ATTR):
            getattr(self.portal, ATTR)[key] = None

        self.assertIsNone(view.layout)  # because of cache

    def test_default_site_layout_invalidate_mtime(self):
        # Clear cache if there
        if hasattr(self.portal, ATTR):
            delattr(self.portal, ATTR)

        resources = getToolByName(self.portal, 'portal_resources')
        resources._setOb('sitelayout', BTreeFolder2('sitelayout'))
        resources['sitelayout']._setOb('testlayout3',
                                       BTreeFolder2('testlayout3'))
        resources['sitelayout']['testlayout3']._setOb(
            'site.html', File('site.html', 'site.html', StringIO(
                '<html><head><title>ZODB test</title></head></html>'))
        )

        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout3/site.html'

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"ZODB test" in rendered)

        # Trigger invalidation by modifying the context and committing
        self.portal.title = u"New title"
        transaction.commit()

        # Modify the site layout
        resources['sitelayout']['testlayout3']._delOb('site.html')
        resources['sitelayout']['testlayout3']._setOb(
            'site.html', File('site.html', 'site.html', StringIO(
                '<html><head><title>Cache test</title></head></html>'))
        )

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"Cache test" in rendered)
        self.assertFalse(u"ZODB test" in rendered)

    def test_default_site_layout_invalidate_registry_key(self):
        # Clear cache if there
        if hasattr(self.portal, ATTR):
            delattr(self.portal, ATTR)

        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"Layout title" in rendered)

        # Trigger invalidation by modifying the global site layout selection
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter((self.portal, self.request,),
                               name=u'default-site-layout')
        rendered = view()

        self.assertTrue(u"Layout 2 title" in rendered)
        self.assertFalse(u"Layout title" in rendered)
