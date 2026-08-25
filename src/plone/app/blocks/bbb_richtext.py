"""Marker module for the ``installed plone.app.blocks.bbb_richtext``
ZCML condition in ``configure.zcml``.

This module is importable only when the ``IJsonCompatible`` adapter for
``IRichTextValue`` (``utils.richtext_json_compatible``) has to be
registered by plone.app.blocks itself: ``plone.app.textfield`` must be
available and ``plone.restapi`` must not already ship its own converter.
plone.restapi >= 10.0.3 registers one, so registering ours as well would
break Zope startup with a ``ConfigurationConflictError``.

See https://github.com/plone/plone.app.blocks/issues/124
"""

from plone.app.textfield.interfaces import IRichTextValue  # noqa: F401
from plone.restapi.serializer import converters

if hasattr(converters, "richtextvalue_converter"):
    raise ImportError(
        "plone.restapi already registers an IJsonCompatible converter "
        "for IRichTextValue"
    )
