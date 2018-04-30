#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Chang, Ching-Hao <me@frankchang.me>
# Author: Chang, Ching-Hao <me@frankchang.me>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import socket
import select
import time
import errno
from os import dup

class SpeedtestContext(object):
    def __init__(self):
        self.stats = {
            'sent': 0,
            'recv': 0,
            'last_sent': 0,
            'last_recv': 0,
        }
        self.buf = bytearray(("speedtest" * 32 * 1024)[:128*1024], 'ascii')
        self._last_print = time.time()
        self.started = True

    def dataReceived(self, data):
        self.stats['recv'] += len(data)

    def sendAvailable(self):
        len_ = 0
        if self.started:
            try:
                len_ = self.transport.send(self.buf)
            except socket.error as e:
                self.connectionLost(e)

            self.stats['sent'] += len_ #len(self.buf)

    def connectionMade(self):
        print("{0} connected" \
              .format(":".join( str(x) for x in self.peer )))

    def connectionLost(self, reason):
        print("{0} disconnected: {1}" \
              .format(":".join( str(x) for x in self.peer ),\
                      repr(reason)))
        self.transport.close()
        self.server.unregisterSocket(self.transport)
        del self.server.contexts[self.transport]

    def printStats(self):
        t = time.time()
        sent_diff = self.stats['sent'] - self.stats['last_sent']
        recv_diff = self.stats['recv'] - self.stats['last_recv']
        self.stats['last_sent'] = self.stats['sent']
        self.stats['last_recv'] = self.stats['recv']

        print("[{2}] Tx: {0} Mbps/Rx: {1} Mbps" \
              .format(round(sent_diff/(t-self._last_print)/1000/1000*8, 2),\
                      round(recv_diff/(t-self._last_print)/1000/1000*8, 2),
                      (":".join( str(x) for x in self.peer ))))
        self._last_print = t

class SpeedtestServer(object):

    def __init__(self, host=None, port=1199):
        self.host = host
        self.port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", port))
        self._sock.listen(10)
        self.client_socks = []
        self.contexts = dict()

    def registerSocket(self, sock):
        if sock not in self.client_socks:
            self.client_socks.append(sock)

    def unregisterSocket(self, sock):
        if sock in self.client_socks:
            self.client_socks.remove(sock)

    def start(self, signature="speedtest"):
        buf = (signature * 32)[:32]
        last_print = time.time()

        while True:
            r, w, _ = select.select([self._sock]+self.client_socks, [self._sock]+self.client_socks, [], 0.1)

            for s in r:
                if s == self._sock:
                    new_s, addr = self._sock.accept()
                    context = SpeedtestContext()
                    context.transport = new_s
                    context.peer = addr
                    context.server = self
                    self.contexts.update({new_s: context})
                    self.registerSocket(new_s)
                    context.connectionMade()

                else:
                    try:
                        d = s.recv(32 * 1024)
                    except socket.error as e:
                        # Avoid further writing to the socket
                        if s in w: w.remove(s)
                        self.contexts[s].connectionLost(e)
                        continue
                        
                    if d:
                        self.contexts[s].dataReceived(d)
                    else:
                        self.contexts[s].connectionLost()
                        if s in w:
                            w.remove(s)


            for s in w:
                self.contexts[s].sendAvailable()

            t = time.time()
            if t - last_print >= 1:
                for s in self.contexts:
                    self.contexts[s].printStats()

                last_print = t

if __name__ == "__main__":
    s = SpeedtestServer(None, 9487)
    s.start()
