import unittest2 as unittest

from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING

class TestPageSiteLayout(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING
    
    def test_page_site_layout_no_registry_key(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        from zExceptions import NotFound
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = None
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        self.assertRaises(NotFound, view)
    
    def test_page_site_layout_default(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout title" in rendered)
    
    def test_page_site_layout_page_override(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        class DocumentLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1']['d1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            sectionSiteLayout = None
            pageSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(DocumentLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(DocumentLayoutAware)
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
    
    def test_page_site_layout_section_override(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            sectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
            pageSiteLayout = None
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(FolderLayoutAware)
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
    
    def test_page_site_layout_cache(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        currentSectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            pageSiteLayout = None
            
            @property
            def sectionSiteLayout(self):
                return currentSectionSiteLayout
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
        
        # Change the section value
        currentSectionSiteLayout = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(FolderLayoutAware)
        
        # Cache means our change is ignored
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
    
    def test_page_site_layout_cache_invalidate_mtime(self):
        import transaction
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        currentSectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            pageSiteLayout = None
            
            @property
            def sectionSiteLayout(self):
                return currentSectionSiteLayout
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
        
        # Trigger invalidation by modifying the context
        portal['f1']['d1'].title = u"New title"
        transaction.commit()
        
        # Change the section value
        currentSectionSiteLayout = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(FolderLayoutAware)
        
        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"Layout 2 title" in rendered)
    
    def test_page_site_layout_cache_invalidate_catalog_counter(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        currentSectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            pageSiteLayout = None
            
            @property
            def sectionSiteLayout(self):
                return currentSectionSiteLayout
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
        
        # Trigger invalidation by incrementing the catalog counter
        portal['portal_catalog']._increment_counter()
        
        # Change the section value
        currentSectionSiteLayout = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(FolderLayoutAware)
        
        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"Layout 2 title" in rendered)
    
    def test_page_site_layout_cache_invalidate_registry_key(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getGlobalSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        currentSectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            pageSiteLayout = None
            
            @property
            def sectionSiteLayout(self):
                return currentSectionSiteLayout
        
        sm = getGlobalSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
        
        # Trigger invalidation by modifying the global registry key
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout2/mylayout.html'
        
        # Change the section value
        currentSectionSiteLayout = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'page-site-layout')
        rendered = view()
        
        sm.unregisterAdapter(FolderLayoutAware)
        
        # We now get the new layout
        self.assertTrue(u"Layout title" in rendered)
        self.assertFalse(u"Layout 2 title" in rendered)
