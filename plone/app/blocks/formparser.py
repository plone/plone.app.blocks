##############################################################################
# Pulled from zope.httpform
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""HTTP form parser that supports file uploads, Unicode, and various suffixes.

The FormParser class uses Python's standard ``cgi.FieldStorage`` class.
It converts field names and values to Unicode, handles file uploads in
a graceful manner, and allows field name suffixes that tell the parser
how to handle each field.  The standard suffixes are:

    - ``:int``      -- convert to an integer
    - ``:float``    -- convert to a float
    - ``:long``     -- convert to a long integer
    - ``:string``   -- convert to a string (useful for uploads)
    - ``:required`` -- raise ValueError if the field is not provided
    - ``:tokens``   -- split the input on whitespace characters
    - ``:lines``    -- split multiline input into a list of lines
    - ``:text``     -- normalize line endings of multiline text
    - ``:boolean``  -- true if nonempty, false if empty
    - ``:list``     -- make a list even if there is only one value
    - ``:tuple``    -- make a tuple
    - ``:action``   -- specify the form action
    - ``:method``   -- same as ``:action``
    - ``:default``  -- provide a default value
    - ``:record``   -- generate a record object
    - ``:records``  -- generate a list of record object
    - ``:ignore_empty``   -- discard the field value if it's empty
    - ``:default_action`` -- specifies a default form action
    - ``:default_method`` -- same as ``:default_action``

