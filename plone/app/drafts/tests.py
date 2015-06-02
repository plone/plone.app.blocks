from plone.app.drafts.draft import Draft
from plone.app.drafts.interfaces import ICurrentDraftManagement
from plone.app.drafts.interfaces import IDraft
from plone.app.drafts.interfaces import IDraftProxy
from plone.app.drafts.interfaces import IDraftStorage
from plone.app.drafts.interfaces import IDraftSyncer
from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.proxy import DraftProxy
from plone.app.drafts.testing import DRAFTS_AT_FUNCTIONAL_TESTING
from plone.app.drafts.testing import DRAFTS_DX_FUNCTIONAL_TESTING
from plone.app.drafts.testing import DRAFTS_INTEGRATION_TESTING
from plone.app.drafts.utils import getCurrentDraft
from plone.app.drafts.utils import getCurrentUserId
from plone.app.drafts.utils import getDefaultKey
from plone.app.drafts.utils import syncDraft
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.testing.z2 import Browser
from plone.uuid.interfaces import IUUID
import transaction
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.component import getUtility
from zope.component import provideAdapter
from zope.component import queryUtility
from zope.interface import implements
import pkg_resources
import unittest

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True

try:
    pkg_resources.get_distribution('Products.ATContentTypes')
except pkg_resources.DistributionNotFound:
    HAS_ATCONTENTTYPES = False
else:
    HAS_ATCONTENTTYPES = True


class TestSetup(unittest.TestCase):
    
    layer = DRAFTS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
    
    def test_tool_installed(self):
        self.failUnless('portal_drafts' in self.portal.objectIds())
        util = queryUtility(IDraftStorage)
        self.failUnless(IDraftStorage.providedBy(util))


