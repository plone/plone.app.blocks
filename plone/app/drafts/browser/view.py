from datetime import datetime
from plone.app.uuid.utils import uuidToObject
from urllib import quote


class View(object):
    """A shared view class that is used for each of the three views. They
    each use a different template.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):

        form = self.request.form

        # @@overview view
        if 'form.button.PruneUsers' in form:
            userIds = form.get('userIds', [])
            for userId in userIds:
                if userId in self.context.drafts:
                    self.context.discardDrafts(userId)

        # @@targets view
        if 'form.button.PruneTargets' in form:
            userId = form.get('userId', None)
            targetKeys = form.get('targetKeys', [])

            targets = self.context.drafts.get(userId, {})
            for targetKey in targetKeys:
                if targetKey in targets:
                    self.context.discardDrafts(userId, targetKey)

        # @@drafts view
        if 'form.button.PruneDrafts' in form:
            userId = form.get('userId', None)
            targetKey = form.get('targetKey', None)
            draftNames = form.get('draftNames', [])

            drafts = self.context.drafts.get(userId, {}).get(targetKey, {})
            for draftName in draftNames:
                draft = drafts.get(draftName, None)
                if draft is not None:
                    self.context.discardDraft(draft)

        return self.index()

    def targetInfo(self, targetKey):

        child = False
        url = None
        title = targetKey
        portal_type = None
        uuid = None

        if ':' in targetKey:
            uid, portal_type = targetKey.split(':', 1)
            child = True
        else:
            uuid = targetKey

        target = uuidToObject(uuid)
        if target is not None:
            url = target.absolute_url()
            title = target.title
            portal_type = target.portal_type

        return {'title': title, 'url': url,
                'child': child, 'portal_type': portal_type}

    def quote(self, key):
        return quote(key)

    def draftInfo(self, draft):
        p_mtime = getattr(draft, '_p_mtime', None)
        if p_mtime is None:
            mtime = None
        else:
            mtime = datetime.fromtimestamp(p_mtime)
        return {'mtime': mtime}
