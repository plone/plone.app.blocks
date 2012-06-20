from zope.i18nmessageid import MessageFactory

from zope.interface import Interface
from zope import schema

from plone.resource.manifest import ManifestFormat

SITE_LAYOUT_RESOURCE_NAME = "sitelayout"
SITE_LAYOUT_FILE_NAME = "site.html"

SITE_LAYOUT_MANIFEST_FORMAT = ManifestFormat(SITE_LAYOUT_RESOURCE_NAME,
        keys=('title', 'description', 'file'),
        defaults={'file': SITE_LAYOUT_FILE_NAME},
    )

DEFAULT_SITE_LAYOUT_REGISTRY_KEY = 'plone.defaultSiteLayout'

_ = MessageFactory('plone')


class IBlocksLayer(Interface):
    """Browser layer used to ensure blocks functionality can be installed on
    a site-by-site basis.
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
