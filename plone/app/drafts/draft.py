# -*- coding: utf-8 -*-
from persistent import Persistent
from plone.app.drafts.interfaces import IDraft
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.interface import implementer


@implementer(IDraft, IAttributeAnnotatable)
class Draft(Persistent):
    """Basic draft object.

    Attributes and annotations may be set as required.
    """

    def __init__(self, userId=None, targetKey=None, name=None):
        self._draftUserId = userId
        self._draftTargetKey = targetKey
        self.__name__ = name
