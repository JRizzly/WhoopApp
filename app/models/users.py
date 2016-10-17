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

from werkzeug import generate_password_hash, check_password_hash

from flask import current_app
from flask.ext.login import UserMixin, current_user

from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Unicode, Binary
from sqlalchemy.orm import relationship, backref

from app import app
from app.exceptions import DatabaseValueError
from app.util import DataModelMixin

db = app.db

ROLE_ADMINISTRATOR = "administrator"
ROLE_STANDARD = "standard"

enabled = lambda *args, **kwargs: True
disabled = lambda *args, **kwargs: False


class Role(db.Model, DataModelMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(
        "User",
        backref=backref(
            "role", 
            cascade="all, delete-orphan",
            single_parent=True,
            uselist=False
        )
    )

    type = Column(
        Enum(
            ROLE_ADMINISTRATOR,
            ROLE_STANDARD,
            name="role_type"
        ),
        nullable=False
    )

    __mapper_args__ = {
        "polymorphic_identity": "role",
        "polymorphic_on": type
    }

    def can_to_error(self, can):
        return "Permission denied: {}".format(can)

    def __getattr__(self, name):
        if name.startswith("can_"):
            return disabled

        return getattr(super(Role, self), name)


class AdministratorRole(Role):
    __tablename__ = "administrator_roles"

    id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": ROLE_ADMINISTRATOR
    }

    def __init__(self, *args, **kwargs):
        super(AdministratorRole, self).__init__(*args, **kwargs)
        self.type = ROLE_ADMINISTRATOR

    def __getattr__(self, name):
        if name.startswith("can_"):
            return enabled

        return super(AdministratorRole, self).__getattr__(name)


class StandardRole(Role):
    __tablename__ = "standard_roles"

    id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": ROLE_STANDARD
    }

    def __init__(self, *args, **kwargs):
        super(StandardRole, self).__init__(*args, **kwargs)
        self.type = ROLE_STANDARD

    def __getattr__(self, name):
        if name.startswith("can_"):
            return lambda: False

        return super(StandardRole, self).__getattr__(name)


class User(db.Model, UserMixin, DataModelMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email_address = Column(Unicode, index=True, unique=True, nullable=False)
    first_name = Column(Unicode, nullable=False, default="")
    last_name = Column(Unicode, nullable=False, default="")
    _password = Column("password", Binary, nullable=False)
    mobile_no = Column(Unicode, nullable=False, default="")
    handle = Column(Unicode, unique=True, nullable=False, default="")
    enabled = Column(Boolean, nullable=False, default=True)
    
    @property
    def name(self):
        return (self.first_name + " " + self.last_name).strip()

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        if password is not None:
            self._password = app.bcrypt.generate_password_hash(password)
        else:
            l.debug("password is none - not changing")

        l.debug("password set to = {}".format(self._password))

    # Hide password encryption by exposing password field only.
    password = db.synonym("_password",
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        return app.bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return "<User {}>".format(self.email_address)

class BlockedUser(db.Model, UserMixin, DataModelMixin):
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key = True)
    blocking_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    blocking_user = relationship(
        "User", 
        foreign_keys = [blocking_user_id],
        backref = backref(
            "blocking_users"
        )
    )
    blocked_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    blocked_user = relationship(
        "User", 
        foreign_keys = [blocked_user_id],
        backref = backref(
            "blocked_users"
        )
    )
