from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def step_setup_various(context):
    if context.readDataFile("plone.app.blocks_default.txt") is None:
        return
    portal = context.getSite()
    initialize_default_layout_registry_values(portal)


def initialize_default_layout_registry_values(portal):
    registry = getUtility(IRegistry)
    records = (
        (
            "plone.defaultSiteLayout",
            "Default site layout",
            "The default site layout for the site",
            None,
        ),
        (
            "plone.defaultAjaxLayout",
            "Default ajax layout",
            "The default ajax layout for the site",
            None,
        ),
    )
    for key, title, description, value in records:
        if key not in registry.records:
            registry.records[key] = Record(
                field.BytesLine(title=title, description=description, required=False),
                value,
            )
