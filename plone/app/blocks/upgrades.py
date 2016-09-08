# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable

PROFILE_ID = 'profile-plone.app.blocks:default'


def upgrade_settings(context):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')


def upgrade_rolemap(context):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')


def migrate_content_to_customContentLayout(context):
    pc = getToolByName(context, 'portal_catalog')
    brains = []
    brains.extend(pc.unrestrictedSearchResults(
        object_provides=ILayoutAware.__identifier__))
    brains.extend(pc.unrestrictedSearchResults(
        object_provides=ILayoutBehaviorAdaptable.__identifier__))
    for brain in brains:
        ob = brain._unrestrictedGetObject()
        adapted = ILayoutAware(ob)
        if all([
            not getattr(adapted, 'customContentLayout', None),
            getattr(adapted, 'content', None)
        ]):
            adapted.customContentLayout = adapted.content
            adapted.content = None