class TestStorage(unittest.TestCase):

    layer = DRAFTS_INTEGRATION_TESTING

    def setUp(self):
        self.storage = getUtility(IDraftStorage)

    def test_createDraft(self):
        draft = self.storage.createDraft('user1', '123')
        self.failUnless(IDraft.providedBy(draft))
        self.failUnless(draft.__name__ in self.storage.drafts['user1']['123'])
    
    def test_createDraft_existing_user_and_key(self):
        draft1 = self.storage.createDraft('user1', '123')
        draft2 = self.storage.createDraft('user1', '123')
        
        self.assertNotEqual(draft1.__name__, draft2.__name__)
        self.failUnless(draft1.__name__ in self.storage.drafts['user1']['123'])
        self.failUnless(draft2.__name__ in self.storage.drafts['user1']['123'])
    
    def test_createDraft_existing_user_only(self):
        draft1 = self.storage.createDraft('user1', '123')
        draft2 = self.storage.createDraft('user1', '345')
        
        self.failUnless(draft1.__name__ in self.storage.drafts['user1']['123'])
        self.failUnless(draft2.__name__ in self.storage.drafts['user1']['123'])
    
    def test_createDraft_factory(self):
        def factory(userId, targetKey):
            return Draft(name=u"foo")
        
        draft1 = self.storage.createDraft('user1', '123', factory=factory)
        self.assertEquals(u"foo", draft1.__name__)
        self.failUnless(draft1.__name__ in self.storage.drafts['user1']['123'])
        
        draft2 = self.storage.createDraft('user1', '123', factory=factory)
        self.assertEquals(u"foo-1", draft2.__name__)
        self.failUnless(draft2.__name__ in self.storage.drafts['user1']['123'])
    
    def test_discardDrafts(self):
        self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '123')
        self.storage.discardDrafts('user1', '123')
        self.failIf('user1' in self.storage.drafts)
    
    def test_discardDrafts_keep_user(self):
        self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '234')
        self.storage.discardDrafts('user1', '123')
        
        self.failUnless('user1' in self.storage.drafts)
        self.failIf('123' in self.storage.drafts['user1'])
        self.failUnless('234' in self.storage.drafts['user1'])
    
    def test_discardDrafts_all_for_user(self):
        self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '234')
        self.storage.createDraft('user2', '123')
        self.storage.discardDrafts('user1')
        
        self.failIf('user1' in self.storage.drafts)
        self.failUnless('user2' in self.storage.drafts)
        self.failUnless('123' in self.storage.drafts['user2'])
    
    def test_discardDrafts_no_key(self):
        self.storage.createDraft('user1', '123')
        self.storage.discardDrafts('user1', '345')
        self.failIf('345' in self.storage.drafts['user1'])
    
    def test_discardDrafts_no_user(self):
        self.storage.createDraft('user1', '123')
        self.storage.discardDrafts('user2', '123')
        self.failIf('user2' in self.storage.drafts)
    
    def test_discardDraft(self):
        draft = self.storage.createDraft('user1', '123')
        self.storage.discardDraft(draft)
        self.failIf('user1' in self.storage.drafts)
    
    def test_discardDraft_keep_user_and_target(self):
        draft = self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '123')
        self.storage.discardDraft(draft)
        self.assertEquals(1, len(self.storage.drafts['user1']['123']))
    
    def test_discardDraft_keep_user(self):
        draft = self.storage.createDraft('user1', '123')
        self.storage.createDraft('user1', '124')
        self.storage.discardDraft(draft)
        self.assertEquals(1, len(self.storage.drafts['user1']))
        self.failUnless('124' in self.storage.drafts['user1'])
    
    def test_discardDraft_not_found(self):
        self.storage.createDraft('user1', '123')
        draft = Draft('user1', '123', u"bogus")
        self.storage.discardDraft(draft)
    
    def test_discardDraft_no_key(self):
        self.storage.createDraft('user1', '123')
        draft = Draft('user1', '234', u"draft")
        self.storage.discardDraft(draft)
    
    def test_discardDraft_no_user(self):
        self.storage.createDraft('user1', '123')
        draft = Draft('user2', '123', u"draft")
        self.storage.discardDraft(draft)
    
    def test_getDrafts(self):
        draft1 = self.storage.createDraft('user1', '123')
        draft2 = self.storage.createDraft('user1', '123')
        
        drafts = self.storage.getDrafts('user1', '123')
        self.assertEquals(drafts[draft1.__name__], draft1)
        self.assertEquals(drafts[draft2.__name__], draft2)
    
    def test_getDrafts_no_user(self):
        self.storage.createDraft('user1', '123')
        drafts = self.storage.getDrafts('user2', '123')
        self.assertEquals(0, len(drafts))
    
    def test_getDrafts_no_key(self):
        self.storage.createDraft('user1', '123')
        drafts = self.storage.getDrafts('user2', '234')
        self.assertEquals(0, len(drafts))
    
    def test_getDraft_found(self):
        draft = self.storage.createDraft('user1', '123')
        self.assertEquals(draft, self.storage.getDraft('user1', '123', draft.__name__))
    
    def test_getDraft_not_found(self):
        self.storage.createDraft('user1', '123')
        self.assertEquals(None, self.storage.getDraft('user1', '123', u"bogus"))
    
    def test_getDraft_no_key(self):
        draft = self.storage.createDraft('user1', '123')
        self.assertEquals(None, self.storage.getDraft('user1', '234', draft.__name__))
    
    def test_getDraft_no_user(self):
        draft = self.storage.createDraft('user1', '123')
        self.assertEquals(None, self.storage.getDraft('user2', '123', draft.__name__))


