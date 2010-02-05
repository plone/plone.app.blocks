from zope.i18nmessageid import MessageFactory

from zope.interface import Interface
from zope import schema

_ = MessageFactory('plone.app.blocks')

class ITilePageRendered(Interface):
    """This marker interface can be applied to views that should use separate
    tile page/content.xsl rendering.
    """

class IBlocksLayer(Interface):
    """Browser layer used to ensure blocks functionality can be installed on
    a site-by-site basis.
    """

class IBlocksSettings(Interface):
    """Settings registered with the portal_registry tool
    """
    
    esi = schema.Bool(
            title=_(u"Enable Edge Side Includes"),
            description=_(u"Allows tiles which support Edge Side Includes (ESI)"
                          u"to be rendered as ESI links instead of invoked directly."),
            default=False,
        )
