from plone.app.blocks import utils

def intercept(request, tree):
    """Transform the response represented by the lxml tree `tree` for the
    given request.
    
    If this returns None, the response is invalid and could not be
    transformed.
    """

    return None