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


class ILayoutField(Interface):
    """Marker interface for the layout field
    """


class IOmittedField(Interface):
    """Marker interface to distinguish the layout behavior schema fields from
    other fields to allow hiding them in the user interfaces
    """


class ILayoutFieldDefaultValue(Interface):
    """Multi adapter interface for looking up the default value for the
    layout field content
    """

    def __unicode__():
        """Return the layout as a unicode value"""

    def __str__():
        """Return the layout as a str value"""
