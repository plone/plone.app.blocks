from UserDict import DictMixin

from zope.interface import implements
from zope.component import adapts
from zope.annotation.interfaces import IAnnotations

_marker = object()

class DraftProxy(object):
    """A simple proxy object that is initialised with a draft object and the
    underlying target. All attribute and annotation writes are performed
    against the draft; all reads are performed against the draft unless the
    specified attribute or key is not not found, in which case the they are
    read from the target object instead.
    
    Attribute deletions are saved in a set ``draft._proxyDeleted``. Annotation
    key deletions are saved in a set ``draft._proxyAnnotationsDeleted``.
    """
    
    def __init__(self, draft, target):
        self.__dict__['_DraftProxy__draft'] = draft
        self.__dict__['_DraftProxy__target'] = target
    
    def __getattr__(self, name):
        
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            raise AttributeError(name)
        
        if hasattr(self.__draft, name):
            return getattr(self.__draft, name)
        
        return getattr(self.__target, name)
    
    def __setattr__(self, name, value):
        setattr(self.__draft, name, value)
        
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            deleted.remove(name)
            self.__draft._p_changed
    
    def __delattr__(self, name):
        getattr(self, name) # allow attribute error to be raised
        
        # record deletion
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name not in deleted:
            deleted.add(name)
            setattr(self.__draft, '_proxyDeleted', deleted)
        
        # only delete on draft
        if hasattr(self.__draft, name):
            delattr(self.__draft, name)
    
class AliasAnnotations(DictMixin):
    """Layer draft annotations atop target annotations
    """
    
    implements(IAnnotations)
    adapts(DraftProxy)
   
    def __init__(self, proxy):
        self.proxy = proxy
        
        self.draft = self.proxy._DraftProxy__draft
        self.target = self.proxy._DraftProxy__target
        
        self.draftAnnotations = IAnnotations(self.draft)
        self.targetAnnotations = IAnnotations(self.target)
       
    def __nonzero__(self):
        return self.targetAnnotations.__nonzero__() or self.draftAnnotations.__nonzero__()
   
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
   
    def setdefault(self, key, default):
        value = self.get(key, _marker)
        if value is _marker:
            self[key] = value = default
            
            deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
            if key in deleted:
                deleted.remove(key)
                self.draft._proxyAnnotationsDeleted = deleted
        
        return value
   
    def __delitem__(self, key):
        self[key] # allow KeyError to be raised if we don't have this key
        
        if key in self.draftAnnotations:
            del self.draftAnnotations[key]
        
        deleted = getattr(self.draft, '_proxyAnnotationsDeleted', set())
        deleted.add(key)
        self.draft._proxyAnnotationsDeleted = deleted
