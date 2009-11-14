from lxml import etree
from lxml.builder import E

from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound

from plone.app.blocks import utils, panel

XSLT_NS = "http://www.w3.org/1999/XSL/Transform"
XSLT_BOILERPLATE = """\
<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
</xsl:template>
</xsl:stylesheet>
"""

class ContentXSL(object):
    """Generate the content XSLT file by calling the context (assumed to be
    a view) and panel-merging its output.
    """
    implements(IPublishTraverse)
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.traversed = 1
    
    def publishTraverse(self, request, name):
        """Gobble up the sub-path. Used for cacheability only.
        """
        self.traversed += 1
        return self
    
    def __call__(self):
    
        # Invoke the context (a view) to get the raw page contents. Any query
        # string passed to this view is given to the context view.

        original_url = '/'.join(self.request.getURL().split('/')[:-self.traversed])
        if self.request['QUERY_STRING']:
            original_url += '?' + self.request['QUERY_STRING']
        
        tree = utils.resolve(self.request, original_url)
        if tree is None:
            raise NotFound(original_url)
        
        tree = panel.merge(self.request, tree)
        if tree is None:
            raise TypeError("Page could not be merged")
        
        # Find tiles
        tiles = utils.findTiles(self.request, tree, remove=True)
        
        # Build the stylesheet
        xslt_root = etree.fromstring(XSLT_BOILERPLATE)
        xslt_tree = xslt_root.getroottree()
        
        xslt_template = xslt_root.find("{%s}template" % XSLT_NS)
        
        # Copy the whole content HTML file into the XSLT as the template
        xslt_template.append(tree.getroot())
        
        for tile_id, tile_href in tiles.items():
            tile_target = utils.xpath1("//*[@id='%s']" % tile_id, xslt_template)
            if tile_target is None:
                continue
            
            # Replace the tile placeholder's contents with an <xsl:copy-of />
            tile_target.getparent().replace(tile_target, E("{%s}copy-of" % XSLT_NS, select="/html/body/div[@id='%s']" % tile_id))
        
        # Make sure we have the correct content type
        self.request.response.setHeader('Content-Type', 'text/xsl')
        return etree.tostring(xslt_tree)
