Introduction
============

plone.app.drafts implements services for managing auto-saved content drafts in Plone.
This addresses two problems:

* If the browser is accidentally closed or crashes whilst a page is being edited, all changes are lost.
* Some data may need to be managed asynchronously,
  e.g. via a pop-up dialogue box in the visual editor.
  This data should not be saved until the form is saved
  (and in the case of an add form, it is impossible to do so).

The former problem pertains to any content add or edit form.
The latter applies in particular to the "tiles" model as implemented by `plone.app.tiles`_ and its dependencies.

..  image:: https://secure.travis-ci.org/plone/plone.app.drafts.png
    :target: http://travis-ci.org/plone/plone.app.drafts


Installation
============

You can install plone.app.drafts as normal,
by depending on it in your ``setup.py`` or adding it to the ``eggs`` list in your buildout.
The package will self-configure for Plone; there is no need to add a ZCML slug.

You will also need to install the product from the portal_quickinstaller tool or Plone's Add-ons control panel.

Draft storage
=============

After installation,
you should notice a new tool called ``portal_drafts`` in the ZMI.
When drafts have been created, you can browse them here, and purge them if you believe they are stale.

To access the draft storage in code, look it up as a (local) utility:

    >>> from zope.component import getUtility
    >>> draftStorage = getUtility(IDraftStorage)

The draft storage contains methods for creating, finding and discarding drafts.
This is mostly useful for integration logic.

A draft is accessed by using a hierarchy of keys, all strings:

1. The user id of the user owning the draft
2. A unique "target object" key that represents the object being drafted
3. A unique draft name

The target object key is by convention a string representation of a unique integer id (via `zope.intid`_) for drafts that represent existing content objects being edited, or a string like::

    '<container-intid>:<portal_type>'

(e.g. ``'123456:Document'``) for drafts representing objects being added to a particular container.

The draft name is unique and assigned when the draft is created.

See the ``IDraftStorage`` interface for details on how to access drafts based on these keys.

The draft object itself is a minimal persistent object providing the ``IDraft`` interface.
Importantly, it is *not* a full-blown content object.
It has no intrinsic security, no workflow, and no standard fields.
It *is* however annotatable, i.e. it may be adapted to ``IAnnotations``.

A draft has a few basic attributes
(``__name__``, ``_draftUserId``, and ``_draftTargetKey``),
but is otherwise a blank canvas.
Draft data may be stored as attributes, or in annotations.
The attributes that are used depends on how the draft is integrated.
The two primary patterns are:

Autosave
  An explicit or timed background request submits the edit form to a handler,
  which extracts the form data and saves it on the draft object,
  e.g. in a ``form`` dictionary.
  The draft is updated periodically.
  On a successful save or cancel the draft is simply discarded.
  If the user returns to the edit screen after a browser crash or abandoned session,
  however, the request may be restored by copying the draft data to the real ``request.form`` dictionary prior to rendering the edit form.
  Provided the edit form is well-behaved,
  it should then show the last auto-saved values.
  These values can then be edited, before they are saved as normal.

Asynchronous updates
  An AJAX dialogue box can be used to configure an object asynchronously.
  For example, a content type that supports attachments may use such a dialogue box to upload attached files.
  These must be stored temporarily, but should not be persisted with the real content object until the underlying edit form is saved
  (and should be discarded if it is cancelled).
  The file upload handler can save the data to the drafts storage,
  and then copy it to its final location on save.

  A helper function called ``syncDraft`` is provided for this purpose in the ``plone.app.drafts.utils`` module.
  It looks up any number of named ``IDraftSyncer`` multi-adapters (on the draft object and the target content object) and calls them in turn.

Current draft management
========================

To access the current draft from code,
use the ``getCurrentDraft()`` helper function, passing it the current request:

    >>> from plone.app.drafts.utils import getCurrentDraft
    >>> currentDraft = getCurrentDraft(request)

This may return ``None`` if there is no current draft.
It is possible that the necessary information for creating a draft (user id and target key) are known,
but that no draft has been created yet.
In this case, you can request that a new draft is created on demand, by passing ``create=True``.

The current draft user id, target key and (once the draft has been created) draft name are looked up from the request, by adapting it to the interface ``ICurrentDraftManagement``.
You should not normally need to use this yourself, unless you are integrating the draft storage with an external framework.

The default ``ICurrentDraftManagement`` adapter allows the user id, target key and draft name to be set explicitly.
If they are not set, they are read from the request.
This means that they may come in request parameters, or in cookies.
The request keys are ``plone.app.drafts.targetKey`` and ``plone.app.drafts.draftName``.
The user id always defaults to the currently logged in user's id.

The ``ICurrentDraftManagement`` adapter also exposes lifecycle functions that can save or discard the current draft information.
The default implementation does this using cookies that are set for a path corresponding to the edit page.
It is the responsibility of the add/edit form integration code to ensure that this cookie is set for a path that is specific enough not to "leak" to other edit pages,
but still allows AJAX dialogue boxes and other asynchronous requests to obtain the draft information if required.

Integration
===========

Archetypes integration is provided in the ``archetypes`` module,
which is configured if Archetypes is installed.
The integration works as follows:

* An ``IEditBegunEvent`` is fired by Archetypes when the user enters an add/edit form.
  An event handler for this event will calculate a target key for the context, taking "add forms" based on the ``portal_factory`` tool into account.
  Provided a key can be calculated, it is saved via an ``ICurrentDraftManagement`` adapter as explained below.
  A draft is not created immediately, but if a single draft is discovered in the storage for this user id and key,
  that draft name is saved so that it will be returned when ``getCurrentDraft()`` is called.
  The cookie path is calculated as well and saved.
  This ensures that if the draft is created in an asynchronous request with a "deeper" URL, the cookie path will be the same.

* An event handler is installed for ``IObjectInitializedEvent`` and   ``IObjectEditedEvent``, which are fired when the user clicks *Save* on a valid  add or edit form, respectively.
  This handler will get the current draft if it has been created during the editing cycle, and uses the ``syncDraft()`` method to synchronise it as necessary.
  The draft is then discarded, as is the current draft information, causing the cookies to expire.

* An event handler is also installed for ``IEditCancelledEvent``, which is fired when the user clicks *Cancel*.
  This simply discards the draft and current draft information without synchronisation.

The draft proxy
---------------

Simple drafting integration will tend to just store data on the draft object directly.
However, it may sometimes be useful to have an object that behaves as a facade onto a "real" object, so that:

* If an attribute or annotation value that has never been set on the draft is read, the value from the underlying target object is used.

* If an attribute or annotation value is set, it is written to the draft.
  If it is subsequently read, it is read from the draft.

* If an attribute or annotation value is deleted,
  it is deleted from the draft, and the fact that it was deleted is recorded so that this may be later synchronised with the underlying object when the draft is "saved"
  (e.g. via an ``IDraftSyncer`` adapter).

To get these semantics, create a ``DraftProxy`` object like so:

    >>> from plone.app.drafts.proxy import DraftProxy
    >>> proxy = DraftProxy(draft, target)

Here, ``draft`` is an ``IDraft`` object and ``target`` is the object it is a draft of.
If attributes are deleted, they will be stored in one of two sets:

    >>> deletedAttributes = getattr(draft, '_proxyDeleted', set())
    >>> deletedAnnotations = getattr(draft, '_proxyAnnotationsDeleted', set())

Note that these attributes may not be present if nothing has ever been deleted,
so we need to fetch them defensively.

.. _plone.app.tiles: http://pypi.python.org/pypi/plone.app.tiles
.. _zope.intid: http://pypi.python.org/pypi/zope.intid