class TestDraftProxy(unittest.TestCase):
    
    layer = DRAFTS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        setRoles(self.portal,TEST_USER_ID, ['Contributor'])
        login(self.portal, TEST_USER_NAME)

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']

    def test_attributes(self):
        
        self.folder.invokeFactory('Document', 'd1')
        target = self.folder['d1']
        
        target.title = u"Old title"
        
        draft = Draft()
        draft.someAttribute = 1
        
        proxy = DraftProxy(draft, target)
        
        self.assertEquals(u"Old title", proxy.title)
        self.assertEquals(1, proxy.someAttribute)
        
        proxy.title = u"New title"
        
        self.assertEquals(u"New title", proxy.title)

    def test_attribute_deletion(self):
        
        self.folder.invokeFactory('Document', 'd1')
        target = self.folder['d1']
        
        target.title = u"Old title"
        target.description = u"Old description"
        
        draft = Draft()
        
        draft.someAttribute = 1
        draft.description = u"New description"
        
        proxy = DraftProxy(draft, target)
        
        del proxy.someAttribute
        del proxy.title
        del proxy.description
        
        self.assertEquals(set(['someAttribute', 'title', 'description']), draft._proxyDeleted)
        
        self.failIf(hasattr(draft, 'someAttribute'))
        self.failIf(hasattr(draft, 'title'))
        self.failIf(hasattr(draft, 'description'))
        
        self.failIf(hasattr(proxy, 'someAttribute'))
        self.failIf(hasattr(proxy, 'title'))
        self.failIf(hasattr(proxy, 'description'))
        
        self.assertEquals(u"Old title", target.title)
        self.assertEquals(u"Old description", target.description)
    
    def test_interfaces(self):
        
        self.folder.invokeFactory('Document', 'd1')
        target = self.folder['d1']
        
        draft = Draft()
        proxy = DraftProxy(draft, target)
        
        self.failIf(IDraft.providedBy(proxy))
        self.failUnless(IDraftProxy.providedBy(proxy))

        if HAS_PLONE_APP_CONTENTTYPES:
            from plone.app.contenttypes.interfaces import IDocument
            self.failUnless(IDocument.providedBy(proxy))
        elif HAS_ATCONTENTTYPES:
            from Products.ATContentTypes.interfaces import IATDocument
            self.failUnless(IATDocument.providedBy(proxy))

    def test_annotations(self):
        
        self.folder.invokeFactory('Document', 'd1')
        target = self.folder['d1']
        
        targetAnnotations = IAnnotations(target)
        targetAnnotations[u"test.key"] = 123
        targetAnnotations[u"other.key"] = 456
        
        draft = Draft()
        
        draftAnnotations = IAnnotations(draft)
        draftAnnotations[u"some.key"] = 234
        
        proxy = DraftProxy(draft, target)
        
        proxyAnnotations = IAnnotations(proxy)
        
        self.assertEquals(123, proxyAnnotations[u"test.key"])
        self.assertEquals(234, proxyAnnotations[u"some.key"])
        
        proxyAnnotations[u"test.key"] = 789
        
        self.assertEquals(789, proxyAnnotations[u"test.key"])
        self.assertEquals(123, targetAnnotations[u"test.key"])
        
        # Annotations API
        
        self.assertEquals(789, proxyAnnotations.get(u"test.key"))
        
        keys = proxyAnnotations.keys()
        self.failUnless(u"test.key" in keys)
        self.failUnless(u"some.key" in keys)
        self.failUnless(u"other.key" in keys)
                
        self.assertEquals(789, proxyAnnotations.setdefault(u"test.key", -1))
        self.assertEquals(234, proxyAnnotations.setdefault(u"some.key", -1))
        self.assertEquals(456, proxyAnnotations.setdefault(u"other.key", -1))
        self.assertEquals(-1, proxyAnnotations.setdefault(u"new.key", -1))
        
        del proxyAnnotations[u"test.key"]
        self.failIf(u"test.key" in proxyAnnotations)
        self.failIf(u"test.key" in draftAnnotations)
        self.failUnless(u"test.key" in targetAnnotations)
        self.failUnless(u"test.key" in draft._proxyAnnotationsDeleted)
        
        del proxyAnnotations[u"some.key"]
        self.failIf(u"some.key" in proxyAnnotations)
        self.failIf(u"some.key" in draftAnnotations)
        self.failIf(u"some.key" in targetAnnotations)
        self.failUnless(u"some.key" in draft._proxyAnnotationsDeleted)
        
        del proxyAnnotations[u"other.key"] # this key was never in the proxy/draft
        self.failIf(u"other.key" in proxyAnnotations)
        self.failIf(u"other.key" in draftAnnotations)
        self.failUnless(u"other.key" in targetAnnotations)
        self.failUnless(u"other.key" in draft._proxyAnnotationsDeleted)


