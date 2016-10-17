import logging
l = logging.getLogger(__name__)

from flask import current_app
from flask.ext.login import UserMixin, current_user

from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Unicode, Binary, DateTime, func
from sqlalchemy.orm import relationship, backref

from app import app
from app.exceptions import DatabaseValueError
from app.util import DataModelMixin

db = app.db

class Notification(db.Model, DataModelMixin):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    recipient_user = relationship(
        "User",
        backref = backref("notifications")
    )
    message_id =Column(Integer, ForeignKey("messages.id"), nullable = False)
    message = relationship(
        "Message",
        backref=backref(
            "notifications"
        )
    )
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())


class VerificationCode(db.Model, DataModelMixin):
    __tablename__ = "verification_codes"
    id = Column(Integer, primary_key = True)
    mobile_number = Column(Unicode, nullable = False, default = "")
    verification_code = Column(Unicode, nullable = False, default = "")
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())


class Device(db.Model, DataModelMixin):
    __tablename__ = "devices"
    id = Column(Integer, primary_key = True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    owner = relationship(
        "User",
        backref = backref("devices")
    )
    status =  Column(Unicode, nullable = False, default="")
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())

    def __init__(self, owner_user_id, status):
        self.owner_user_id = owner_user_id
        self.status = status


class MessageActivity(db.Model, DataModelMixin):
    __tablename__ = "message_activity"
    id = Column(Integer, primary_key = True)
    to_user_id = Column(Integer, nullable = False)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    from_user = relationship(
        "User",
        foreign_keys = [from_user_id],
        backref = backref(
            "from_user"
        )
    )

    send_date = Column(DateTime(True), nullable = False, server_default = func.now())
    location = Column(Unicode, nullable = False, default = "")
    orig_message_id = Column(Integer, ForeignKey("messages.id"), nullable = False)

    # self ref foreign key for traceability of message forwards
    parent_id = Column(Integer, ForeignKey("message_activity.id"), nullable = True)
    children = relationship("MessageActivity",
                backref=backref('parent', remote_side=[id])
            )
    off_network = Column(Boolean, nullable = False, default = False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    new_message_id = Column(Integer, ForeignKey("messages.id"), nullable = True)
    fwded_message_id = Column(Integer, ForeignKey("messages.id"), nullable = True)


class DeviceCharacteristic(db.Model, DataModelMixin):
    __tablename__ = "device_characteristics"
    id = Column(Integer, primary_key = True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable = False)
    device = relationship(
        "Device",
        backref = backref("device_characteristic")
    )
    type = Column(Unicode, nullable = False, default = "") # Android or iOS maybe?
    os = Column(Unicode, nullable = True)
    device_model = Column(Unicode, nullable = True) # Type of phone/tablet
    carrier = Column(Unicode, nullable = True)
    instance_id = Column(Unicode, nullable = True) # From InstanceID API, passed in from Android device
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())

    def __init__(self, device_id, type, os, device_model, carrier, instance_id):
        self.device_id = device_id
        self.type = type
        self.os = os
        self.device_model = device_model
        self.carrier = carrier
        self.instance_id = instance_id


class SurveyResponse(db.Model, DataModelMixin):
    __tablename__ = "survey_responses"
    id = Column(Integer, primary_key = True)
    question_text = Column(Unicode, nullable = False, default = "")
    response_text = Column(Unicode, nullable = False, default = "")
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    user = relationship(
        "User",
        backref = backref("users")
    )
