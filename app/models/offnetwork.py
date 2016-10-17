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

class OffNetworkMessage(db.Model, DataModelMixin):
    __tablename__ = "off_network_messages"
    id = Column(Integer, primary_key =  True)
    off_network_bucket_id = Column(Integer, ForeignKey("off_network_buckets.id"), nullable = False)
    off_network_bucket = relationship(
        "OffNetworkBucket",
        backref = backref(
            "off_network_bucket"
        )
    )
    message_id =  Column(Integer, ForeignKey("messages.id"), nullable = False)
    message = relationship(
        "Message",
        backref = backref(
            "message"
        )
    )
    forwarded = Column(Boolean, nullable = False, default = False)

    def __init__(self, off_network_bucket_id, message_id, forwarded):
        self.off_network_bucket_id = off_network_bucket_id
        self.message_id = message_id
        self.forwarded = forwarded

class OffNetworkBucket(db.Model, DataModelMixin):
    __tablename__ = "off_network_buckets"
    id = Column(Integer, primary_key = True)
    bucket_id = Column(Unicode, nullable = False, unique = True, default = "")
    bucket_type = Column(Unicode, nullable = False, default = "")

    def __init__(self, bucket_id, bucket_type):
        self.bucket_id = bucket_id
        self.bucket_type = bucket_type

class OffNetworkContact(db.Model, DataModelMixin):
    __tablename__ = "off_network_contacts"
    id = Column(Integer, primary_key = True)
#    email_address = Column(Unicode, index=True, unique=True, nullable=False)
    email_address = Column(Unicode, nullable=False)
    first_name = Column(Unicode, nullable=False, default="")
    last_name = Column(Unicode, nullable=False, default="")
    mobile_no = Column(Unicode, nullable=False, default="")
    owning_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    owning_user = relationship(
        "User",
        backref = backref(
            "owning_user"
        )
    )
    active = Column(Boolean, nullable = False, default = True)
    deleted = Column(Boolean, nullable = False, default = False)
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())

    def __init__(self, email_address, first_name, last_name, mobile_no, owning_user_id, active):
        self.email_address = email_address
        self.first_name = first_name
        self.last_name = last_name
        self.mobile_no = mobile_no
        self.owning_user_id = owning_user_id
        self.active = active

class OffNetworkGroupMember(db.Model, DataModelMixin):
    __tablename__ = "off_network_group_members"
    id = Column(Integer, primary_key = True)
    off_network_contact_id = Column(Integer, ForeignKey("off_network_contacts.id"), nullable = False)
    off_network_contact = relationship(
        "OffNetworkContact",
        backref = backref(
            "off_network_group_members"
        )
    )

    group_id = Column(Integer, ForeignKey("groups.id"), nullable = False)
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    deleted = Column(Boolean, nullable = False, default = False)
