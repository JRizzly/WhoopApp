# Copyright (c) 2014 Data Bakery LLC. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, this list of
# conditions and the following disclaimer.
# 
#     2. Redistributions in binary form must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other materials provided with
# the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY DATA BAKERY LLC ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DATA BAKERY LLC OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from gevent import monkey
monkey.patch_all()

import logging
l = logging.getLogger(__name__)

import os
import signal
import argparse
import traceback
import gevent

from gevent.backdoor import BackdoorServer
from functools import wraps, partial

import zmq.green as zmq

from app import create_app

from flask import current_app

commands = {}
daemons = []
initializers = []

def command(func):
    commands[func.__name__] = func
    return func


def daemon(func):
    daemons.append(func)
    return func


def initializer(func):
    initializers.append(func)
    return func

def server():
    l.debug("backend server starting")

    for initializer in initializers:
        initializer()
 
    greenlets = set()
    for daemon in daemons:
        l.debug("spawning {!r}".format(daemon))
 
        # VERY TRICKY STUFF HERE. Must use partials to bind parameters to funcs
        # in this loop or the loop variables won't be the correct ones when these
        # functions get called - even the function names themselves for the recursion.
        def daemon_exception(daemon_starter, greenlet):
            greenlets.remove(greenlet)
            l.debug("daemon {} failed - restarting in a few seconds".format(greenlet))
 
            gevent.sleep(5) # just in case we get into some weird loop
            daemon_starter()
 
        def daemon_starter(daemon):
            greenlet = gevent.spawn(daemon)
            greenlet.link_exception(partial(daemon_exception, partial(daemon_starter, daemon)))
            greenlets.add(greenlet)
 
        daemon_starter(daemon)
 
    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    server_socket.bind(current_app.config["SERVER_ZMQ_URI"])

    while True:
        message = server_socket.recv_json()
        l.debug("received message: {}".format(message))

        try:
            result = commands.get(message["command"])(**message["arguments"])
        except Exception as e:
            server_socket.send_json({
                "success": False,
                "result": str(e)
            })
            traceback.print_exc()
        else:            
            server_socket.send_json({
                "success": True,
                "result": result
            })


def main():
    global context
    global app

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", 
        "--pid-file",
        help="location to write process ID",
        required=False
    )
    args = parser.parse_args()

    if args.pid_file is not None:
        with open(args.pid_file, "w") as pid_file:
            pid_file.write(str(os.getpid()) + "\n")

    app = create_app()

    #from . import emergency # we do this late so app is available for import

    with app.app_context():
        try:
            backdoor = BackdoorServer(('127.0.0.1', app.config["BACKEND_BACKDOOR_SERVER_PORT"]), locals=locals())
            backdoor.start()

            server()
        except KeyboardInterrupt as e:
            l.debug("shutting down")

if __name__ == '__main__':
    main()