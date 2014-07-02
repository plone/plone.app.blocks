# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.registry import Record, field
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


import pkg_resources

try:
    pkg_resources.get_distribution('plone.app.widgets')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_WIDGETS = False
else:
    HAS_PLONE_APP_WIDGETS = True


def step_setup_various(context):
    if context.readDataFile('plone.app.blocks_default.txt') is None:
        return
    portal = context.getSite()
    if HAS_PLONE_APP_WIDGETS:
        try:
            import_profile(portal, 'profile-plone.app.widgets:default')
        except KeyError:
            pass
    initialize_default_layout_registry_values(portal)


def initialize_default_layout_registry_values(portal):
    registry = getUtility(IRegistry)
    records = (
        ('plone.defaultSiteLayout', u'Default site layout',
         u'The default site layout for the site', None),
        ('plone.defaultAjaxLayout', u'Default ajax layout',
         u'The default ajax layout for the site', None),
    )
    for key, title, description, value in records:
        if not key in registry.records:
            registry.records[key] = Record(
                field.BytesLine(
                    title=title,
                    description=description,
                    required=False
                ), value)


def import_profile(portal, profile_name):
    setup_tool = getToolByName(portal, 'portal_setup')
    if not setup_tool.getProfileImportDate(profile_name):
        setup_tool.runAllImportStepsFromProfile(profile_name)
