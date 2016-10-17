import logging
l = logging.getLogger(__name__)

from werkzeug import generate_password_hash, check_password_hash

from flask import current_app
from flask.ext.login import UserMixin, current_user

from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Unicode, Binary, DateTime, func
from sqlalchemy.orm import relationship, backref

from app import app
from app.exceptions import DatabaseValueError
from app.util import DataModelMixin

db = app.db


class Contact(db.Model, DataModelMixin):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key = True)

    contactor_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    contactor = relationship(
        "User",
        foreign_keys = [contactor_user_id],
        backref = backref(
            "contactor"
        )
    )

    contactee_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    contactee = relationship(
        "User",
        foreign_keys = [contactee_user_id],
        backref = backref(
            "contactee"
        )
    )
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    deleted = Column(Boolean, nullable = False, default = False)

    def __init__(self, contactor_user_id, contactee_user_id):
        self.contactor_user_id = contactor_user_id
        self.contactee_user_id = contactee_user_id

class GroupMember(db.Model, DataModelMixin):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key = True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable = False)
    contact = relationship(
        "Contact",
        backref=backref(
            "contact"
        )
    )
    group_id = Column(Integer, ForeignKey("groups.id"), nullable = False)
    group = relationship(
        "Group",
        backref=backref(
            "group"
        )
    )
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    deleted = Column(Boolean, nullable = False, default = False)

class Group(db.Model, DataModelMixin):
    __tablename__ = "groups"
    id = Column(Integer, primary_key = True)
    name = Column(Unicode, nullable = False, default="")
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    owner = relationship(
        "User",
        backref = backref("owner")
    )
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    deleted = Column(Boolean, nullable = False, default = False)    

    def __init__(self, name, owner_user_id):
        self.name = name
        self.owner_user_id = owner_user_id

