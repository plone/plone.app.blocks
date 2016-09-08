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
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import createContent
from plone.uuid.interfaces import IMutableUUID
from plone.uuid.interfaces import IUUID
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
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
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


def isDraftable(fti):
    return any([
        IDraftable.__identifier__ in fti.behaviors,
        'plone.draftable' in fti.behaviors
    ])


class IDisplayFormDrafting(IFormLayer):
    """Marker interface for requests drafting on Dexterity display form"""


class IAddFormDrafting(IFormLayer):
    """Marker interface for requests drafting on Dexterity add form"""


class IEditFormDrafting(IFormLayer):
    """Marker interface for requests drafting on Dexterity edit form"""


@adapter(DefaultAddForm, IFormLayer, Interface)
@implementer(IWidgets)
class DefaultAddFormFieldWidgets(FieldWidgetsBase):

    def __init__(self, form, request, context):
        fti = queryUtility(IDexterityFTI, name=form.portal_type)
        if isDraftable(fti):
            current = ICurrentDraftManagement(request)

            if current.targetKey != '++add++{0}'.format(form.portal_type):
                beginDrafting(context, None)
                current.path = '/'.join(context.getPhysicalPath())
                current.targetKey = '++add++{0}'.format(form.portal_type)
                current.save()
            else:
                current.mark()

            target = getattr(current.draft, '_draftAddFormTarget', None)
            if current.draft and target:
                context = DraftProxy(current.draft, target.__of__(context))
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
        if isDraftable(fti):
            current = ICurrentDraftManagement(request)

            if current.targetKey is None:
                beginDrafting(context, None)
                current.path = '/'.join(context.getPhysicalPath())
                current.targetKey = IUUID(context)
                current.save()
            else:
                current.mark()

            if current.draft:
                context = DraftProxy(current.draft, context)
                alsoProvides(request, IEditFormDrafting)

        super(DefaultEditFormFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(IGroup, IEditFormDrafting, Interface)
@implementer(IWidgets)
class DefaultEditFormGroupFieldWidgets(FieldWidgetsBase):

    def __init__(self, form, request, context):
        draft = getCurrentDraft(request)
        context = DraftProxy(draft, context)
        super(DefaultEditFormGroupFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(WidgetsView, IDisplayFormDrafting, IDexterityContent)
@implementer(IWidgets)
class DefaultDisplayFormFieldWidgets(FieldWidgetsBase):

    def __init__(self, form, request, context):
        fti = queryUtility(IDexterityFTI, name=context.portal_type)
        if isDraftable(fti):
            current = ICurrentDraftManagement(request)

            if current.targetKey is not None:
                current.mark()

            if current.draft:
                context = DraftProxy(current.draft, context)

        super(DefaultDisplayFormFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(IGroup, IDisplayFormDrafting, Interface)
@implementer(IWidgets)
class DefaultDisplayFormGroupFieldWidgets(FieldWidgetsBase):

    def __init__(self, form, request, context):
        draft = getCurrentDraft(request)
        context = DraftProxy(draft, context)
        super(DefaultDisplayFormGroupFieldWidgets, self).__init__(form, request, context)  # noqa


def autosave(event):  # noqa
    context = getattr(event, 'object', None)
    request = getattr(context, 'REQUEST', getRequest())
    if not request.URL.endswith('/@@z3cform_validate_field'):
        return

    view = getattr(request, 'PUBLISHED', None)
    form = getattr(view, 'context', None)
    if getattr(aq_base(form), 'form_instance', None):
        form = form.form_instance

    if IAddForm.providedBy(form):
        fti = queryUtility(IDexterityFTI, name=form.portal_type)
        if not isDraftable(fti):
            return

        draft = getCurrentDraft(request, create=True)
        target = getattr(draft, '_draftAddFormTarget', None)

        if target is None:
            target = createContent(form.portal_type)
            target.id = ''
            IMutableUUID(target).set('++add++{0}'.format(form.portal_type))
            draft._draftAddFormTarget = target
        target = target.__of__(context)

    else:
        fti = queryUtility(IDexterityFTI, name=context.portal_type)
        if not isDraftable(fti):
            return

        draft = getCurrentDraft(request, create=True)
        target = context

    fti = queryUtility(IDexterityFTI, name=target.portal_type)
    if not isDraftable(fti):
        return

    if not getattr(form, 'extractData', None):
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
    target = getattr(draft, '_draftAddFormTarget', None)
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
        target = getattr(draft, '_draftAddFormTarget', None)
        if target:
            syncDraftOnSave(target, event)
        else:
            discardDraftsOnCancel(event.action.form.context, event)
    else:
        syncDraftOnSave(event.action.form.context, event)
