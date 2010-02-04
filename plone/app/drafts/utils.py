from zope.component import queryUtility
from zope.component import getAdapters

from zope.intid.interfaces import IIntIds

from plone.app.drafts.interfaces import IDraftStorage
from plone.app.drafts.interfaces import IDraftSyncer
from plone.app.drafts.interfaces import ICurrentDraftManagement

from AccessControl import getSecurityManager

def syncDraft(draft, target):
    """Look up all (named) IDraftSyncer adapters from (draft, target) and
    call each one in turn.
    """
    
    for name, syncer in getAdapters((draft, target), IDraftSyncer):
        syncer()

def getCurrentDraft(request, create=False):
    """Get the current draft as stored in the request.
    
    The request must have been set up via an ``ICurrentDraftManagement``
    adapter. This should happen in the integration layer between the drafts
    storage and the draft edit form.
    
    If no draft is available, but a user id and target key have been given,
    a new draft will be created if ``create`` is True.
    
    If not found, return None.
    """
    
    current = ICurrentDraftManagement(request, None)
    if current is None:
        return None
    
    draft = current.draft
    if draft is not None:
        return draft
    
    if create and current.userId and current.targetKey:
        storage = queryUtility(IDraftStorage)
        if storage is None:
            return None
        
        draft = storage.createDraft(current.userId, current.targetKey)
        
        current.draft = draft
        current.draftName = draft.__name__
        
        current.save()
        
        return draft
    
    return None

def getCurrentUserId():
    """Get the current user id. Returns None if the user is Anonymous.
    """
    
    return getSecurityManager().getUser().getId()

def getDefaultKey(context):
    """Get the default (string) key for the given context, based on intiids
    """
    
    intids = queryUtility(IIntIds)
    if intids is None:
        return None
    
    intid = intids.queryId(context)
    if intid is None:
        return None
    
    return str(intid)
