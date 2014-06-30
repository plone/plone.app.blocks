# -*- coding: utf-8 -*-
from copy import deepcopy
from diazo import rules
from diazo import cssrules
from diazo import compiler
from diazo import utils as diazo_utils
from lxml import etree
from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks import utils
from plone.registry.interfaces import IRegistry
from plone.tiles.interfaces import ESI_HEADER, ESI_HEADER_KEY
from urlparse import urljoin
from zExceptions import NotFound
from zope.component import queryUtility


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
            if tileRulesHref.startswith('/'):
                tileRulesHref = urljoin(baseURL, tileRulesHref)
            try:
                rules_doc = utils.resolveResource(tileRulesHref)
                rules_doc = etree.ElementTree(etree.fromstring(rules_doc))
            except NotFound:
                rules_doc = None
        else:
            rules_doc = None

        if tileTree is not None:
            tileRoot = tileTree.getroot()
            if rules_doc is not None:
                compiled = compile_theme(
                    rules_doc, etree.ElementTree(deepcopy(tileNode)))
                transform = etree.XSLT(compiled)
                result = transform(tileRoot.find('body')).getroot()
                del tileRoot.find('body')[:]
                tileRoot.find('body').append(result)

            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            utils.replace_with_children(tileNode, tileRoot.find('body'))

    return tree


def add_theme(rules_doc, theme_doc, absolute_prefix=None):
    if absolute_prefix is None:
        absolute_prefix = ''
    root = rules_doc.getroot()
    element = root.makeelement(
        rules.fullname(rules.namespaces['diazo'], 'theme'))
    root.append(element)
    rules.expand_theme(element, theme_doc, absolute_prefix)
    return rules_doc


def process_rules(rules_doc, theme=None, trace=None, css=True,
                  absolute_prefix=None, includemode=None,
                  update=True, stop=None):
    if trace:
        trace = '1'
    else:
        trace = '0'
    if stop == 0:
        return rules_doc
    if stop == 1:
        return rules_doc
    rules_doc = rules.add_identifiers(rules_doc)
    if stop == 2 or stop == 'add_identifiers':
        return rules_doc
    if update:
        rules_doc = rules.update_namespace(rules_doc)
    if stop == 3:
        return rules_doc
    if css:
        rules_doc = cssrules.convert_css_selectors(rules_doc)
    if stop == 4:
        return rules_doc
    rules_doc = rules.fixup_theme_comment_selectors(rules_doc)
    if stop == 5:
        return rules_doc
    if theme is not None:
        rules_doc = add_theme(rules_doc, theme, absolute_prefix)
    if stop == 6:
        return rules_doc
    if includemode is None:
        includemode = 'document'
    includemode = "'%s'" % includemode
    rules_doc = rules.normalize_rules(rules_doc, includemode=includemode)
    if stop == 7:
        return rules_doc
    rules_doc = rules.apply_conditions(rules_doc)
    if stop == 8:
        return rules_doc
    rules_doc = rules.merge_conditions(rules_doc)
    if stop == 9:
        return rules_doc
    rules_doc = rules.fixup_themes(rules_doc)
    if stop == 10:
        return rules_doc
    rules_doc = rules.annotate_themes(rules_doc)
    if stop == 11:
        return rules_doc
    rules_doc = rules.annotate_rules(rules_doc)
    if stop == 12:
        return rules_doc
    rules_doc = rules.apply_rules(rules_doc, trace=trace)
    return rules_doc


def compile_theme(rules_doc, theme_doc=None, css=True,
                  absolute_prefix=None, update=True, trace=False,
                  includemode=None, parser=None, compiler_parser=None):
    rules_doc = process_rules(
        rules_doc=rules_doc,
        theme=theme_doc,
        css=css,
        absolute_prefix=absolute_prefix,
        update=update,
        trace=trace,
        includemode=includemode,
    )

    # Build a document with all the <xsl:param /> values to set the defaults
    # for every value passed in as xsl_params
    known_params = compiler.build_xsl_params_document({})

    # Create a pseudo resolver for this
    known_params_url = 'file:///__diazo_known_params__'
    emit_stylesheet_resolver = diazo_utils.CustomResolver({
        known_params_url: etree.tostring(known_params)})
    emit_stylesheet_parser = etree.XMLParser()
    emit_stylesheet_parser.resolvers.add(emit_stylesheet_resolver)

    # Run the final stage compiler
    emit_stylesheet = diazo_utils.pkg_xsl(
        'emit-stylesheet.xsl', parser=emit_stylesheet_parser)
    compiled_doc = emit_stylesheet(rules_doc)
    compiled_doc = compiler.set_parser(
        etree.tostring(compiled_doc), parser, compiler_parser)

    return compiled_doc
