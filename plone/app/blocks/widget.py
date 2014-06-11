from plone.app.widgets.dx import BaseWidget
from z3c.form.browser.text import TextWidget as z3cform_TextWidget
from plone.app.widgets.base import InputWidget
from zope.interface import implementsOnly
from z3c.form.interfaces import ITextWidget
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from plone.app.blocks.interfaces import IBlocksRegistryAdapter
try:
    import json
except:
    import simplejson as json

from plone.app.widgets.base import dict_merge
from z3c.form.util import getSpecification
from z3c.form.widget import FieldWidget
from zope.component import adapter
from zope.interface import implementer
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from plone.app.blocks.layoutbehavior import ILayoutAware




class ILayoutWidget(ITextWidget):
    """Marker interface for the LayoutWidget."""


class LayoutWidget(BaseWidget, z3cform_TextWidget):
    """Layout widget for z3c.form."""

    _base = InputWidget

    implementsOnly(ILayoutWidget)

    pattern = 'layout'
    pattern_options = BaseWidget.pattern_options.copy()

    def obtainType(self):
        """
        Obtains the type of the context object or of the object we are adding
        """
        if 'type' in self.request.form:
            return self.request.form['type']
        else:
            if hasattr(self.context, 'portal_type'):
                return self.context.portal_type
        return None

    def get_options(self):
        registry = queryUtility(IRegistry)
        adapted = IBlocksRegistryAdapter(registry)
        kwargs = {
            'type': self.obtainType(),
            'context': self.context,
            'request': self.request,
        }
        result = adapted(**kwargs)
        result['can_change_layout'] = True
        return {'data': result}

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(LayoutWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = self.value

        args.setdefault('pattern_options', {})
        args['pattern_options'] = dict_merge(
            self.get_options(),
            args['pattern_options'])

        return args


@adapter(getSpecification(ILayoutAware['content']), IFormLayer)
@implementer(IFieldWidget)
def LayoutFieldWidget(field, request):
    return FieldWidget(field, LayoutWidget(request))
