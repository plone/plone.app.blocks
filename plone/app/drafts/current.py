from rwproperty import getproperty, setproperty

from zope.interface import alsoProvides
from zope.interface import implements

from zope.component import adapts
from zope.component import getUtility

from zope.annotation.interfaces import IAnnotations
from zope.publisher.interfaces import IRequest

from plone.app.drafts.interfaces import IDraftStorage

from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.interfaces import ICurrentDraftManagement

from plone.app.drafts.interfaces import USERID_KEY
from plone.app.drafts.interfaces import TARGET_KEY
from plone.app.drafts.interfaces import PATH_KEY
from plone.app.drafts.interfaces import DRAFT_NAME_KEY
from plone.app.drafts.interfaces import DRAFT_KEY

from plone.app.drafts.utils import getCurrentUserId

class DefaultCurrentDraftManagement(object):
    
    implements(ICurrentDraftManagement)
    adapts(IRequest)
    
    def __init__(self, request):
        self.request = request
        self.annotations = IAnnotations(request)
    
    # User id
    
    @getproperty
    def userId(self):
        userId = self.annotations.get(USERID_KEY, None)
        if userId is None:
            return getCurrentUserId()
        return userId

    @setproperty
    def userId(self, value):
        self.annotations[USERID_KEY] = value
    
    # Target key
    
    @getproperty
    def targetKey(self):
        targetKey = self.annotations.get(TARGET_KEY, None)
        if targetKey is None:
            targetKey = self.request.get(TARGET_KEY, None)
        return targetKey
    
    @setproperty
    def targetKey(self, value):
        self.annotations[TARGET_KEY] = value
    
    # Path
    
    @getproperty
    def path(self):
        path = self.annotations.get(PATH_KEY, None)
        if path is None:
            path = self.request.get(PATH_KEY, None)
        return path
    
    @setproperty
    def path(self, value):
        self.annotations[PATH_KEY] = value
    
    # Draft name
    
    @getproperty
    def draftName(self):
        draftName = self.annotations.get(DRAFT_NAME_KEY, None)
        if draftName is None:
            draftName = self.request.get(DRAFT_NAME_KEY, None)
        return draftName
        
    @setproperty
    def draftName(self, value):
        self.annotations[DRAFT_NAME_KEY] = value
    
    # Draft
    
    @getproperty
    def draft(self):
        draft = self.annotations.get(DRAFT_KEY, None)
        if draft is None:
            if (self.userId is not None and 
                self.targetKey is not None and
                self.draftName is not None
            ):
                storage = getUtility(IDraftStorage)
                draft = storage.getDraft(self.userId, self.targetKey, self.draftName)
        return draft
    
    @setproperty
    def draft(self, value):
        self.annotations[DRAFT_KEY] = value
    
    # Request marking
    
    def mark(self):
        if self.userId and self.targetKey:
            alsoProvides(self.request, IDrafting)
    
    # Cookie management
    
    def save(self):
        if self.targetKey is None:
            return False

        path = self.path or self.defaultPath
        self.request.response.setCookie(TARGET_KEY, self.targetKey, path=path)
        
        if self.draftName is not None:
            self.request.response.setCookie(DRAFT_NAME_KEY, self.draftName, path=path)

        # Save userId, because it may be needed to access draft during traverse
        if self.draftName is not None and self.userId is not None:
            self.request.response.setCookie(USERID_KEY, self.userId, path=path)

        # Save the path only if we set it explicitly during this request.
        if self.annotations.get(PATH_KEY, None) is not None:
            self.request.response.setCookie(PATH_KEY, self.path, path=path)
        
        return True
    
    def discard(self):
        path = self.path or self.defaultPath
        self.request.response.expireCookie(USERID_KEY, path=path)
        self.request.response.expireCookie(TARGET_KEY, path=path)
        self.request.response.expireCookie(DRAFT_NAME_KEY, path=path)
        self.request.response.expireCookie(PATH_KEY, path=path)
    
    @property
    def defaultPath(self):
        # Get the context minus the view
        url = '/'.join(self.request.getURL().split('/')[:-1])
        server = self.request.get('SERVER_URL')
        path = url[len(server):]
        if not path:
            return '/'
        elif path.endswith('/'):
            return path[:-1]
        else:
            return path
