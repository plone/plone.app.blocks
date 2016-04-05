# -*- coding: utf-8 -*-
# from concurrent import futures
from App.config import getConfiguration
from ZPublisher.Iterators import IStreamIterator
from ZServer.Producers import iterator_producer
from ZServer.PubCore.ZEvent import Wakeup
from plone.app.blocks import utils
from urllib import urlencode
from urlparse import parse_qs, urljoin
from urlparse import urlparse
from urlparse import urlunparse
from zope.interface import implementer
from concurrent import futures
import StringIO
import StringIO
import uuid
import logging
import mimetypes
import os
import re
import requests
import threading
import zipfile


class BigPipeChannel(object):

    def __init__(self, channel):
        self._channel = channel
        self._channel.set_terminator('0\r\n\r\n')
        self._initialized = False
        self._deferred = []
        self._finishing_producers = []

    def push(self, producer, send=1, force=False):
        if (isinstance(producer, str) and
                producer.startswith('HTTP/1')):
            producer = producer.replace(
                    'Content-Length: 0\r\n',
                    'Transfer-Encoding: chunked\r\n'
            )
            self._channel.push(producer, send)
            self._initialized = True
        else:
            self._finishing_producers.append(producer)

    def stream(self, chunk):
        length = str(hex(len(chunk)))[2:].upper()
        producer = '%s\r\n%s\r\n' % (length, chunk)
        if not self._initialized:
            self._deferred.append(producer)
        else:
            while self._deferred:
                self._channel.push(self._deferred.pop(0), 1)
            self._channel.push(producer, 1)

    def finish(self):
        while self._deferred:
            self._channel.push(self._deferred.pop(0), 1)
        self._channel.push('0\r\n\r\n')
        while self._finishing_producers:
            self._channel.push(self._finishing_producers.pop(0), 1)

    def __getattr__(self, key):
        return getattr(self._channel, key)


# noinspection PyPep8Naming
class BigPipeStreamer(object):

    def __init__(self, serializer, baseURL, channel):
        self.serializer = serializer
        self.baseURL = baseURL
        self.channel = channel

    def __call__(self):
        # TODO: VHM support, absolute URLs, headTiles
        tiles = {}
        for node in utils.bodyTileXPath(self.serializer.tree):
            href = urljoin(self.baseURL, node.attrib[utils.tileAttrib])
            node.attrib['id'] = str(uuid.uuid4())
            tiles[node.attrib['id']] = href

        layout = ''.join(self.serializer)

        self.channel.stream(layout[:layout.find('</body>')])
        for tile in tiles.values():
            self.channel.stream(tile)
        self.channel.stream(layout[layout.find('</body>'):])
        self.channel.finish()


def stream(event):
    streamer = event.request.get('plone.app.blocks.bigpipe.streamer')
    if streamer is not None:
        threading.Thread(target=streamer).start()


@implementer(IStreamIterator)
class BigPipeStreamIterator(StringIO.StringIO):
    """Dummy stream iterator to pass the request's response channel
    control to BigPipe streamer"""

    def __init__(self, request, serializer):
        # Init buffer
        StringIO.StringIO.__init__(self)

        # Wrap the Medusa channel with BigPipe Channel
        channel = BigPipeChannel(request.response.stdout._channel)
        request.response.stdout._channel = channel

        # Clear body
        request.response.body = ''

        # Set content-length as required by ZPublisher
        request.response.setHeader('content-length', '0')

        # Initialize the streamer in a separate thread
        request['plone.app.blocks.bigpipe.streamer'] = \
            BigPipeStreamer(serializer, request.getURL(), channel)

    def next(self):
        raise StopIteration

    def __len__(self):
        return 0
