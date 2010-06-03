from plone.app.blocks import utils
from lxml import etree
from urlparse import urljoin

headerReplace = [etree.XPath("/html/head/%s" % tag) for tag in ('title', 'base',)]
headerAppend = [etree.XPath("/html/head/%s" % tag) for tag in ('style', 'link', 'script', 'meta')]

def merge(request, pageTree):
    """Perform panel merging for the given page.
    
    Returns None if the page has no layout.
    """
    
    # Find layout node
    layoutNode = utils.xpath1(utils.layoutXPath, pageTree)
    if layoutNode is None:
        return None
    
    layoutHref = layoutNode.get('href')
    if layoutHref is None:
        return None
    
    # Resolve layout tree
    baseURL = request.getURL()
    layoutHref = urljoin(baseURL, layoutHref) # turn the link absolute
    layoutTree = utils.resolve(request, layoutHref)
    if layoutTree is None:
        return None
    
    # Map page panels onto the layout
    
    for panelLinkNode in utils.panelXPath(layoutTree):
        panelId = panelLinkNode.get('target')
        panelName = panelLinkNode.get('rev')
        
        if panelId and panelName:
            
            layoutPanelXPath = etree.XPath("//*[@id='%s']" % panelId)
            layoutPanelNode = utils.xpath1(layoutPanelXPath, layoutTree)
            
            pagePanelXPath = etree.XPath("//*[@id='%s']" % panelName)
            pagePanelNode = utils.xpath1(pagePanelXPath, pageTree)
            
            if layoutPanelNode is not None and pagePanelNode is not None:
                layoutPanelNode.getparent().replace(layoutPanelNode, pagePanelNode)
    
    # Merge the head of both documents
    utils.mergeHead(pageTree, layoutTree, headerReplace, headerAppend)
    
    return layoutTree
