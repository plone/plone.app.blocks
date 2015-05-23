from zope.interface import Interface
from zope import schema

# Keys used for request annotations and cookies
import zope.interface

USERID_KEY = 'plone.app.drafts.userId'
TARGET_KEY = 'plone.app.drafts.targetKey'
PATH_KEY = 'plone.app.drafts.path'
DRAFT_NAME_KEY = 'plone.app.drafts.draftName'
DRAFT_KEY = 'plone.app.drafts.draft'

class IDraft(Interface):
    """A draft as stored in the draft storage.
    
    This is a persistent, almost-empty object. Arbitrary data may be written
    to it as required.
    """
    
    _draftUserId = schema.TextLine(title=u"User id")
    _draftTargetKey = schema.TextLine(title=u"Target object key")
    __name__ = schema.TextLine(title=u"Unique draft name")
    
class IDraftStorage(Interface):
    """Persistent draft storage.
    
    Normally available as a local utility.
    """
    
    enabled = schema.Bool(
            title=u"Whether drafting is enabled",
            default=True,
        )
    
    drafts = schema.Dict(
            title=u"Drafts",
            description=u"Use the methods below to inspect and manipulate this",
            key_type=schema.TextLine(title=u"User id"),
            value_type=schema.Dict(
                key_type=schema.TextLine(title=u"Draft target key"),
                value_type=schema.Dict(
                    key_type=schema.TextLine(title=u"Draft name"),
                    value_type=schema.Object(schema=IDraft),
                ),
            ),
        )
    
    def createDraft(userId, targetKey, factory=None):
        """Create a new draft for the given user id and target, indicated by
        a string key (normally a string representation for an uuid, but may be
        more complex). Returns the new draft.
        
        The ``factory`` parameter can be used to pass a custom factory to
        create the draft object. It should be callable that takes two
        arguments: userId and soruceKey. The factory may set the ``__name__``
        attribute on the returned draft. This will be used, but may have a
        numeric suffix appended to ensure uniqueness.
        
        If ``factory`` is omitted, a basic, annotatable ``IDraft`` object will
        be created.
        """
    
    def discardDrafts(userId, targetKey=None):
        """Discard all drafts under the given userId and target key. If
        ``targetKey`` is not given, discard all drafts for the given user.
        """
    
    def discardDraft(draft):
        """Discard a particular draft.
        """
    
    def getDrafts(userId, targetKey):
        """Get a list mappping of all drafts under the given userId and
        target key. The returned mapping should not be modified directly.
        """
    
    def getDraft(userId, targetKey, draftName, default=None):
        """Get a particular named draft. If not found, the default is
        returned.
        """

class IDraftable(Interface):
    """Marker interface which can be applied to types that should have
    automatic drafting support.
    """

class IDrafting(Interface):
    """Marker interface which is applied to the request to indicate that
    drafting is in progress.
    """

class IDraftProxy(Interface):
    """Marker interface for the draft proxy. See ``proxy.py`` for details.
    """

class IDraftSyncer(Interface):
    """Some draft data may need to be synchronised on save. This package
    provides a helper function, ``plone.app.drafts.utils.syncDraft``, which
    can be called e.g. from an on-save event handler to copy draft data to
    the target object. This function will look up all named multi-adapters
    from the target object (e.g. a content object) and the draft to this
    interface, and call them in turn.
    """
    
    def __call__():
        """Copy data from the draft (first adapted context) to the target
        content object (second adapted context) as necessary
        """

class ICurrentDraftManagement(Interface):
    """Adapt the request to this interface to access low-level "current draft"
    management. For the most part, this is done automatically be the add/edit
    form integration (e.g. see ``archetypes.py``).
    
    Use the ``getCurrentDraft()`` function in ``utils.py`` for a simpler
    interface to get hold of (and optionally create on-demand) a draft.
    
    Use the ``IDraftStorage`` utility to access specific drafts.
    
    This interface allows the add/edit form integration to get and set the
    basic values that identify a draft: the user id, the target object key,
    and the draft name.
    
    The current draft information may be persisted across requests by calling
    ``save()``. Once saved, it can be later discard by calling ``save()``.
    
    The deafult implementation stores information in cookies that are set
    when the form is entered and cleared when it is saved or cancelled. The
    cookes are set for a path corresponding to the content object. This allows
    things like AJAX requests in the visual editor to find the same draft
    information, and minimises the risk of a draft for one object being used
    for another.
    
    The default path may be obtained via the ``defaultPath`` property, but
    an explicit path may be set. If set, it is persisted when ``save()`` is
    called. This is done to allow the draft information to be saved or
    updated with the same path as a previously created draft.
    
    The ``mark()`` method may be called to optionally mark the request with
    ``IDrafting`` if draft information (at least user id and target key) has
    been set.
    """
    
    userId = schema.TextLine(title=u"Current user id")
    targetKey = schema.TextLine(title=u"Current target key")
    draftName = schema.TextLine(title=u"Current draft name")
    path = schema.TextLine(title=u"Path prefix in which the data should be retained")
    defaultPath = schema.TextLine(title=u"Default path prefix for this request", readonly=True)
    
    draft = schema.Object(
            title=u"Current draft",
            description=u"If userId, targetKey and draftName are set, the "
                        u"draft will be lazily fetched from the storage",
            schema=IDraft,
        )
    
    def mark():
        """Mark the request with IDrafting if there is drafting information
        available.
        """
    
    def save():
        """Save the current draft information for the next request. Returns
        True if the value could be saved, False otherwise.
        
        For example, this could set a cookie.
        """
    
    def discard():
        """Discard the current draft information for the next request.
        
        For example, this could expire a cookie.
        """
