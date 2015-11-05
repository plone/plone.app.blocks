from Products.CMFPlone.utils import safe_unicode
from lxml.html import fromstring
from lxml.html import tostring
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.indexer.decorator import indexer
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
from zope.annotation.interfaces import IAnnotations

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


@indexer(ILayoutAware)
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
    if not behavior_data.contentLayout and behavior_data.content:
        dom = fromstring(behavior_data.content)
        for el in dom.cssselect('.mosaic-text-tile .mosaic-tile-content'):
            text.append(tostring(el))

    return concat(*text)