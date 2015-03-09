# -*- coding: utf-8 -*-
from plone.app.blocks.testing import BLOCKS_INTEGRATION_TESTING

import unittest


class TestTraversers(unittest.TestCase):

    layer = BLOCKS_INTEGRATION_TESTING

    def test_site_layout_traverser_registered(self):
        from plone.resource.file import FilesystemFile
        portal = self.layer['portal']

        layout = portal.restrictedTraverse(
            '++sitelayout++testlayout1/site.html')
        self.assertTrue(isinstance(layout, FilesystemFile))

    def test_site_layouts_vocabulary_and_manifest(self):
        from zope.schema.vocabulary import getVocabularyRegistry
        portal = self.layer['portal']

        vocab = getVocabularyRegistry().get(portal,
                                            'plone.availableSiteLayouts')
        vocab = list(vocab)
        vocab.sort(key=lambda t: t.token)

        self.assertEqual(len(vocab), 2)

        self.assertEqual(vocab[0].token, 'testlayout1')
        self.assertEqual(vocab[0].title, 'Testlayout1')
        self.assertEqual(vocab[0].value,
                         u'/++sitelayout++testlayout1/site.html')

        self.assertEqual(vocab[1].token, 'testlayout2')
        self.assertEqual(vocab[1].title, 'My site layout')
        self.assertEqual(vocab[1].value,
                         u'/++sitelayout++testlayout2/mylayout.html')
