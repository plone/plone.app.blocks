from lxml import etree, html

from plone.transformchain.interfaces import ITransform

from zope.interface import implements

from plone.app.blocks import tilepage, panel, tiles

from Globals import DevelopmentMode
PRETTY_PRINT = bool(DevelopmentMode)

class ParseXML(object):
    """First stage in the 8000's chain: parse the content to an lxml tree.
    The subsequent steps until 8999 will assume their result inputs are lxml
    trees as well.
    """
    
    implements(ITransform)
    
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

class MergePanels(object):
    """Find the site layout and merge panels.
    """
    
    implements(ITransform)
    
    order = 8100
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
        
        tree = panel.merge(self.request, result)
        if tree is None:
            return None
    
        # Set a marker in the request to let subsequent steps know the merging has happened
        self.request['plone.app.blocks.merged'] = True
    
        return tree

class CreateTilePage(object):
    """Turn a panel-merged page into a tile page. Assumes the input result is
    an lxml tree and returns an lxml tree for later serialization.
    """
    
    implements(ITransform)
    
    order = 8500
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
        
        if not self.request.get('plone.app.blocks.merged', False):
            return None
        
        return tilepage.create_tilepage(self.request, result)

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
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
        
        if not self.request.get('plone.app.blocks.merged', False):
            return None
        
        return tiles.render_tiles(self.request, result)

class SerializeXML(object):
    """Serialize an lxml tree to an encoded string.
    """
    
    implements(ITransform)
    
    order = 8999
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, result, encoding):
        if not isinstance(result, etree._ElementTree):
            return None
            
        return html.tostring(result, pretty_print=PRETTY_PRINT)
