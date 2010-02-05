import re

ESI_NAMESPACE_MAP = {'esi': 'http://www.edge-delivery.org/esi/1.0'}
ESI_TEMPLATE = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <body>
        <a class="_esi_placeholder" rel="esi" href="%(url)s/@@esi-body?%(queryString)s"></a>
    </body>
</html>
"""

class ESISnippet(object):
    """Standard ESI snippet view for tiles providing IESIRendered.
    
    This renders an <a /> tag, which is then replaced using regular
    expressions later. Yes, this is lame. The HTML parser in lxml/libml2
    refuses to recognise the namespace, causing all sorts of brekaage.
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def __call__(self):
        return ESI_TEMPLATE % {
                'url': self.request.getURL(), 
                'queryString': self.request['QUERY_STRING']
            }

def substituteESILinks(rendered):
    """Turn ESI links like <a class="_esi_placeholder" rel="esi" href="..." />
    into <esi:include /> links.
    
    ``rendered`` should be an HTML string.
    """
    
    rendered = re.sub(r'<html', '<html xmlns:esi="%s"' % ESI_NAMESPACE_MAP['esi'], rendered, 1)
    return re.sub(r'<a class="_esi_placeholder" rel="esi" href="([^"]+)"></a>',
                  r'<esi:include src="\1" />', rendered)
