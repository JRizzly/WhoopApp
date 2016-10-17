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



class Message(db.Model, DataModelMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    sender = relationship(
        "User",
        backref=backref(
            "message"        )
    )


    message_text = Column(String, nullable=False)
    send_date = Column(DateTime(True), nullable = False, server_default = func.now())
    #TODO We may want to normalize this out to store x,y, gps type, gps quality
    #TODO For now we'll store "x,y" as JSON string and adjust later as needed.
    sender_location = Column(String, nullable = True)
    sender_location_type = Column(String, nullable = True)

    message_config_id = Column(Integer, ForeignKey("message_configs.id"), nullable = True)
    message_config = relationship(
        "MessageConfig",
        backref=backref(
            "message"
        )
    )

    message_forwarded = Column(Boolean, nullable = True, default = False)
    deleted = Column(Boolean, nullable = True, default = False)
    creator_id = Column(Integer, nullable = True)
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    
class ReceivedMessage(db.Model, DataModelMixin):
    __tablename__ = "received_messages"

    id = Column(Integer, primary_key = True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    recipient = relationship(
        "User",
        backref=backref(
            "received_message"
        )
    )
    message_id = Column(Integer, ForeignKey("messages.id"), nullable = False)
    message = relationship(
        "Message",
        backref=backref(
            "received_message"
        )
    )

    status = Column(String, nullable = True)
    timestamp = Column(DateTime(True), nullable = False, server_default = func.now())
    read_msg_timestamp = Column(DateTime(True), nullable = False, server_default = func.now())

    def __init__(self, recipient_id, message_id, status):
        self.recipient_id = recipient_id
        self.message_id = message_id
        self.status = status


class ReportedMessage(db.Model, DataModelMixin):
    __tablename__ = "reported_messages"

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    reporting_user = relationship(
        "User",
        backref=backref(
            "reported_message"
        )
    )

    message_id = Column(Integer, ForeignKey("messages.id"), nullable = False)
    reported_message = relationship(
        "Message",
        backref=backref(
            "reported_message"
        )
    )



