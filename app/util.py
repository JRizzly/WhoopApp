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

import json
import smtplib
import random
import string
import datetime
import pytz
import decimal

from functools import wraps

from flask import request, abort, jsonify, session, make_response, Response, current_app

from flask.ext.classy import FlaskView
from flask.ext.login import current_user

from sqlalchemy.orm.relationships import RelationshipProperty

from app.exceptions import ValidationError, ForbiddenError, NotFoundError


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.replace(tzinfo=pytz.utc).isoformat()
        elif isinstance(obj, (datetime.timedelta)):
            return obj.total_seconds()
        elif isinstance(obj, (decimal.Decimal)):
            return str(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        else:
            return json.JSONEncoder.default(self, obj)


class DebugFormatter(logging.Formatter):
    def format(self, record):
        record.where = "{filename:s}:{lineno:d} {funcName:s}".format(**record.__dict__)
        result = logging.Formatter.format(self, record)
        return result


def setup_logging(level):
    logger = logging.getLogger()
    logger.setLevel(level)
    debug_handler = logging.StreamHandler()
    debug_handler.setFormatter(
        DebugFormatter(
            '[%(asctime)s%(msecs)03d|%(process)5d|%(levelname)7s|%(name)-30s|%(where)-35s]: %(message)s', '%d/%m/%Y %H:%M:%S.'
        )
    )
    logger.addHandler(debug_handler)
    logger.warning("started logging")    


class DataModelMixin(object):
    def _get_attributes(self, only, include, exclude):
        if only is not None:
            attributes = set(only)
        else:
            attributes = { 
                property_.key
                for property_ in self.__mapper__.attrs
                if not isinstance(property_, RelationshipProperty)
            }
            attributes |= set(include)
            attributes -= set(exclude)

        return attributes

    def _to_data(self, only=None, include=[], exclude=[], follow={}, parent=None):
        attributes = self._get_attributes(only, include, exclude)
        
        data = dict([ (attribute, getattr(self, attribute)) for attribute in attributes ])

        for relation, kwargs in list(follow.items()):
            container = getattr(self, relation)

            if container is None:
                data[relation] = None
            elif hasattr(container, "_to_data"):
                data[relation] = container._to_data(parent=self, **kwargs)
            else:
                data[relation] = []
                for item in container:
                    data[relation].append(item._to_data(parent=self, **kwargs))

        return data

    def _from_data(self, data, only=None, include=[], exclude=[]):
        attributes = self._get_attributes(only, include, exclude)

        for key, value in list(data.items()):
            if key in attributes:
                setattr(self, key, value)
                

class JSONRESTView(FlaskView):
    model = None

    max_page_limit = 1000
    page_limit = 500
    sortby = None
    sort_direction = "asc"
    sortby_map = None

    def _respond(self, data):
        json_buffer = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False, cls=JSONEncoder)
        response = make_response(json_buffer)
        response.mimetype = "application/json"
        return response

    def _process_pagination(self, query=None, request_args=None):
        if request_args is None:
            request_args = request.args

        if query is None:
            query = getattr(self.model, "query")

        try:
            limit = int(request_args.get("limit", self.page_limit))
            limit = min(limit, self.max_page_limit)
        except:
            raise ValidationError("Invalid limit")

        try:
            offset = int(request_args.get('offset', 0))
        except:
            raise ValidationError("Invalid offset")

        try:
            sortby = request_args.get("sortby", None)
            if sortby:
                sortby = str(sortby)
        except:
            raise ValidationError("Invalid sortby")

        try:
            direction = str(request_args.get("direction", self.sort_direction))
        except:
            raise ValidationError("Invalid direction")

        if direction not in ("asc", "desc"):
            raise ValidationError("Invalid direction")

        if sortby:
            query = query.order_by(getattr(getattr(self.model, sortby), direction)())
        elif query is None:
            query = self.model.query

        query = query.limit(limit).offset(offset)
        return {
            "count": query.count(),
            "limit": limit,
            "offset": offset,
            "sortby": sortby,
            "direction": direction
        }, query


def require(can_verb):
    def wrapper(function):
        @wraps(function)
        def decorated(*args, **kwargs):
            if hasattr(current_user, "role"):
                if getattr(current_user.role, can_verb)():
                    return function(*args, **kwargs)
                else:
                    raise ForbiddenError(current_user.role.can_to_error(can_verb))
            raise ForbiddenError()
        return decorated
    return wrapper


def login_required_json(function):
    @wraps(function)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            raise ForbiddenError("login required to use this API end point")
        return function(*args, **kwargs)
    return decorated_view
 

def gen_token():
    return "".join((random.choice(string.ascii_letters + string.digits) for i in range(40)))
