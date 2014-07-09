# -*- coding: utf-8 -*-
from plone.resource.manifest import ManifestFormat
from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface


SITE_LAYOUT_RESOURCE_NAME = "sitelayout"
SITE_LAYOUT_FILE_NAME = "site.html"

SITE_LAYOUT_MANIFEST_FORMAT = ManifestFormat(
    SITE_LAYOUT_RESOURCE_NAME,
    keys=('title', 'description', 'file'),
    defaults={'file': SITE_LAYOUT_FILE_NAME},
    parameterSections=['variants']
)

DEFAULT_SITE_LAYOUT_REGISTRY_KEY = 'plone.defaultSiteLayout'
DEFAULT_AJAX_LAYOUT_REGISTRY_KEY = 'plone.defaultAjaxLayout'

_ = MessageFactory('plone')


class IBlocksLayer(Interface):
    """Browser layer used to ensure blocks functionality can be installed on
    a site-by-site basis for published objects (usually views), which
    provider IBlocksTransformEnabled marker interface.
    """


class IBlocksTransformEnabled(Interface):
    """Marker interface for views (or other published objects), which require
    blocks transform
    """


class IBlocksSettings(Interface):
    """Settings registered with the portal_registry tool
    """

    esi = schema.Bool(
        title=_(u"Enable Edge Side Includes"),
        description=_(u"Allows tiles which support Edge Side Includes "
                      u"(ESI) to be rendered as ESI links instead of "
                      u"invoked directly."),
        default=False,
    )


class IOmittedField(Interface):
    """Marker interface for schema fields not to be shown to users
    """


class ILayoutField(Interface):
    """Marker interface for the layout field
    """


class IBlocksRegistryAdapter(Interface):
    """Marker interface for the registry adapter"""


class IWeightedDict(Interface):
    name = schema.TextLine(title=_(u"Name"))
    label = schema.TextLine(title=_(u"Label"))
    weight = schema.Int(title=_(u"Weight"))


class IFormat(Interface):
    """Interface for the format configuration in the registry"""
    name = schema.TextLine(title=_(u"Name"))
    category = schema.TextLine(title=_(u"Category"))
    label = schema.TextLine(title=_(u"Label"))
    action = schema.TextLine(title=_(u"Action"))
    icon = schema.Bool(title=_(u"Icon"))
    favorite = schema.Bool(title=_(u"Favorite"))
    weight = schema.Int(title=_(u"Weight"))


class IAction(Interface):
    name = schema.TextLine(title=_(u"Name"))
    fieldset = schema.TextLine(title=_(u"Fieldset"))
    label = schema.TextLine(title=_(u"Label"))
    action = schema.TextLine(title=_(u"Action"))
    icon = schema.Bool(title=_(u"Icon"))
    menu = schema.Bool(title=_(u"Menu"))
    weight = schema.Int(title=_(u"Weight"))


class IFieldTile(Interface):
    """Interface for the field tile configuration in the registry
    """
    id = schema.TextLine(title=_(u"The widget id"))
    name = schema.TextLine(title=_(u"Name"))
    label = schema.TextLine(title=_(u"Label"))
    category = schema.TextLine(title=_(u"Category"))
    tile_type = schema.TextLine(title=_(u"Type"))
    read_only = schema.Bool(title=_(u"Read only"))
    favorite = schema.Bool(title=_(u"Favorite"))
    widget = schema.TextLine(title=_(u"Field widget"))
    available_actions = schema.List(title=_(u"Actions"),
                                    value_type=schema.TextLine())


class ITile(Interface):
    """Interface for the tile configuration in the registry"""
    name = schema.TextLine(title=_(u"Name"))
    label = schema.TextLine(title=_(u"Label"))
    category = schema.TextLine(title=_(u"Category"))
    tile_type = schema.TextLine(title=_(u"Type"))
    default_value = schema.TextLine(title=_(u"Default value"), required=False)
    read_only = schema.Bool(title=_(u"Read only"))
    settings = schema.Bool(title=_(u"Settings"))
    favorite = schema.Bool(title=_(u"Favorite"))
    rich_text = schema.Bool(title=_(u"Rich Text"))
    weight = schema.Int(title=_(u"Weight"))


class IWidgetAction(Interface):
    name = schema.TextLine(title=_(u"Name"))
    actions = schema.List(title=_(u"Actions"),
                          value_type=schema.TextLine())

