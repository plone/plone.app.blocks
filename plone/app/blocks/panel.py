# -*- coding: utf-8 -*-
from urllib import urlencode
from plone.app.blocks import utils
from urlparse import urljoin
from urlparse import urlparse
from urlparse import parse_qs
from urlparse import urlunparse


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
    if request.getVirtualRoot():
        # plone.subrequest deals with VHM requests
        baseURL = ''
    layoutHref = urljoin(baseURL, layoutHref)  # turn the link absolute
    if request.form.get('ajax_load'):
        parts = list(urlparse(layoutHref))
        query = parse_qs(parts[4])
        query['ajax_load'] = request.form.get('ajax_load')
        parts[4] = urlencode(query)
        layoutHref = urlunparse(parts)
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
