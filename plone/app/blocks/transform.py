from lxml import etree, html

from plone.transformchain.interfaces import ITransform

from zope.interface import implements, Interface
from zope.component import adapts

from plone.app.blocks import tilepage
from plone.app.blocks import contentxsl

from Globals import DevelopmentMode
PRETTY_PRINT = bool(DevelopmentMode)

class ParseXML(object):
    """First stage in the 8000's chain: parse the content to an lxml tree.
    The subsequent steps until 8999 will assume their result inputs are lxml
    trees as well.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 8000
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        content_type = self.request.response.getHeader('Content-Type')
        if content_type is None or not content_type.startswith('text/html'):
            return None
        
        content_encoding = self.request.response.getHeader('Content-Encoding')
        if content_encoding and content_encoding in ('zip', 'deflate', 'compress',):
            return None
        
        parser = html.HTMLParser()
        for chunk in result:
            try:
                parser.feed(chunk)
            except (TypeError, etree.ParseError):
                return None
        try:
            root = parser.close()
        except (TypeError, etree.ParseError):
            return None
            
        return root.getroottree()

class TilePage(object):
    """Turn a published page into a tile page. Assumes the input result is
    an lxml tree and returns an lxml tree for later serialization.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 8100
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
        
        return tilepage.intercept(self.request, result)

class XSLT(object):
    """Parse XSLT processing instructions and process them.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 8500
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
        
        return contentxsl.intercept(self.request, result)

class SerializeXML(object):
    """Serialize an lxml tree to an encoded string.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 8999
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
            
        return html.tostring(result, pretty_print=PRETTY_PRINT)