class TestDraftSyncer(unittest.TestCase):
    
    layer = DRAFTS_INTEGRATION_TESTING

    def test_syncDraft(self):
        
        class Target(object):
            pass
        
        draft = Draft()
        draft.a1 = 1
        draft.a2 = 2
        
        target = Target()
        
        class Syncer1(object):
            implements(IDraftSyncer)
            adapts(Draft, Target)
            
            def __init__(self, draft, target):
                self.draft = draft
                self.target = target
            
            def __call__(self):
                self.target.a1 = self.draft.a1
        
        provideAdapter(Syncer1, name=u"s1")
        
        class Syncer2(object):
            implements(IDraftSyncer)
            adapts(Draft, Target)
            
            def __init__(self, draft, target):
                self.draft = draft
                self.target = target
            
            def __call__(self):
                self.target.a2 = self.draft.a2
        
        provideAdapter(Syncer2, name=u"s2")
        
        syncDraft(draft, target)
        
        self.assertEquals(1, target.a1)
        self.assertEquals(2, target.a2)


class TestCurrentDraft(unittest.TestCase):
    
    layer = DRAFTS_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer['request']
    
    def test_userId(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(TEST_USER_ID, current.userId)
        
        current.userId = u"third-user"
        self.assertEquals(u"third-user", current.userId)
        
    def test_targetKey(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(None, current.targetKey)
        
        request.set('plone.app.drafts.targetKey', u"123")
        self.assertEquals(u"123", current.targetKey)
        
        current.targetKey = u"234"
        self.assertEquals(u"234", current.targetKey)
        
        self.assertEquals(u"123", request.get('plone.app.drafts.targetKey'))
    
    def test_draftName(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(None, current.draftName)
        
        request.set('plone.app.drafts.draftName', u"draft-1")
        self.assertEquals(u"draft-1", current.draftName)
        
        current.draftName = u"draft-2"
        self.assertEquals(u"draft-2", current.draftName)
        
        self.assertEquals(u"draft-1", request.get('plone.app.drafts.draftName'))
    
    def test_path(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(None, current.path)
        
        request.set('plone.app.drafts.path', u"/test")
        self.assertEquals(u"/test", current.path)
        
        current.path = u"/test/test-1"
        self.assertEquals(u"/test/test-1", current.path)
        
        self.assertEquals(u"/test", request.get('plone.app.drafts.path'))
    
    def test_draft(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(None, current.draft)
        
        current.userId = u"user1"
        current.targetKey = u"123"
        current.draftName = u"draft"
        
        self.assertEquals(None, current.draft)
        
        storage = getUtility(IDraftStorage)
        created = storage.createDraft(u"user1", u"123")
        current.draftName = created.__name__
        
        self.assertEquals(created, current.draft)
        
        newDraft = storage.createDraft(u"user1", u"123")
        current.draft = newDraft
        
        self.assertEquals(newDraft, current.draft)
    
    def test_defaultPath(self):
        request = self.request
        
        request['URL'] = 'http://nohost'
        
        current = ICurrentDraftManagement(request)
        self.assertEquals("/", current.defaultPath)
        
        request['URL'] = 'http://nohost/'
        self.assertEquals("/", current.defaultPath)
        
        request['URL'] = 'http://nohost/test/edit'
        self.assertEquals("/test", current.defaultPath)
        
        request['URL'] = 'http://nohost/test/edit/'
        self.assertEquals("/test/edit", current.defaultPath)
    
    def test_mark(self):
        request = self.request
        
        current = ICurrentDraftManagement(request)
        current.mark()
        self.failIf(IDrafting.providedBy(request))
        
        current.targetKey = u"123"
        current.mark()
        self.failUnless(IDrafting.providedBy(request))
    
    def test_save(self):
        request = self.request
        response = request.response
        
        current = ICurrentDraftManagement(request)
        self.assertEquals(False, current.save())
        
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
        self.failIf('plone.app.drafts.userId' in response.cookies)
        self.failIf('plone.app.drafts.path' in response.cookies)
        
        current.targetKey = u"123"
        self.assertEquals(True, current.save())
        
        self.assertEquals({'value': '123', 'quoted': True, 'path': '/'}, response.cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in response.cookies)
        self.failIf('plone.app.drafts.path' in response.cookies)
        
        current.targetKey = u"123"
        current.draftName = u"draft-1"
        self.assertEquals(True, current.save())
        
        self.assertEquals({'value': '123', 'quoted': True, 'path': '/'}, response.cookies['plone.app.drafts.targetKey'])
        self.assertEquals({'value': 'draft-1', 'quoted': True, 'path': '/'}, response.cookies['plone.app.drafts.draftName'])
        self.failIf('plone.app.drafts.path' in response.cookies)
        
        current.targetKey = u"123"
        current.draftName = u"draft-1"
        current.path = '/test'
        self.assertEquals(True, current.save())

        self.assertEquals({'value': '123', 'quoted': True, 'path': '/test'}, response.cookies['plone.app.drafts.targetKey'])
        self.assertEquals({'value': 'draft-1', 'quoted': True, 'path': '/test'}, response.cookies['plone.app.drafts.draftName'])
        self.assertEquals({'value': '/test', 'quoted': True, 'path': '/test'}, response.cookies['plone.app.drafts.path'])

    def test_discard(self):
        request = self.request
        response = request.response
        
        current = ICurrentDraftManagement(request)
        current.discard()
        
        deletedToken = {'expires': 'Wed, 31-Dec-97 23:59:59 GMT', 'max_age': 0,
                        'path': '/', 'quoted': True, 'value': 'deleted'}
        
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.targetKey'])
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.draftName'])
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.path'])
        
        current.path = "/test"
        current.discard()
        
        deletedToken['path'] = '/test'
        
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.targetKey'])
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.draftName'])
        self.assertEquals(deletedToken, response.cookies['plone.app.drafts.path'])


class TestUtils(unittest.TestCase):
    
    layer = DRAFTS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        setRoles(self.portal,TEST_USER_ID, ['Contributor'])
        login(self.portal, TEST_USER_NAME)

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']
        self.request = self.layer['request']

    def test_getUserId(self):
        self.assertEquals(TEST_USER_ID, getCurrentUserId())
    
    def test_getUserId_anonymous(self):
        logout()
        self.assertEquals(None, getCurrentUserId())
    
    def test_getDefaultKey(self):
        uuid = IUUID(self.folder)
        self.assertEquals(str(uuid), getDefaultKey(self.folder))
    
    def test_getCurrentDraft_not_set_no_create(self):
        request = self.request
        draft = getCurrentDraft(request)
        self.assertEquals(None, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_not_set_no_details_create(self):
        request = self.request
        draft = getCurrentDraft(request, create=True)
        self.assertEquals(None, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_draft_set(self):
        request = self.request
        
        management = ICurrentDraftManagement(request)
        management.draft = setDraft = Draft()
        
        draft = getCurrentDraft(request)
        self.assertEquals(setDraft, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_draft_set_create(self):
        request = self.request
        
        management = ICurrentDraftManagement(request)
        management.draft = setDraft = Draft()
        
        draft = getCurrentDraft(request, create=True)
        self.assertEquals(setDraft, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_draft_details_set_not_in_storage(self):
        request = self.request
        
        management = ICurrentDraftManagement(request)
        management.userId = u"user1"
        management.targetKey = u"123"
        management.draftName = u"bogus"
        
        draft = getCurrentDraft(request)
        self.assertEquals(None, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_draft_details_set_not_in_storage_create(self):
        request = self.request
        
        management = ICurrentDraftManagement(request)
        management.userId = u"user1"
        management.targetKey = u"123"
        management.draftName = u"bogus"
        
        draft = getCurrentDraft(request, create=True)
        inStorage = getUtility(IDraftStorage).getDraft(u"user1", u"123", draft.__name__)
        
        self.assertEquals(inStorage, draft)
        
        response = request.response
        self.failUnless('plone.app.drafts.targetKey' in response.cookies)
        self.failUnless('plone.app.drafts.draftName' in response.cookies)
        
        self.assertEquals('123', response.cookies['plone.app.drafts.targetKey']['value'])
        self.assertEquals(draft.__name__, response.cookies['plone.app.drafts.draftName']['value'])
    
    def test_getCurrentDraft_draft_details_set_in_storage(self):
        request = self.request
        
        inStorage = getUtility(IDraftStorage).createDraft(u"user1", u"123")
        
        management = ICurrentDraftManagement(request)
        management.userId = u"user1"
        management.targetKey = u"123"
        management.draftName = inStorage.__name__
        
        draft = getCurrentDraft(request)
        self.assertEquals(inStorage, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)
    
    def test_getCurrentDraft_draft_details_set_in_storage_create(self):
        request = self.request
        
        inStorage = getUtility(IDraftStorage).createDraft(u"user1", u"123")
        
        management = ICurrentDraftManagement(request)
        management.userId = u"user1"
        management.targetKey = u"123"
        management.draftName = inStorage.__name__
        
        draft = getCurrentDraft(request, create=True)
        self.assertEquals(inStorage, draft)
        
        response = request.response
        self.failIf('plone.app.drafts.targetKey' in response.cookies)
        self.failIf('plone.app.drafts.draftName' in response.cookies)


class TestArchetypesIntegration(unittest.TestCase):
    
    layer = DRAFTS_AT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']

        transaction.commit()

    def test_add_to_portal_root_cancel(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.portal.absolute_url() + '/portal_factory/Document/document.2010-02-04.2866363923/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"/plone/portal_factory/Document/document.2010-02-04.2866363923"', cookies['plone.app.drafts.path'])
        self.assertEquals('"0%3ADocument"', cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
        # We can now cancel the edit. The cookies should expire.
        browser.getControl(name='form.button.cancel').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
    def test_add_to_portal_root_save(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.portal.absolute_url() + '/portal_factory/Document/document.2010-02-04.2866363923/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"/plone/portal_factory/Document/document.2010-02-04.2866363923"', cookies['plone.app.drafts.path'])
        self.assertEquals('"0%3ADocument"', cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
        # We can now fill in the required fields and save. The cookies should expire.
        
        browser.getControl(name='title').value = u"New document"
        browser.getControl(name='form.button.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
    def test_add_to_folder(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        uuid = IUUID(self.folder)
        
        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.folder.absolute_url() + '/portal_factory/Document/document.2010-02-04.2866363923/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals(
                '"%s/portal_factory/Document/document.2010-02-04.2866363923"' % self.folder.absolute_url_path(),
                cookies['plone.app.drafts.path']
            )
        self.assertEquals('"%s%%3ADocument"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
        # We can now cancel the edit. The cookies should expire.
        browser.getControl(name='form.button.cancel').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
    
    def test_edit(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        self.folder.invokeFactory('Document', 'd1')
        self.folder['d1'].setTitle(u"New title")

        transaction.commit()
        
        uuid = IUUID(self.folder['d1'])
        
        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.button.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
    
    def test_edit_existing_draft(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        self.folder.invokeFactory('Document', 'd1')
        self.folder['d1'].setTitle(u"New title")

        uuid = IUUID(self.folder['d1'])
        
        # Create a single draft for this object - we expect this to be used now
        storage = getUtility(IDraftStorage)
        draft = storage.createDraft(TEST_USER_ID, str(uuid))

        transaction.commit()

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.assertEquals('"%s"' % TEST_USER_ID, cookies['plone.app.drafts.userId'])
        self.assertEquals('"%s"' % draft.__name__, cookies['plone.app.drafts.draftName'])
        
        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.button.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.userId' in browser.cookies.forURL(browser.url))

    def test_edit_multiple_existing_drafts(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        
        self.folder.invokeFactory('Document', 'd1')
        self.folder['d1'].setTitle(u"New title")

        transaction.commit()

        uuid = IUUID(self.folder['d1'])
        
        # Create two drafts for this object - we don't expect either to be used
        storage = getUtility(IDraftStorage)
        storage.createDraft(TEST_USER_ID, str(uuid))
        storage.createDraft(TEST_USER_ID, str(uuid))
        
        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()
        
        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # Confirm pass CSRF protection
        try:
            browser.getControl(name='form.button.confirm').click()
        except LookupError:
            pass

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        
        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.button.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))


class TestDexterityIntegration(unittest.TestCase):

    layer = DRAFTS_DX_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']

        transaction.commit()

    def test_add_to_portal_root_cancel(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.portal.absolute_url() + '/++add++MyDocument')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"/plone"', cookies['plone.app.drafts.path'])
        self.assertEquals('"%2B%2Badd%2B%2BMyDocument"', cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

        # We can now cancel the edit. The cookies should expire.
        browser.getControl(name='form.buttons.cancel').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

    def test_add_to_portal_root_save(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.portal.absolute_url() + '/++add++MyDocument')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"/plone"', cookies['plone.app.drafts.path'])
        self.assertEquals('"%2B%2Badd%2B%2BMyDocument"', cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

        # We can now fill in the required fields and save. The cookies should expire.

        browser.getControl(name='form.widgets.IDublinCore.title').value = u"New Document"
        browser.getControl(name='form.buttons.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

    def test_add_to_folder(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the add screen for a temporary portal_factory-managed object
        browser.open(self.folder.absolute_url() + '/++add++MyDocument')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals(
            '"%s"' % self.folder.absolute_url_path(),
            cookies['plone.app.drafts.path']
        )
        self.assertEquals('"%2B%2Badd%2B%2BMyDocument"', cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

        # We can now cancel the edit. The cookies should expire.
        browser.getControl(name='form.buttons.cancel').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))

    def test_edit(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        self.folder.invokeFactory('MyDocument', 'd1')
        self.folder['d1'].title = u"New title"

        transaction.commit()

        uuid = IUUID(self.folder['d1'])

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.buttons.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

    def test_edit_existing_draft(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        self.folder.invokeFactory('MyDocument', 'd1')
        self.folder['d1'].title = u"New title"

        uuid = IUUID(self.folder['d1'])

        # Create a single draft for this object - we expect this to be used now
        storage = getUtility(IDraftStorage)
        draft = storage.createDraft(TEST_USER_ID, str(uuid))

        transaction.commit()

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.assertEquals('"%s"' % TEST_USER_ID, cookies['plone.app.drafts.userId'])
        self.assertEquals('"%s"' % draft.__name__, cookies['plone.app.drafts.draftName'])

        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.buttons.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.userId' in browser.cookies.forURL(browser.url))

    def test_edit_multiple_existing_drafts(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        self.folder.invokeFactory('MyDocument', 'd1')
        self.folder['d1'].title = u"New title"

        transaction.commit()

        uuid = IUUID(self.folder['d1'])

        # Create two drafts for this object - we don't expect either to be used
        storage = getUtility(IDraftStorage)
        storage.createDraft(TEST_USER_ID, str(uuid))
        storage.createDraft(TEST_USER_ID, str(uuid))

        # Login
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl('Log in').click()

        # Enter the edit screen
        browser.open(self.folder['d1'].absolute_url() + '/edit')

        # We should now have cookies with the drafts information
        cookies = browser.cookies.forURL(browser.url)
        self.assertEquals('"%s"' % self.folder['d1'].absolute_url_path(), cookies['plone.app.drafts.path'])
        self.assertEquals('"%s"' % uuid, cookies['plone.app.drafts.targetKey'])
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))

        # We can now save the page. The cookies should expire.
        browser.getControl(name='form.buttons.save').click()
        self.failIf('plone.app.drafts.targetKey' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.path' in browser.cookies.forURL(browser.url))
        self.failIf('plone.app.drafts.draftName' in browser.cookies.forURL(browser.url))
