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

import os
import logging
import gevent
import datetime

from gevent.queue import Queue
from gevent.event import AsyncResult
import zmq.green as zmq

from werkzeug.contrib.fixers import ProxyFix

# Greens the postgress connector
try:
    import psycogreen.gevent
    psycogreen.gevent.patch_psycopg()
except ImportError:
    pass

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.assets import Environment

from app.util import setup_logging
from app.exceptions import TimeoutError, BackendError


app = None

# Have to use an actor pattern because we cannot allow more than one request to
# be pending at a time.
class Backend(gevent.Greenlet):
    def __init__(self):
        super(Backend, self).__init__()

        self.inbox = Queue()
        self.zmq_context = zmq.Context()
        self.zmq_socket = None
        self.init_socket()

    def init_socket(self):
        zmq_socket = self.zmq_socket
        if zmq_socket is not None:
            zmq_socket.close(0)

        zmq_socket = self.zmq_context.socket(zmq.REQ)
        zmq_socket.connect(app.config["SERVER_ZMQ_URI"])
        self.zmq_socket = zmq_socket

    def process(self, request):
        zmq_socket = self.zmq_socket

        poller = zmq.Poller()
        poller.register(zmq_socket, zmq.POLLIN)

        zmq_socket.send_json({
            "command": request["command"],
            "arguments": request["arguments"]
        })
        sockets = dict(poller.poll(10 * 1000))

        if zmq_socket not in sockets:
            self.init_socket()
            result = request["result"]
            result.set_exception(TimeoutError("The request to the backend timed out."))
            return
 
        received = zmq_socket.recv_json()

        result = request["result"]
        if received["success"]:
            result.set(received["result"])
        else:
            result.set_exception(BackendError(received["result"]))

    def _run(self):
        while True:
            self.process(self.inbox.get())            

    def send(self, command, **kwargs):
        result = AsyncResult()
        self.inbox.put({
            "command": command,
            "arguments": kwargs,
            "result": result
        })
        return result.get()


def current_year():
    return datetime.datetime.now().year


def create_app():
    global app
    global l

    mode = os.environ.get("APP_MODE")

    assert mode is not None, "APP_MODE environment variable must be set"

    app = Flask(__name__)
    app.config.from_object("config.config_flask_{}".format(mode))

    setup_logging(app.config["LOGGING_LEVEL"])
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
    # logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
    # logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)
    
    l = logging.getLogger(__name__)
    l.info("starting in mode {}".format(mode))

    app.jinja_env.globals.update(current_year=current_year)

    # Have to do this so that redirects work in proxy mode behind NGINX.
    if mode == "production":
        app.wsgi_app = ProxyFix(app.wsgi_app)

    app.db = SQLAlchemy(app)

    app.bcrypt = Bcrypt(app)
    app.assets = Environment(app)

    login_manager = LoginManager()
    login_manager.login_view = "signin"
    login_manager.login_message_category = "alert"  # Need newer release of Flask-Login for this to work.
    login_manager.init_app(app)

    from app import views
    from app import models

    app.backend = Backend()
    app.backend.start()
    
    return app
