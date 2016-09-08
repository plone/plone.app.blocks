# -*- coding: utf-8 -*-
from zope import event
from plone.uuid.interfaces import IUUID
from zope.globalrequest import getRequest
from zope.lifecycleevent import ObjectModifiedEvent
from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.interfaces import ICurrentDraftManagement
from plone.app.drafts.lifecycle import syncDraftOnSave
from plone.app.drafts.utils import getCurrentDraft


def subscriber(event):
    # Only listen to ObjectModifiedEvent
    if not isinstance(event, ObjectModifiedEvent):
        return

    # Only listen when we are drafting
    request = getRequest()
    if not IDrafting.providedBy(request):
        return

    # Only listen if its our drafting target, which has been modified
    drafting = ICurrentDraftManagement(request, None)
    if drafting is None:
        return

    source = IUUID(event.object, None)
    if source is None or source != drafting.targetKey:
        return

    # Sync draft now before indexers are called
    syncDraftOnSave(event.object, event)


def initialize(context):
    event.subscribers.insert(0, subscriber)
