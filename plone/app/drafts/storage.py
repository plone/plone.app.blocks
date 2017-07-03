# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from plone.app.drafts.draft import Draft
from plone.app.drafts.interfaces import IDraftStorage
from zope.interface import implementer


@implementer(IDraftStorage)
class Storage(SimpleItem):
    """The draft storage
    """

    id = 'portal_drafts'
    title = 'Drafts in progress for content items being edited'
    meta_type = 'Plone Drafts Storage'

    manage_options = (
        dict(label='Drafts', action='@@overview'),
    ) + SimpleItem.manage_options

    enabled = True

    def __init__(self, id='portal_drafts'):
        self.id = id
        self.drafts = OOBTree()

    def createDraft(self, userId, targetKey, factory=None):

        user = self.drafts.get(userId, None)
        if user is None:
            user = self.drafts[userId] = OOBTree()

        container = user.get(targetKey, None)
        if container is None:
            container = user[targetKey] = OOBTree()

        if factory is None:
            factory = Draft

        draft = factory(userId, targetKey)

        if not draft.__name__:
            draft.__name__ = u'draft'

        if draft.__name__ in container:
            idx = len(container)
            while u'{0}-{1}'.format(draft.__name__, idx, ) in container:
                idx += 1
            draft.__name__ = u'{0}-{1}'.format(draft.__name__, idx, )

        container[draft.__name__] = draft
        return draft

    def discardDrafts(self, userId, targetKey=None):
        if userId not in self.drafts:
            return

        if targetKey is None:
            del self.drafts[userId]
        else:
            if targetKey in self.drafts[userId]:
                del self.drafts[userId][targetKey]

                if len(self.drafts[userId]) == 0:
                    del self.drafts[userId]

    def discardDraft(self, draft):
        userId = draft._draftUserId
        targetKey = draft._draftTargetKey
        draftName = draft.__name__

        if userId not in self.drafts:
            return

        if targetKey not in self.drafts[userId]:
            return

        if draftName not in self.drafts[userId][targetKey]:
            return

        del self.drafts[userId][targetKey][draftName]

        if len(self.drafts[userId][targetKey]) == 0:
            del self.drafts[userId][targetKey]

        if len(self.drafts[userId]) == 0:
            del self.drafts[userId]

    def getDrafts(self, userId, targetKey):
        return self.drafts.get(userId, {}).get(targetKey, {})

    def getDraft(self, userId, targetKey, draftName, default=None):
        return self.getDrafts(userId, targetKey).get(draftName, default)
