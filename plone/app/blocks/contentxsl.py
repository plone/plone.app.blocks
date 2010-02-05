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

        originalURL = '/'.join(self.request.getURL().split('/')[:-self.traversed])
        if self.request['QUERY_STRING']:
            originalURL += '?' + self.request['QUERY_STRING']
        
        tree = utils.resolve(self.request, originalURL)
        if tree is None:
            raise NotFound(originalURL)
        
        tree = panel.merge(self.request, tree)
        if tree is None:
            raise TypeError("Page could not be merged")
        
        # Find tiles
        tiles = utils.findTiles(self.request, tree, remove=True)
        
        # Build the stylesheet
        xsltRoot = etree.fromstring(XSLT_BOILERPLATE)
        xsltTree = xsltRoot.getroottree()
        
        xsltTemplate = xsltRoot.find("{%s}template" % XSLT_NS)
        
        # Copy the whole content HTML file into the XSLT as the template
        xsltTemplate.append(tree.getroot())
        
        for tileId, tileHref in tiles.items():
            tileTarget = utils.xpath1("//*[@id='%s']" % tileId, xsltTemplate)
            if tileTarget is None:
                continue
            
            # Replace the tile placeholder's contents with an <xsl:copy-of />
            tileTarget.getparent().replace(tileTarget, E("{%s}copy-of" % XSLT_NS, select="/html/body/div[@id='%s']" % tileId))
        
        # Make sure we have the correct content type
        self.request.response.setHeader('Content-Type', 'text/xsl')
        return etree.tostring(xsltTree)
