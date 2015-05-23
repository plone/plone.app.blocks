from AccessControl import getSecurityManager
from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from plone.uuid.interfaces import IUUID
from zope.component import queryUtility
from zope.component import getAdapters

from plone.app.drafts.interfaces import IDraftStorage
from plone.app.drafts.interfaces import IDraftSyncer
from plone.app.drafts.interfaces import ICurrentDraftManagement


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
    """Get the default (string) key for the given context, based on uuids
    """
    return IUUID(context, None)


def getObjectKey(context):
    """Get a key for an Archetypes object. This will be a string
    representation of its uuid, unless it is in the portal_factory, in
    which case it'll be the a string like
    "${parent_uuid}:portal_factory/${portal_type}"
    """

    portal_factory = getToolByName(context, 'portal_factory', None)
    if portal_factory is None or not portal_factory.isTemporary(context):
        return getDefaultKey(context)

    tempFolder = aq_parent(context)
    folder = aq_parent(aq_parent(tempFolder))

    defaultKey = getDefaultKey(folder)
    if defaultKey is None:
        # probably the portal root
        defaultKey = '0'

    return "%s:%s" % (defaultKey, tempFolder.getId())
