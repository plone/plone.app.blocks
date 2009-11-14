from plone.app.blocks import utils
from lxml import etree

header_replace = [etree.XPath("/html/head/%s" % tag) for tag in ('title', 'base',)]
header_append = [etree.XPath("/html/head/%s" % tag) for tag in ('style', 'link', 'script', 'meta')]

def merge(request, page_tree):
    """Perform panel merging for the given page.
    
    Returns None if the page has no layout.
    """
    
    # Find layout node
    layout_node = utils.xpath1(utils.layout_xpath, page_tree)
    if layout_node is None:
        return None
    
    layout_href = layout_node.get('href')
    if layout_href is None:
        return None
    
    # Resolve layout tree
    layout_tree = utils.resolve(request, layout_href)
    if layout_tree is None:
        return None
    
    # Map page panels onto the layout
    
    panels = {} # name -> (layout node, page node)
    to_remove = []
    
    for panel_link_node in utils.panel_xpath(layout_tree):
        panel_id = panel_link_node.get('target')
        panel_name = panel_link_node.get('rev')
        
        if panel_id and panel_name:
            
            to_remove.append(panel_link_node)
            
            layout_panel_xpath = etree.XPath("//*[@id='%s']" % panel_id)
            layout_panel_node = utils.xpath1(layout_panel_xpath, layout_tree)
            
            page_panel_xpath = etree.XPath("//*[@id='%s']" % panel_name)
            page_panel_node = utils.xpath1(page_panel_xpath, page_tree)
            
            if layout_panel_node is not None and page_panel_node is not None:
                layout_panel_node.getparent().replace(layout_panel_node, page_panel_node)
    
    # Merge the head of both documents
    utils.mergeHead(page_tree, layout_tree, header_replace, header_append)
    
    return layout_tree