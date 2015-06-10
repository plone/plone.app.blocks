# -*- coding: utf-8 -*-
from plone.app.blocks import utils
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements

import json


class IGridSystem(Interface):
    """ Utility to get the grid System
    """


class BS3GridSystem(object):
    implements(IGridSystem)

    def __init__(self):
        self.offset = 1

    def transform(self, key):
        """ its possible:
            {type: row} -> row
            {type: cell, info: {xs:False, sm:False, md:True, lg:true, pos:{x:1 width:10}}} ->
                hidden-xs hidden-sm col-md-10
        """
        element = json.loads(key)
        if 'type' in element and element['type'] == 'row':
            self.offset = 1
            return 'row'
        elif 'type' in element and element['type'] == 'cell':
            result = ''
            if 'info' in element:
                if 'xs' in element['info'] and element['info']['xs'].lower() == "false":
                    result += 'hidden-xs '
                if 'sm' in element['info'] and element['info']['sm'].lower() == "false":
                    result += 'hidden-sm '
                if 'md' in element['info'] and element['info']['md'].lower() == "false":
                    result += 'hidden-md '
                if 'lg' in element['info'] and element['info']['lg'].lower() == "false":
                    result += 'hidden-lg '
                if 'pos' in element['info']:
                    if element['info']['pos']['x'] > self.offset:
                        result += 'col-md-offset-%d ' % (element['info']['pos']['x'] - (self.offset - 1))
                    if 'width' in element['info']['pos']:
                        self.offset += element['info']['pos']['width']
                        result += 'col-md-%d' % element['info']['pos']['width']
            return result


class DecoGridSystem(object):
    implements(IGridSystem)

    def transform(self, key):
        """ its possible:
            {type: row} -> row
            {type: cell, info: {xs:False, sm:False, md:True, lg:true, pos:{x:1 width:10}}} ->
            cell position-1 width-10
        """
        element = json.loads(key)
        if 'type' in element and element['type'] == 'row':
            return 'row'
        elif 'type' in element and element['type'] == 'cell':
            result = 'cell '
            if 'info' in element:
                if 'pos' in element['info']:
                    if 'x' in element['info']['pos']:
                        deco_pos = int(element['info']['pos']['x']) - 1
                        result += 'position-%d ' % deco_pos
                    if 'width' in element['info']['pos']:
                        result += 'width-%d' % element['info']['pos']['width']
            return result


def merge(request, layoutTree):
    """Perform grid system merging for the given page.

    Returns None if the page has no layout.
    """

    # Find layout node
    gridSystem = utils.xpath1(utils.gridXPath, layoutTree)
    if gridSystem is None:
        gridSystem = 'deco'

    gridUtil = getUtility(IGridSystem, gridSystem)()
    for layoutGridNode in utils.gridDataXPath(layoutTree):
        gridinfo = layoutGridNode.attrib['data-grid']
        cssGridClass = gridUtil.transform(gridinfo)
        if cssGridClass is not None:
            if 'class' in layoutGridNode.attrib:
                layoutGridNode.attrib['class'] = layoutGridNode.attrib['class'] + ' ' + cssGridClass  # noqa
            else:
                layoutGridNode.attrib['class'] = cssGridClass
        del layoutGridNode.attrib['data-grid']
    return layoutTree
