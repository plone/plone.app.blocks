from plone.app.drafts.interfaces import ICurrentDraftManagement
from plone.app.drafts.interfaces import IDraftStorage
from plone.app.drafts.utils import getCurrentDraft
from plone.app.drafts.utils import getObjectKey
from plone.app.drafts.utils import syncDraft
from zope.component import queryUtility


# Main event handlers


def beginDrafting(context, event):
    """When we enter the edit screen, set up the target key and draft cookie
    path. If there is exactly one draft for the given user id and target key,
    consider that to be the current draft. Also mark the request with
    IDrafting if applicable.
    """

    storage = queryUtility(IDraftStorage)
    if storage is None or not storage.enabled:
        return

    request = getattr(context, 'REQUEST', None)
    if request is None:
        return

    current = ICurrentDraftManagement(request)

    # Update target key regardless - we could have a stale cookie
    current.targetKey = getObjectKey(context)

    if current.draftName is None:
        drafts = storage.getDrafts(current.userId, current.targetKey)
        if len(drafts) == 1:
            current.draftName = tuple(drafts.keys())[0]

    # Save the path now so that we can use it again later, even on URLs
    # (e.g. in AJAX dialogues) that are below this path.
    current.path = current.defaultPath

    current.mark()
    current.save()


def syncDraftOnSave(context, event):
    """When the edit form is saved, sync the draft (if set) and discard it.
    Also discard the drafting cookies.
    """

    storage = queryUtility(IDraftStorage)
    if storage is None or not storage.enabled:
        return

    request = getattr(context, 'REQUEST', None)
    if request is None:
        return

    draft = getCurrentDraft(request)
    if draft is not None:
        syncDraft(draft, context)

    current = ICurrentDraftManagement(request)
    if current.userId and current.targetKey:
        storage.discardDrafts(current.userId, current.targetKey)

    current.discard()


def discardDraftsOnCancel(context, event):
    """When the edit form is cancelled, discard any unused drafts and
    remove the drafting cookies.
    """

    storage = queryUtility(IDraftStorage)
    if storage is None or not storage.enabled:
        return

    request = getattr(context, 'REQUEST', None)
    if request is None:
        return

    current = ICurrentDraftManagement(request)

    if current.userId and current.targetKey:
        storage.discardDrafts(current.userId, current.targetKey)

    current.discard()