$Id: $
"""
__docformat__ = 'restructuredtext'

from cgi import FieldStorage
from cStringIO import StringIO
import re
from zope.interface.common.mapping import IExtendedReadMapping


newlines = re.compile('\r\n|\n\r|\r')
array_types = (list, tuple)


def field2string(v):
    if not isinstance(v, basestring):
        if hasattr(v, 'value'):
            v = v.value
        else:
            v = str(v)
    return v


def field2text(v):
    return newlines.sub("\n", field2string(v))


def field2required(v):
    test = field2string(v)
    if not test.strip():
        raise ValueError('No input for required field')
    return v


def field2int(v):
    if isinstance(v, array_types):
        return map(field2int, v)
    v = field2string(v)
    if not v:
        raise ValueError('Empty entry when integer expected')
    try:
        return int(v)
    except ValueError:
        raise ValueError("An integer was expected in the value '%s'" % v)


def field2float(v):
    if isinstance(v, array_types):
        return map(field2float, v)
    v = field2string(v)
    if not v:
        raise ValueError('Empty entry when float expected')
    try:
        return float(v)
    except ValueError:
        raise ValueError("A float was expected in the value '%s'" % v)


def field2long(v):
    if isinstance(v, array_types):
        return map(field2long, v)
    v = field2string(v)

    # handle trailing 'L' if present.
    if v and v[-1].upper() == 'L':
        v = v[:-1]
    if not v:
        raise ValueError('Empty entry when integer expected')
    try:
        return long(v)
    except ValueError:
        raise ValueError("A long integer was expected in the value '%s'" % v)


def field2tokens(v):
    return field2string(v).split()


def field2lines(v):
    if isinstance(v, array_types):
        return [field2string(item) for item in v]
    return field2text(v).splitlines()


def field2boolean(v):
    v = field2string(v)
    if v.lower() in ('1', 't', 'true'):
        return True
    return False


type_converters = {
    'float':    field2float,
    'int':      field2int,
    'long':     field2long,
    'string':   field2string,
    'required': field2required,
    'tokens':   field2tokens,
    'lines':    field2lines,
    'text':     field2text,
    'boolean':  field2boolean,
    }

get_converter = type_converters.get


def registerTypeConverter(field_type, converter, replace=False):
    """Add a custom type converter to the registry.
    If 'replace' is not true, raise a KeyError if a converter is
    already registered for 'field_type'.
    """
    existing = type_converters.get(field_type)

    if existing is not None and not replace:
        raise KeyError('Existing converter for field_type: %s' % field_type)

    type_converters[field_type] = converter

_type_format = re.compile('([a-zA-Z][a-zA-Z0-9_]+|\\.[xy])$')


# Flag Constants
SEQUENCE = 1
DEFAULT = 2
RECORD = 4
RECORDS = 8
REC = RECORD | RECORDS
CONVERTED = 32

def decode_utf8(s):
    """Decode a UTF-8 string"""
    return unicode(s, 'utf-8')


def _remove_mini_storage_wrapper(value):
    if hasattr(value, 'value'):
        value = value.value
    if type(value) == list:
        value = [_remove_mini_storage_wrapper(v)
                 for v in value]
    elif type(value) == tuple:
        value = tuple([_remove_mini_storage_wrapper(v)
                       for v in value])
    elif type(value) in (dict, Record):
        data = {}
        for name, value in value.items():
            data[name] = _remove_mini_storage_wrapper(value)
        value = data
    return value


class FormParser(object):

    def __init__(self, env, to_unicode=decode_utf8):
        """Create a form parser for the given WSGI or CGI environment.

        The wsgi_input parameter provides the request input stream.
        If wsgi_input is None (default), the parser tries to get
        the request input stream from 'wsgi.input' in the environment.

        If to_unicode is specified, it is the function to use
        to convert input byte strings to Unicode.  Otherwise, UTF-8
        encoding is assumed.
        """
        self._env = env
        self._to_unicode = to_unicode

    def parse(self):
        self.form = {}
        # If 'QUERY_STRING' is not present in self._env,
        # FieldStorage will try to get it from sys.argv[1],
        # which is not what we need.
        if 'QUERY_STRING' not in self._env:
            self._env['QUERY_STRING'] = ''

        fp = StringIO('')

        fs = TempFieldStorage(fp=fp, environ=self._env,
                              keep_blank_values=1)

        fslist = getattr(fs, 'list', None)
        if fslist is not None:
            self._tuple_items = {}
            self._defaults = {}

            # process all entries in the field storage (form)
            for item in fslist:
                self._process_item(item)

            if self._defaults:
                self._insert_defaults()

            if self._tuple_items:
                self._convert_to_tuples()

        return _remove_mini_storage_wrapper(self.form)

    def _process_item(self, item):
        """Process item in the field storage."""

        # Check whether this field is a file upload object
        # Note: A field exists for files, even if no filename was
        # passed in and no data was uploaded. Therefore we can only
        # tell by the empty filename that no upload was made.
        key = item.name
        flags = 0
        converter = None
        tuple_item = False

        # Loop through the different types and set
        # the appropriate flags
        # Syntax: var_name:type_name

        # We'll search from the back to the front.
        # We'll do the search in two steps.  First, we'll
        # do a string search, and then we'll check it with
        # a re search.

        while key:
            pos = key.rfind(":")
            if pos < 0:
                break
            match = _type_format.match(key, pos + 1)
            if match is None:
                break

            key, type_name = key[:pos], key[pos + 1:]

            # find the right type converter
            c = get_converter(type_name)

            if c is not None:
                converter = c
                flags |= CONVERTED
            elif type_name == 'list':
                flags |= SEQUENCE
            elif type_name == 'tuple':
                tuple_item = True
                flags |= SEQUENCE
            elif (type_name == 'method' or type_name == 'action'):
                if key:
                    self.action = self._to_unicode(key)
                else:
                    self.action = self._to_unicode(item)
            elif (type_name == 'default_method'
                    or type_name == 'default_action') and not self.action:
                if key:
                    self.action = self._to_unicode(key)
                else:
                    self.action = self._to_unicode(item)
            elif type_name == 'default':
                flags |= DEFAULT
            elif type_name == 'record':
                flags |= RECORD
            elif type_name == 'records':
                flags |= RECORDS
            elif type_name == 'ignore_empty':
                if not item:
                    # skip over empty fields
                    return

        # Make it unicode if not None
        if key is not None:
            key = self._to_unicode(key)

        if isinstance(item, basestring):
            item = self._to_unicode(item)

        if tuple_item:
            self._tuple_items[key] = True

        if flags:
            self._set_item_with_type(key, item, flags, converter)
        else:
            self._set_item_without_type(key, item)

    def _set_item_without_type(self, key, item):
        """Set item value without explicit type."""
        form = self.form
        if key not in form:
            form[key] = item
        else:
            found = form[key]
            if isinstance(found, list):
                found.append(item)
            else:
                form[key] = [found, item]

    def _set_item_with_type(self, key, item, flags, converter):
        """Set item value with explicit type."""
        # Split the key and its attribute
        if flags & REC:
            key, attr = self._split_key(key)

        # defer conversion
        if flags & CONVERTED:
            try:
                item = converter(item)
            except:
                if item or flags & DEFAULT or key not in self._defaults:
                    raise
                item = self._defaults[key]
                if flags & RECORD:
                    item = getattr(item, attr)
                elif flags & RECORDS:
                    item = getattr(item[-1], attr)

        # Determine which dictionary to use
        if flags & DEFAULT:
            form = self._defaults
        else:
            form = self.form

        # Insert in dictionary
        if key not in form:
            if flags & SEQUENCE:
                item = [item]
            if flags & RECORD:
                r = form[key] = Record()
                setattr(r, attr, item)
            elif flags & RECORDS:
                r = Record()
                setattr(r, attr, item)
                form[key] = [r]
            else:
                form[key] = item
        else:
            r = form[key]
            if flags & RECORD:
                if not flags & SEQUENCE:
                    setattr(r, attr, item)
                else:
                    if not hasattr(r, attr):
                        setattr(r, attr, [item])
                    else:
                        getattr(r, attr).append(item)
            elif flags & RECORDS:
                last = r[-1]
                if not hasattr(last, attr):
                    if flags & SEQUENCE:
                        item = [item]
                    setattr(last, attr, item)
                else:
                    if flags & SEQUENCE:
                        try:
                            getattr(last, attr).append(item)
                        except:
                            pass
                    else:
                        new = Record()
                        setattr(new, attr, item)
                        r.append(new)
            else:
                if isinstance(r, list):
                    r.append(item)
                else:
                    form[key] = [r, item]

    def _split_key(self, key):
        """Split the key and its attribute."""
        i = key.rfind(".")
        if i >= 0:
            return key[:i], key[i + 1:]
        return key, ""

    def _convert_to_tuples(self):
        """Convert form values to tuples."""
        form = self.form

        for key in self._tuple_items:
            if key in form:
                form[key] = tuple(form[key])
            else:
                k, attr = self._split_key(key)

                if k in form:
                    item = form[k]
                    if isinstance(item, Record):
                        if hasattr(item, attr):
                            setattr(item, attr, tuple(getattr(item, attr)))
                    else:
                        for v in item:
                            if hasattr(v, attr):
                                setattr(v, attr, tuple(getattr(v, attr)))

    def _insert_defaults(self):
        """Insert defaults into the form dictionary."""
        form = self.form

        for keys, values in self._defaults.iteritems():
            if keys not in form:
                form[keys] = values
            else:
                item = form[keys]
                if isinstance(values, Record):
                    for k, v in values.items():
                        if not hasattr(item, k):
                            setattr(item, k, v)
                elif isinstance(values, list):
                    for val in values:
                        if isinstance(val, Record):
                            for k, v in val.items():
                                for r in item:
                                    if not hasattr(r, k):
                                        setattr(r, k, v)
                        elif val not in item:
                            item.append(val)


class Record(object):
    _attrs = frozenset(IExtendedReadMapping)

    def __getattr__(self, key, default=None):
        if key in self._attrs:
            return getattr(self.__dict__, key)
        raise AttributeError(key)

    def __setattr__(self, name, value):
        if name in self._attrs or name.startswith('_'):
            raise AttributeError("Illegal record attribute name: %s" % name)
        self.__dict__[name] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __str__(self):
        items = self.__dict__.items()
        items.sort()
        return "{" + ", ".join(["%s: %s" % item for item in items]) + "}"

    def __repr__(self):
        items = self.__dict__.items()
        items.sort()
        return ("{"
            + ", ".join(["%s: %s" % (repr(key), repr(value))  # noqa
            for key, value in items]) + "}")  # noqa


class TempFieldStorage(FieldStorage):
    """FieldStorage that stores uploads in temporary files"""

    def make_file(self, binary=None):
        return StringIO()


def parse(env, to_unicode=decode_utf8):
    """Shortcut for creating a FormParser and calling the parse() method."""
    return FormParser(env, to_unicode).parse()
