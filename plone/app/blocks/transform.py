from lxml import etree

from repoze.xmliter.utils import getHTMLSerializer
from repoze.xmliter.serializer import XMLSerializer

from plone.transformchain.interfaces import ITransform

from zope.interface import implements

from plone.app.blocks import tilepage, panel, tiles

from Globals import DevelopmentMode
PRETTY_PRINT = bool(DevelopmentMode)

class ParseXML(object):
    """First stage in the 8000's chain: parse the content to an lxml tree
    encapsulated in an XMLSerializer.
    
    The subsequent steps in this package will assume their result inputs are
    XMLSerializer iterables, and do nothing if it is not. This also gives us
    the option to parse the content here, and if we decide it's not HTML,
    we can avoid trying to parse it again.
    """
    
    implements(ITransform)
    
    order = 8000
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformString(self, result, encoding):
        return None
    
    def transformUnicode(self, result, encoding):
        return None
    
    def transformIterable(self, result, encoding):
        content_type = self.request.response.getHeader('Content-Type')
        if content_type is None or not content_type.startswith('text/html'):
            return None
        
        content_encoding = self.request.response.getHeader('Content-Encoding')
        if content_encoding and content_encoding in ('zip', 'deflate', 'compress',):
            return None
        
        try:
            result = getHTMLSerializer(result, pretty_print=PRETTY_PRINT, encoding=encoding)
            self.request['plone.app.blocks.enabled'] = True
            return result
        except (TypeError, etree.ParseError):
            return None

class MergePanels(object):
    """Find the site layout and merge panels.
    """
    
    implements(ITransform)
    
    order = 8100
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformString(self, result, encoding):
        return None
    
    def transformUnicode(self, result, encoding):
        return None
    
    def transformIterable(self, result, encoding):
        if not self.request.get('plone.app.blocks.enabled', False) or not isinstance(result, XMLSerializer):
            return None
        
        tree = panel.merge(self.request, result.tree)
        if tree is None:
            return None
        
        # Set a marker in the request to let subsequent steps know the merging has happened
        self.request['plone.app.blocks.merged'] = True
    
        result.tree = tree
        return result

class CreateTilePage(object):
    """Turn a panel-merged page into a tile page. Assumes the input result is
    an lxml tree and returns an lxml tree for later serialization.
    """
    
    implements(ITransform)
    
    order = 8500
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformString(self, result, encoding):
        return None
    
    def transformUnicode(self, result, encoding):
        return None
    
    def transformIterable(self, result, encoding):
        if not self.request.get('plone.app.blocks.enabled', False) or not isinstance(result, XMLSerializer):
            return None
        
        if not self.request.get('plone.app.blocks.merged', False):
            return None
        
        result.tree = tilepage.create_tilepage(self.request, result.tree)
        return result

class IncludeTiles(object):
    """Turn a panel-merged page into the final composition by including tiles.
    Assumes the input result is an lxml tree and returns an lxml tree for
    later serialization.
    """
    
    implements(ITransform)
    
    order = 8500
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformString(self, result, encoding):
        return None
    
    def transformUnicode(self, result, encoding):
        return None
    
    def transformIterable(self, result, encoding):
        if not self.request.get('plone.app.blocks.enabled', False) or not isinstance(result, XMLSerializer):
            return None
        
        if not self.request.get('plone.app.blocks.merged', False):
            return None
        
        result.tree = tiles.render_tiles(self.request, result.tree)
        return result
