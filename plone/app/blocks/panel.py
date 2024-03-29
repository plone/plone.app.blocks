from plone.app.blocks import utils
from urllib import parse


def merge(request, pageTree, removePanelLinks=False, removeLayoutLink=True):
    """Perform panel merging for the given page.

    Returns None if the page has no layout.
    """

    # Find layout node
    layoutHref = utils.xpath1(utils.layoutXPath, pageTree)
    if layoutHref is None:
        return

    # Resolve layout tree
    baseURL = request.getURL()
    if request.getVirtualRoot():
        # plone.subrequest deals with VHM requests
        baseURL = ""
    layoutHref = parse.urljoin(baseURL, layoutHref)  # noqa: turn the link absolute
    # Pass special ajax_load parameter forward to allow layout indirection
    # views to select, for example, default AJAX layout instead of full layout.
    if request.form.get("ajax_load"):
        parts = list(parse.urlparse(layoutHref))
        query = parse.parse_qs(parts[4])
        query["ajax_load"] = request.form.get("ajax_load")
        parts[4] = parse.urlencode(query)
        layoutHref = parse.urlunparse(parts)
    layoutTree = utils.resolve(layoutHref)
    if layoutTree is None:
        return

    # Map page panels onto the layout

    pagePanels = {
        node.attrib["data-panel"]: node for node in utils.panelXPath(pageTree)
    }

    layoutPanels = {
        node.attrib["data-panel"]: (node, node.get("data-panel-mode", "append"))
        for node in utils.panelXPath(layoutTree)
    }

    # Site layout should always have element with data-panel="content"
    # Note: This could be more generic, but that would empower editors too much
    if "content" in pagePanels and "content" not in layoutPanels:
        for node in layoutTree.xpath('//*[@id="content"]'):
            node.attrib["data-panel"] = "content"
            layoutPanels["content"] = (node, "append")
            break

    for panelId, (layoutPanelNode, layoutPanelMode) in layoutPanels.items():
        pagePanelNode = pagePanels.get(panelId, None)
        if pagePanelNode is not None:
            if layoutPanelMode == "replace":
                utils.replace_with_children(layoutPanelNode, pagePanelNode)
            else:
                utils.replace_content(layoutPanelNode, pagePanelNode)
        if removePanelLinks:
            del layoutPanelNode.attrib["data-panel"]

    if removeLayoutLink:
        del pageTree.getroot().attrib[utils.layoutAttrib]

    return layoutTree
