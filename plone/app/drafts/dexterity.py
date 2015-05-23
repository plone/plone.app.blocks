# -*- coding: utf-8 -*-
from Acquisition import aq_base
from plone.app.drafts.interfaces import ICurrentDraftManagement
from plone.app.drafts.interfaces import IDraftable
from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.lifecycle import beginDrafting
from plone.app.drafts.lifecycle import discardDraftsOnCancel
from plone.app.drafts.lifecycle import syncDraftOnSave
from plone.app.drafts.proxy import DraftProxy
from plone.app.drafts.utils import getCurrentDraft
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import createContent
from plone.uuid.interfaces import IMutableUUID
from z3c.form.field import FieldWidgets as FieldWidgetsBase
from z3c.form.form import applyChanges
from z3c.form.interfaces import IActionEvent
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IGroup
from z3c.form.interfaces import IWidgets
from zope.component import adapter
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.lifecycleevent import IObjectAddedEvent
import transaction

try:
    from plone.protect.interfaces import IDisableCSRFProtection
    HAS_PLONE_PROTECT = True
except ImportError:
    HAS_PLONE_PROTECT = False


AUTOSAVE_BLACKLIST = [
    'IShortName.id'
]


class IAddFormDrafting(IFormLayer):
    """Marker interface for requests drafting on Dexterity add form"""


class IEditFormDrafting(IFormLayer):
    """Marker interface for requests drafting on Dexterity edit form"""


@adapter(DefaultAddForm, IFormLayer, Interface)
@implementer(IWidgets)
class DefaultAddFormFieldWidgets(FieldWidgetsBase):
    def __init__(self, form, request, context):
        fti = queryUtility(IDexterityFTI, name=form.portal_type)
        if IDraftable.__identifier__ in fti.behaviors:
            draft = getCurrentDraft(request, create=False)
            target = getattr(draft, '_draftAddFormTarget',
                             createContent(form.portal_type))

            if draft is None:
                IMutableUUID(target).set('++add++%s' % form.portal_type)
                beginDrafting(target.__of__(context), None)
                draft = getCurrentDraft(request, create=True)
                draft._draftAddFormTarget = target

                # Disable Plone 5 implicit CSRF when no form action
                if HAS_PLONE_PROTECT:
                    if not ([key for key in request.form
                             if key.startswith('form.buttons.')]):
                        alsoProvides(request, IDisableCSRFProtection)
            else:
                current = ICurrentDraftManagement(request)
                current.mark()

            context = DraftProxy(draft, target.__of__(context))
            alsoProvides(request, IAddFormDrafting)

        super(DefaultAddFormFieldWidgets, self).__init__(form, request, context)  # noqa

    def update(self):
        if IAddFormDrafting.providedBy(self.request):
            self.ignoreContext = False
        super(DefaultAddFormFieldWidgets, self).update()


@adapter(IGroup, IAddFormDrafting, Interface)
@implementer(IWidgets)
class DefaultAddFormGroupFieldWidgets(FieldWidgetsBase):
    def __init__(self, form, request, context):
        draft = getCurrentDraft(request)
        target = getattr(draft, '_draftAddFormTarget')
        context = DraftProxy(draft, target.__of__(context))
        super(DefaultAddFormGroupFieldWidgets, self).__init__(form, request, context)  # noqa

    def update(self):
        self.ignoreContext = False
        super(DefaultAddFormGroupFieldWidgets, self).update()


@adapter(DefaultEditForm, IFormLayer, IDexterityContent)
@implementer(IWidgets)
class DefaultEditFormFieldWidgets(FieldWidgetsBase):
    def __init__(self, form, request, context):
        fti = queryUtility(IDexterityFTI, name=form.portal_type)
        if IDraftable.__identifier__ in fti.behaviors:
            draft = getCurrentDraft(request, create=False)

            if draft is None:
                beginDrafting(context, None)
                draft = getCurrentDraft(request, create=True)

                # Disable Plone 5 implicit CSRF when no form action
                if HAS_PLONE_PROTECT:
                    if not ([key for key in request.form
                             if key.startswith('form.buttons.')]):
                        alsoProvides(request, IDisableCSRFProtection)
            else:
                current = ICurrentDraftManagement(request)
                current.mark()

            context = DraftProxy(draft, context)
            alsoProvides(request, IEditFormDrafting)

        super(DefaultEditFormFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(IGroup, IEditFormDrafting, Interface)
@implementer(IWidgets)
class DefaultEditFormGroupFieldWidgets(FieldWidgetsBase):
    def __init__(self, form, request, context):
        draft = getCurrentDraft(request)
        context = DraftProxy(draft, context)
        super(DefaultEditFormGroupFieldWidgets, self).__init__(form, request, context)  # noqa


def autosave(event):
    context = getattr(event, 'object', None)
    request = getattr(context, 'REQUEST', getRequest())
    if not request.URL.endswith('/@@z3cform_validate_field'):
        return

    draft = getCurrentDraft(request)
    if draft is None:
        return

    view = getattr(request, 'PUBLISHED', None)
    form = getattr(view, 'context', None)
    if hasattr(aq_base(form), 'form_instance'):
        form = form.form_instance

    if IAddForm.providedBy(form):
        target = getattr(draft, '_draftAddFormTarget', None)
        if not target:
            return
        target = target.__of__(context)
    else:
        target = context

    fti = queryUtility(IDexterityFTI, name=target.portal_type)
    if IDraftable.__identifier__ not in fti.behaviors:
        return

    if not hasattr(form, "extractData"):
        return

    data, errors = form.extractData()
    if not errors:
        content = DraftProxy(draft, target)

        # Drop known non-draftable values
        map(data.pop, [key for key in AUTOSAVE_BLACKLIST if key in data])

        # Values are applied within savepoint to allow revert of any
        # unexpected side-effects from setting field values
        sp = transaction.savepoint(optimistic=True)
        try:
            applyChanges(form, content, data)
            for group in getattr(form, 'groups', []):
                applyChanges(group, content, data)
        except Exception:
            # If shortname was not blacklisted, it could fail because the
            # behavior trying to rename object on add form.
            pass
        values = dict(draft.__dict__)
        sp.rollback()

        for key, value in values.items():
            setattr(draft, key, value)

        # Disable Plone 5 implicit CSRF to update draft
        if HAS_PLONE_PROTECT:
            alsoProvides(request, IDisableCSRFProtection)


@adapter(IDexterityContent, IObjectAddedEvent)
def capture(ob, event):
    request = getattr(ob, 'REQUEST', getRequest())
    if not IAddFormDrafting.providedBy(request):
        return

    draft = getCurrentDraft(request)
    target = getattr(draft, '_draftAddFormTarget')
    if draft and target and target.portal_type == target.portal_type:
        draft._draftAddFormTarget = ob


@adapter(IActionEvent)
def cancel(event):
    if not IDrafting.providedBy(event.action.request):
        return

    if event.action.name != 'form.buttons.cancel':
        return

    discardDraftsOnCancel(event.action.form.context, event)


@adapter(IActionEvent)
def save(event):
    if not IDrafting.providedBy(event.action.request):
        return

    if event.action.name != 'form.buttons.save':
        return

    data, errors = event.action.form.extractData()
    if errors:
        return

    if IAddForm.providedBy(event.action.form):
        draft = getCurrentDraft(event.action.form.request)
        target = getattr(draft, '_draftAddFormTarget')
        if target:
            syncDraftOnSave(target, event)
    else:
        syncDraftOnSave(event.action.form.context, event)
