# -*- coding: utf-8 -*-
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zExceptions import NotFound
from zope.component import getGlobalSiteManager
from zope.component import getMultiAdapter
from zope.component import getUtility
import pkg_resources
import transaction
import unittest


try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True


class TestPageSiteLayout(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.registry = getUtility(IRegistry)
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        self.portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(self.portal, TEST_USER_ID, ('Member',))

        # setup default behavior
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] =\
            '/++sitelayout++testlayout1/site.html'
        if HAS_PLONE_APP_CONTENTTYPES:
            from plone.app.contenttypes.interfaces import IDocument
            iface = IDocument
        else:
            iface = self.portal['f1']['d1'].__class__

        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.layoutbehavior import LayoutAwareBehavior

        sm = getGlobalSiteManager()
        sm.registerAdapter(LayoutAwareBehavior, [iface])
        registrations = sm.getAdapters(
            (self.portal['f1']['d1'],),
            ILayoutAware
        )
        self.assertEqual(len(list(registrations)), 1)
        self.behavior = ILayoutAware(self.portal['f1']['d1'])
        registrations = sm.getAdapters(
            (self.portal['f1']['d1'],),
            ILayoutAware
        )
        self.assertEqual(len(list(registrations)), 1)

    def test_page_site_layout_no_registry_key(self):
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = None
        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        self.assertRaises(NotFound, view.index)

        from plone.app.blocks.layoutbehavior import SiteLayoutView
        default_view = SiteLayoutView(self.portal['f1']['d1'], self.request)
        self.assertEqual(view().split(), default_view().split())

    def test_page_site_layout_default(self):
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] =\
            '/++sitelayout++testlayout1/site.html'
        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()
        self.assertTrue(u"Layout title" in rendered)

    def test_page_site_layout_page_override(self):
        self.behavior.customContentLayout = u"<html><body>N/A</body></html>"
        self.behavior.pageSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

    def test_page_site_layout_section_override(self):
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter(
            (self.portal['f1']['d1'], self.request,),
            name=u'page-site-layout'
        )
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

    def test_page_site_layout_cache(self):
        self.behavior.pageSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter(
            (self.portal['f1']['d1'], self.request,),
            name=u'page-site-layout'
        )
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

        # Change the section value
        self.behavior.pageSiteLayout = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter(
            (self.portal['f1']['d1'], self.request,),
            name=u'page-site-layout'
        )
        rendered = view()

        # Cache means our change is ignored
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

    def test_page_site_layout_cache_invalidate_mtime(self):
        self.behavior.customContentLayout = u"<html><body>N/A</body></html>"
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

        # Trigger invalidation by modifying the context
        self.portal['f1']['d1'].title = u"New title"
        transaction.commit()

        # Change the section value
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"My Layout 1 Title" in rendered)

    def test_page_site_layout_cache_invalidate_catalog_counter(self):
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

        # Trigger invalidation by incrementing the catalog counter
        self.portal['portal_catalog']._increment_counter()

        # Change the section value
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"My Layout 1 Title" in rendered)

    def test_page_site_layout_cache_invalidate_registry_key(self):
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout2/mylayout.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"My Layout 1 Title" in rendered)

        # Trigger invalidation by modifying the global registry key
        self.registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] =\
            '/++sitelayout++testlayout2/mylayout.html'

        # Change the section value
        self.behavior.sectionSiteLayout = \
            '/++sitelayout++testlayout1/site.html'

        view = getMultiAdapter((self.portal['f1']['d1'], self.request,),
                               name=u'page-site-layout')
        rendered = view()

        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"My Layout 1 Title" in rendered)
