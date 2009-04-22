from zope.interface import Interface
from zope import schema

class IDemoTile(Interface):
    
    magic_number = schema.Int(title=u"Magic number", required=False)