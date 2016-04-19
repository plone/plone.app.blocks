# -*- coding: utf-8 -*-
from plone.app.blocks import utils
from urllib import urlencode
from urlparse import parse_qs
from urlparse import urljoin
from urlparse import urlparse
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

    layoutPanels = dict(
        (node.attrib['data-panel'], node)
        for node in utils.panelXPath(layoutTree)
    )

    # Site layout should always have element with data-panel="content"
    # Note: This could be more generic, but that would empower editors too much
    if 'content' in pagePanels and 'content' not in layoutPanels:
        for node in layoutTree.xpath('//*[@id="content"]'):
            node.attrib['data-panel'] = 'content'
            layoutPanels['content'] = node
            break

    for panelId, layoutPanelNode in layoutPanels.items():
        pagePanelNode = pagePanels.get(panelId, None)
        if pagePanelNode is not None:
            utils.replace_content(layoutPanelNode, pagePanelNode)
        if removePanelLinks:
            del layoutPanelNode.attrib['data-panel']

    if removeLayoutLink:
        del pageTree.getroot().attrib[utils.layoutAttrib]

    return layoutTree
