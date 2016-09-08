# -*- coding: utf-8 -*-
from lxml.html import fromstring
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.indexer.decorator import indexer
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
from Products.CMFPlone.utils import safe_unicode
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import implementer
import pkg_resources


try:
    pkg_resources.get_distribution('collective.dexteritytextindexer')
except pkg_resources.DistributionNotFound:
    HAS_DEXTERITYTEXTINDEXER = False
else:
    from collective.dexteritytextindexer.interfaces import IDynamicTextIndexExtender  # noqa
    HAS_DEXTERITYTEXTINDEXER = True

try:
    from plone.app.contenttypes import indexers
    concat = indexers._unicode_save_string_concat
except ImportError:
    def concat(*args):
        result = ''
        for value in args:
            if isinstance(value, unicode):
                value = value.encode('utf-8', 'replace')
            if value:
                result = ' '.join((result, value))
        return result


@indexer(ILayoutBehaviorAdaptable)
def LayoutSearchableText(obj):
    text = [obj.id]
    try:
        text.append(obj.text.output)
    except AttributeError:
        pass
    try:
        text.append(safe_unicode(obj.title))
    except AttributeError:
        pass
    try:
        text.append(safe_unicode(obj.description))
    except AttributeError:
        pass

    behavior_data = ILayoutAware(obj)
    # get data from tile data
    annotations = IAnnotations(obj)
    for key in annotations.keys():
        if key.startswith(ANNOTATIONS_KEY_PREFIX):
            data = annotations[key]
            for field_name in ('title', 'label', 'content'):
                val = data.get(field_name)
                if isinstance(val, basestring):
                    text.append(val)

    try:
        if behavior_data.content:
            dom = fromstring(behavior_data.content)
            text.extend(dom.xpath('//text()'))
    except AttributeError:
        pass

    try:
        if behavior_data.customLayout:
            dom = fromstring(behavior_data.customLayout)
            text.extend(dom.xpath('//text()'))
    except AttributeError:
        pass

    return concat(*set(text))


if HAS_DEXTERITYTEXTINDEXER:

    @implementer(IDynamicTextIndexExtender)
    @adapter(ILayoutBehaviorAdaptable)
    class LayoutSearchableTextIndexExtender(object):

        def __init__(self, context):
            self.context = context

        def __call__(self):
            return LayoutSearchableText(self.context)()
