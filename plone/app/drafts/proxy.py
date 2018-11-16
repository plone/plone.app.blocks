# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collections import MutableMapping
from plone.app.drafts.interfaces import IDraftProxy
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import implementedBy
from zope.interface import implementer
from zope.interface import providedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor


_marker = object()


class ProxySpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the draft and the proxy target
    """

    def __get__(self, inst, cls=None):
        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)

        # Find the data we need to know if our cache needs to be invalidated
        direct_spec = getattr(inst, '__provides__', None)

        # If the draft proxy doesn't have a __provides__ attribute, get the
        # interfaces implied by the class as a starting point.
        if direct_spec is None:
            direct_spec = implementedBy(cls)

        # Get the interfaces provided by the target
        target = aq_base(inst.__dict__.get('_DraftProxy__target'))
        if target is None:
            return direct_spec
        target_spec = providedBy(target)

        # Find the cached value
        cache = inst.__dict__.get('_DraftProxy__providedBy__', None)
        updated = target._p_mtime, direct_spec, target_spec

        # See if we have a valid cache. Reasons to do this include:
        if cache is not None:
            cached_mtime, cached_direct_spec, \
                cached_target_spec, cached_spec = cache

            if cache[:-1] == updated:
                return cached_spec

        spec = direct_spec + target_spec
        inst.__dict__['_DraftProxy__providedBy__'] = updated + (spec,)

        return spec


@implementer(IDraftProxy)
class DraftProxy(object):
    """A simple proxy object that is initialised with a draft object and the
    underlying target. All attribute and annotation writes are performed
    against the draft; all reads are performed against the draft unless the
    specified attribute or key is not not found, in which case the they are
    read from the target object instead.

    Attribute deletions are saved in a set ``draft._proxyDeleted``. Annotation
    key deletions are saved in a set ``draft._proxyAnnotationsDeleted``.
    """

    __providedBy__ = ProxySpecification()

    def __init__(self, draft, target):
        self.__dict__['_DraftProxy__draft'] = draft
        self.__dict__['_DraftProxy__target'] = target
        self.__dict__['_DraftProxy__providedBy__'] = None

    def __getattr__(self, name):
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            raise AttributeError(name)

        if getattr(self.__draft, name, None):
            return getattr(self.__draft, name)

        return getattr(self.__target, name)

    def __setattr__(self, name, value):
        setattr(self.__draft, name, value)

        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            deleted.remove(name)
            self.__draft._p_changed = True

    def __delattr__(self, name):
        getattr(self, name)  # allow attribute error to be raised

        # record deletion
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name not in deleted:
            deleted.add(name)
            setattr(self.__draft, '_proxyDeleted', deleted)

        # only delete on draft
        if getattr(self.__draft, name, None):
            delattr(self.__draft, name)


@adapter(IDraftProxy)
@implementer(IAnnotations)
class AliasAnnotations(MutableMapping):
    """Layer draft annotations atop target annotations
    """

    def __init__(self, proxy):
        self.proxy = proxy

        self.draft = self.proxy._DraftProxy__draft
        self.target = self.proxy._DraftProxy__target

        self.draftAnnotations = IAnnotations(self.draft)
        self.targetAnnotations = IAnnotations(self.target)

    def __nonzero__(self):
        return self.targetAnnotations.__nonzero__() or \
            self.draftAnnotations.__nonzero__()

    def get(self, key, default=None):

        deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
        if key in deleted:
            return default

        value = self.draftAnnotations.get(key, _marker)
        if value is _marker:
            value = self.targetAnnotations.get(key, _marker)
        if value is _marker:
            return default

        return value

    def __getitem__(self, key):
        value = self.get(key, _marker)
        if value is _marker:
            raise KeyError(key)
        return value

    def keys(self):
        deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
        keys = set(self.draftAnnotations.keys())
        keys.update(self.targetAnnotations.keys())
        return tuple(keys - deleted)

    def __setitem__(self, key, value):
        self.draftAnnotations[key] = value

        deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
        if key in deleted:
            deleted.remove(key)
            self.draft._proxyAnnotationsDeleted = deleted

    def setdefault(self, key, default=None):
        value = self.get(key, _marker)
        if value is _marker:
            self[key] = value = default

            deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
            if key in deleted:
                deleted.remove(key)
                self.draft._proxyAnnotationsDeleted = deleted

        return value

    def __delitem__(self, key):
        self[key]  # allow KeyError to be raised if we don't have this key

        if key in self.draftAnnotations:
            del self.draftAnnotations[key]

        deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
        deleted.add(key)
        self.draft._proxyAnnotationsDeleted = deleted
