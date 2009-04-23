from zope.interface import Interface

class ITilePageRendered(Interface):
    """This marker interface can be applied to views that should use separate
    tile page/content.xsl rendering.
    """
