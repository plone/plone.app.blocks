# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-plone.app.blocks:default'


def upgrade_settings(context):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')


def upgrade_rolemap(context):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
