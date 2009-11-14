from zope.interface import Interface, implements
from zope import schema

from plone.app.blocks.interfaces import ITilePageRendered

class IDemoTile(Interface):
    
    magic_number = schema.Int(title=u"Magic number", required=False)

class DemoTilePageView(object):
    implements(ITilePageRendered)
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
