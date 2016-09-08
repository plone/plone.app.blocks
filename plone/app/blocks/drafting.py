# -*- coding: utf-8 -*-
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.drafts.interfaces import IDraft
from plone.app.drafts.interfaces import IDraftSyncer
from zope.component import adapter
from zope.interface import implementer


@implementer(IDraftSyncer)
@adapter(IDraft, ILayoutBehaviorAdaptable)
class LayoutAwareDataStorageSyncher(object):
    """Copy draft data to the real object on save
    """

    def __init__(self, draft, target):
        self.draft = draft
        self.target = target

    def __call__(self):
        try:
            ILayoutAware(self.target).content = self.draft.content
        except AttributeError:
            pass
