# -*- coding: utf-8 -*-
from Acquisition import aq_base

from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IAddBegunEvent
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import createContent
from plone.uuid.interfaces import IMutableUUID
from z3c.form.field import FieldWidgets as FieldWidgetsBase
from z3c.form.form import applyChanges
from z3c.form.group import Group
from z3c.form.interfaces import IWidgets, IAddForm
from z3c.form.interfaces import IActionEvent
from z3c.form.interfaces import IFormLayer
from zope.component import queryUtility
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.lifecycleevent import IObjectAddedEvent

from plone.app.drafts.interfaces import IDraftable
from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.interfaces import ICurrentDraftManagement
from plone.app.drafts.lifecycle import beginDrafting
from plone.app.drafts.lifecycle import discardDraftsOnCancel
from plone.app.drafts.lifecycle import syncDraftOnSave
from plone.app.drafts.proxy import DraftProxy
from plone.app.drafts.utils import getCurrentDraft


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


@adapter(Group, IAddFormDrafting, Interface)
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
            else:
                current = ICurrentDraftManagement(request)
                current.mark()

            context = DraftProxy(draft, context)
            alsoProvides(request, IEditFormDrafting)

        super(DefaultEditFormFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(Group, IAddFormDrafting, Interface)
@implementer(IWidgets)
class DefaultEditFormGroupFieldWidgets(FieldWidgetsBase):
    def __init__(self, form, request, context):
        draft = getCurrentDraft(request)
        context = DraftProxy(draft, context)
        super(DefaultEditFormGroupFieldWidgets, self).__init__(form, request, context)  # noqa


@adapter(IAddBegunEvent)
def autosave(event):
    context = getattr(event, 'object', None)
    request = getattr(context, 'REQUEST', getRequest())
    if not request.URL.endswith('/@@z3cform_validate_field'):
        return

    draft = getCurrentDraft(request)
    if draft is None:
        return

    target = getattr(draft, '_draftAddFormTarget', None)
    if not target:
        return

    view = getattr(request, 'PUBLISHED', None)
    form = getattr(view, 'context', None)
    if hasattr(aq_base(form), 'form_instance'):
        form = form.form_instance

    fti = queryUtility(IDexterityFTI, name=target.portal_type)
    if IDraftable.__identifier__ not in fti.behaviors:
        return

    if not hasattr(form, "extractData"):
        return

    data, errors = form.extractData()
    if not errors:
        content = DraftProxy(draft, target.__of__(context))
        applyChanges(form, content, data)
        for group in getattr(form, 'groups', []):
            applyChanges(group, content, data)


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

    if IAddForm.providedBy(event.action.form):
        draft = getCurrentDraft(event.action.form.request)
        target = getattr(draft, '_draftAddFormTarget')
        if target:
            syncDraftOnSave(target, event)
    else:
        syncDraftOnSave(event.action.form.context, event)
