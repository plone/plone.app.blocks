# -*- coding: utf-8 -*-
from copy import deepcopy
from urlparse import urljoin

from lxml import etree
from plone.registry.interfaces import IRegistry
from zExceptions import NotFound
from zope.component import queryUtility

from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks import utils
from plone.app.blocks.utils import compile_theme
from plone.tiles.interfaces import ESI_HEADER, ESI_HEADER_KEY


def renderTiles(request, tree):
    """Find all tiles in the given response, contained in the lxml element
    tree `tree`, and insert them into the output.

    Assumes panel merging has already happened.
    """

    # Optionally enable ESI rendering in tiles that support this
    if not request.getHeader(ESI_HEADER):
        registry = queryUtility(IRegistry)
        if registry is not None:
            if registry.forInterface(IBlocksSettings).esi:
                request.environ[ESI_HEADER_KEY] = 'true'

    root = tree.getroot()
    headNode = root.find('head')
    baseURL = request.getURL()
    if request.getVirtualRoot():
        # plone.subrequest deals with VHM requests
        baseURL = ''
    for tileNode in utils.headTileXPath(tree):
        tileHref = tileNode.attrib[utils.tileAttrib]
        if not tileHref.startswith('/'):
            tileHref = urljoin(baseURL, tileHref)
        try:
            tileTree = utils.resolve(tileHref)
        except NotFound:
            continue
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            utils.replace_with_children(tileNode, tileRoot.find('head'))

    for tileNode in utils.bodyTileXPath(tree):
        tileHref = tileNode.attrib[utils.tileAttrib]
        tileRulesHref = tileNode.attrib.get(utils.tileRulesAttrib)

        if not tileHref.startswith('/'):
            tileHref = urljoin(baseURL, tileHref)
        try:
            tileTree = utils.resolve(tileHref)
        except NotFound:
            continue

        if tileRulesHref:
            if not tileRulesHref.startswith('/'):
                tileRulesHref = urljoin(baseURL, tileRulesHref)
            try:
                rules_doc = utils.resolveResource(tileRulesHref)
                rules_doc = etree.ElementTree(etree.fromstring(rules_doc))
            except NotFound:
                rules_doc = None
            del tileNode.attrib[utils.tileRulesAttrib]
        else:
            rules_doc = None

        if tileTree is not None:
            tileRoot = tileTree.getroot()

            if rules_doc is not None:
                compiled = compile_theme(
                    rules_doc, etree.ElementTree(deepcopy(tileNode)))
                transform = etree.XSLT(compiled)
                from lxml import html
                print html.tostring(tileNode)
                print html.tostring(tileRoot.find('body'))
                result = transform(tileRoot.find('body')).getroot()
                del tileRoot.find('body')[:]
                tileRoot.find('body').append(result)

            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            utils.replace_with_children(tileNode, tileRoot.find('body'))

    return tree
