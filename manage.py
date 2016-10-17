#!../app-pyvenv/bin/python
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

import gevent.monkey
gevent.monkey.patch_all() # gunicorn is not around to do it for us.

import os
import logging
import shlex
import subprocess
import signal
import getpass

from gevent.wsgi import WSGIServer
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

from flask import current_app
from flask.ext.script import Manager, Command, prompt_bool

from app import create_app

manager = Manager(create_app())

# Example Alembic migration command
# PYTHONPATH=. alembic revision --autogenerate -m "Added user table"

l = logging.getLogger(__name__)

@manager.command
def compile():
    "compile all scss"
    os.system("cd scss; sass app.scss app.css")

@manager.command
def runserver():
    "run the server"
    from app import app # create_app has been run by now.

    def run_server():
        http_server = WSGIServer((app.config["HOST"],
                                  app.config["PORT"]), 
                                 DebuggedApplication(app))
        http_server.serve_forever()

    run_with_reloader(run_server)

@manager.command
def sass():
    "watch sass files"
    os.system("sass --watch app/scss:app/static/stylesheets")

@manager.command
def runbackend():
    "run the backend server"
    os.system("python -m backend.server")

@manager.command
def stop():
    "stop production application"
    subprocess.call(r"sudo supervisorctl -c /etc/supervisor/supervisord.conf stop app:\*", shell=True)

@manager.command
def start():    
    "start production application"
    subprocess.call(r"sudo supervisorctl -c /etc/supervisor/supervisord.conf start app:\*", shell=True)

@manager.command
def restart():    
    "restart production application"
    subprocess.call(r"sudo supervisorctl -c /etc/supervisor/supervisord.conf restart app:\*", shell=True)

@manager.command
def load():
    "load default data into database"
    from app.models.users import User, AdministratorRole, StandardRole
    from app.models.messages import Message, ReceivedMessage
    db = current_app.db
    session = db.session
    for user in (User(
                    first_name="Super",
                    last_name="Admin",
                    password="admin",
                    email_address="admin@example.com",
                    mobile_no="9706317230",
                    handle="sadmin",
                    role=AdministratorRole()
                 ),
                 User(
                    first_name="Regular",
                    last_name="User",
                    password="user",
                    email_address="user@example.com",
                    mobile_no="3037175273",
                    handle="darn_aggie",
                    role=StandardRole()
                 )):
        session.add(user)
    session.commit()    
    for msg in (Message(
                    message_text = "This is a test message",
                    sender_id = 1,
                    send_date = '02/22/2016' 
                ),
                Message(
                    message_text = "Yet another test whoop!!!",
                    sender_id = 1,
                    send_date = '02/22/2016'
                )):
        session.add(msg)
    for rcd_msg in (ReceivedMessage(
                    recipient_id = 2,
                    message_id = 1,
                    status = "unread"
                ),
                ReceivedMessage(
                    recipient_id = 2,
                    message_id = 2,
                    status = "unread"
                )):    
        session.add(rcd_msg)
    session.commit()

@manager.command
def create():
    "create all database tables from sqlalchemy models"
    db = current_app.db
    db.create_all()

@manager.command
def drop(yes=False):
    "drop all database tables"

    from sqlalchemy.sql.compiler import DDLCompiler
    def visit_drop_table(self, drop):
        return "\nDROP TABLE " + self.preparer.format_table(drop.element) + " CASCADE"
    DDLCompiler.visit_drop_table = visit_drop_table

    db = current_app.db
    if yes or prompt_bool("Are you sure you want to lose all your data"):
        db.drop_all()

@manager.command
def recreate():
    "reset the database to blank"
    drop()
    create()

@manager.command
def sql():
    "connect to db server with interactive SQL shell"
    os.system("psql application")

@manager.command
def wipe():
    username = getpass.getuser()
    for filepath in ("etc/postgres_setup.sql", "etc/postgres_test_setup.sql"):
        script = open(filepath).read()
        script = script % { "username": username }

        process = subprocess.Popen("sudo -u postgres psql", stdin=subprocess.PIPE, shell=True)
        process.communicate(script)

@manager.command
def generate_secret_key():
    open(os.path.expanduser("../var/secret_key"), "wb").write(os.urandom(24))

if __name__ == "__main__":
    manager.run()
