from plone.app.blocks import utils
from urlparse import urljoin


def merge(request, pageTree, removePanelLinks=False, removeLayoutLink=True):
    """Perform panel merging for the given page.

    Returns None if the page has no layout.
    """

    # Find layout node
    layoutHref = utils.xpath1(utils.layoutXPath, pageTree)
    if layoutHref is None:
        return None

    # Resolve layout tree
    baseURL = request.getURL()
    layoutHref = urljoin(baseURL, layoutHref)  # turn the link absolute
    layoutTree = utils.resolve(layoutHref)
    if layoutTree is None:
        return None

    # Map page panels onto the layout

    pagePanels = dict(
        (node.attrib['data-panel'], node)
        for node in utils.panelXPath(pageTree)
        )

    for layoutPanelNode in utils.panelXPath(layoutTree):
        panelId = layoutPanelNode.attrib['data-panel']
        pagePanelNode = pagePanels.get(panelId, None)
        if pagePanelNode is not None:
            utils.replace_content(layoutPanelNode, pagePanelNode)
        if removePanelLinks:
            del layoutPanelNode.attrib['data-panel']

    if removeLayoutLink:
        del pageTree.getroot().attrib[utils.layoutAttrib]

    return layoutTree
