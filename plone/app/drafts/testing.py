# -*- coding: utf-8 -*-
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.dexterity.fti import DexterityFTI
from plone.testing import z2
import pkg_resources

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True

try:
    pkg_resources.get_distribution('Products.ATContentTypes')
except pkg_resources.DistributionNotFound:
    HAS_ATCONTENTTYPES = False
else:
    HAS_ATCONTENTTYPES = True


class DraftingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if HAS_PLONE_APP_CONTENTTYPES:
            import plone.app.contenttypes
            self.loadZCML(package=plone.app.contenttypes)
        import plone.app.drafts
        self.loadZCML(package=plone.app.drafts)

    def setUpPloneSite(self, portal):
        # install plone.app.contenttypes on Plone 5
        if HAS_PLONE_APP_CONTENTTYPES:
            self.applyProfile(portal, 'plone.app.contenttypes:default')
        # install into the Plone site
        self.applyProfile(portal, 'plone.app.drafts:default')


DRAFTS_FIXTURE = DraftingLayer()
DRAFTS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(DRAFTS_FIXTURE,), name="Drafts:Integration")
DRAFTS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(DRAFTS_FIXTURE,), name="Drafts:Functional")


class ArchetypesDraftingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if HAS_PLONE_APP_CONTENTTYPES and HAS_ATCONTENTTYPES:
            import Products.ATContentTypes
            self.loadZCML(package=Products.ATContentTypes)

            z2.installProduct(app, 'Products.Archetypes')
            z2.installProduct(app, 'Products.ATContentTypes')
            z2.installProduct(app, 'plone.app.blob')
        import plone.app.drafts
        self.loadZCML(package=plone.app.drafts)
        self.loadZCML(package=plone.app.drafts, name='archetypes.zcml')

    def setUpPloneSite(self, portal):
        # install plone.app.contenttypes on Plone 5
        if HAS_PLONE_APP_CONTENTTYPES and HAS_ATCONTENTTYPES:
            self.applyProfile(portal, 'Products.ATContentTypes:default')
        # install into the Plone site
        self.applyProfile(portal, 'plone.app.drafts:default')


DRAFTS_AT_FIXTURE = ArchetypesDraftingLayer()
DRAFTS_AT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(DRAFTS_AT_FIXTURE,), name="Drafts:AT:Integration")
DRAFTS_AT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(DRAFTS_AT_FIXTURE,), name="Drafts:AT:Functional")


class DexterityDraftingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.app.dexterity
        self.loadZCML(package=plone.app.dexterity)

        import plone.app.drafts
        self.loadZCML(package=plone.app.drafts)

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'plone.app.dexterity:default')
        self.applyProfile(portal, 'plone.app.drafts:default')

        if 'Folder' not in portal.portal_types.objectIds():
            fti = DexterityFTI('Folder')
            fti.behaviors = (
                'plone.app.dexterity.behaviors.metadata.IDublinCore',
            )
            fti.klass = 'plone.dexterity.content.Container'
            fti.filter_content_types = False
            fti.global_allow = True
            portal.portal_types._setObject('Folder', fti)

        fti = DexterityFTI('MyDocument')
        fti.behaviors = (
            'plone.app.dexterity.behaviors.metadata.IDublinCore',
            'plone.app.drafts.interfaces.IDraftable'
        )
        fti.global_allow = True
        portal.portal_types._setObject('MyDocument', fti)

DRAFTS_DX_FIXTURE = DexterityDraftingLayer()
DRAFTS_DX_INTEGRDXION_TESTING = IntegrationTesting(
    bases=(DRAFTS_DX_FIXTURE,), name="Drafts:DX:Integration")
DRAFTS_DX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(DRAFTS_DX_FIXTURE,), name="Drafts:DX:Functional")
