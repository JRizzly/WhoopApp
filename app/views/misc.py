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

import logging
l = logging.getLogger(__name__)

import gevent
import random
import string
import lxml.html

from functools import wraps

from flask import render_template, redirect, url_for, request, current_app, make_response, session, abort, jsonify, send_from_directory
from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from flask.ext.sqlalchemy import models_committed

from app import app
from app.util import gen_token
from app.models.users import User
from app.exceptions import *


def setup_session(function):
    @wraps(function)
    def setup_session_decorated_view(*args, **kwargs):
        result = function(*args, **kwargs)

        # Since XSRF token has nothing to do with authentication or authorization (it only prevents
        # browser-based request forgery attacks) we go ahead and hand them out like candy. This decorator
        # should be be placed on browser URL or API endpoints that are entries into the application.
        #
        # We would do this check on any request (i.e. flask before_request) but it is not possible to
        # set a cookie during the request phase, only the response phase. It also creates interesting
        # cases where an API call will fail but will instantly work again on retry. Better to be more
        # consistent and code clients to fall back to an entry point to clean the session up.
        l.debug("setting up session")
        header_xsrf_token = request.headers.get("X-XSRF-TOKEN")
        session_xsrf_token = session.get("xsrf_token")

        if header_xsrf_token is None or session_xsrf_token is None or header_xsrf_token != session_xsrf_token:
            xsrf_token = gen_token()
            session["xsrf_token"] = xsrf_token
            session.permanent = True

            response = make_response(result)
            response.set_cookie(
                "XSRF-TOKEN",
                xsrf_token,
                max_age=current_app.config["XSRF_TOKEN_COOKIE_EXPIRATION"],
                secure=current_app.config["SESSION_COOKIE_SECURE"]
            )
            response.headers["X-XSRF-TOKEN"] = xsrf_token
            return response

        return result
    return setup_session_decorated_view


@app.after_request
def commit(response):
    if response.status_code < 400:
        try:
            app.db.session.commit()
        except Exception as e:
            l.exception("database commit failed")
            return InternalError(str(e)).get_response(request.environ)
    else:
        app.db.session.rollback()
    return response


@models_committed.connect_via(app)
def on_models_committed(sender, changes):
    for obj, change in changes:
        if change == "delete" and hasattr(obj, "__commit_delete__"):
            obj.__commit_delete__()


@app.before_request
def redirect_to_ssl():
    if current_app.config["ENFORCE_SSL"] and request.headers.get("X-Forwarded-Protocol", "http") != "https":
        if request.url.startswith("http://"):
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=302)


@app.before_request
def check_xsrf_token():
    if request.path.startswith("/api/"):
        if "application/json" != request.accept_mimetypes.best:
            raise AJAXTokenInvalidError("REST API requires application/json to be accepted.")

        header_xsrf_token = request.headers.get("X-XSRF-TOKEN")
        session_xsrf_token = session.get("xsrf_token")

        if header_xsrf_token is None or session_xsrf_token is None or header_xsrf_token != session_xsrf_token:
            l.error("POST to rpc end point without AJAX CSRF Token")
            raise AJAXTokenInvalidError("AJAX CSRF token missing.")


@app.after_request
def disable_cache(response):
    # nothing served by the app is cacheable (including template generated html)
    if hasattr(response, "cache_control"):
        response.cache_control.no_cache = True
        response.cache_control.max_age = 0
        response.cache_control.must_revalidate = True
        response.cache_control.no_store = True
        response.headers.add("Pragma", "no-cache")
        response.expires = -1
    return response


@app.login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


def authenticate(email_address, password, response=None):
    user = User.query.filter_by(email_address=email_address).first()

    if user is not None and user.check_password(password) and user.enabled:
        login_user(user)
        return True

    gevent.sleep(3.0)
    return False


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def error_handler(error):
    # If it is an API call, return JSON.
    if "application/json" == request.accept_mimetypes.best:
        if isinstance(error, AppError):
            return jsonify(error.to_json()), error.code

        # Do our best to convert this to a proper JSON response.
        if hasattr(error, "get_description"):
            description = error.get_description(request.environ)
            description = lxml.html.fromstring(description)
            description = description.text_content()
        else:
            description = str(error)

            if description == "":
                description = repr(error)

        code = error.code if hasattr(error, "code") else 500

        return jsonify({
            "description": description,
            "error_code": "UNKNOWN"
        }), code

    if hasattr(error, "code"):
        if error.code == 400:
            return render_template(
                "errors/400.html",
                message=error.description
            ), 400
        elif error.code == 403:
            return render_template(
                "errors/403.html",
                message=error.description
            ), 403
        elif error.code == 404:
            return render_template(
                "errors/404.html",
                message=error.description
            ), 404
        elif error.code == 500:
            return render_template("errors/500.html"), 500

    return render_template("errors/500.html"), 500


@app.route("/", methods=["GET"])
@login_required
def index():
    l.debug("current_user = {}".format(current_user))
    return render_template(
        "index.html",
        title="Home",
        user=current_user
    )


@app.route("/signin", methods=["GET"])
@setup_session
def signin():
    return render_template("auth/signin.html")


@app.route("/signout")
def signout():
    # Clear out the CSRF token.
    if "xsrf_token" in session:
        del session["xsrf_token"]
    response = make_response(redirect(url_for("index")))
    response.set_cookie("XSRF-TOKEN", "", expires=0, secure=current_app.config["SESSION_COOKIE_SECURE"])

    logout_user()
    return response

# This is primarily used by non-browser clients to bootstrap a session (i.e. get an XSRF token assigned).
# Normal browser clients will be handled by the setup_session decorator.
@app.route("/ping")
@setup_session
def ping():
    return "pong"

