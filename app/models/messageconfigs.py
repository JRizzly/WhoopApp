import logging
l = logging.getLogger(__name__)

from werkzeug import generate_password_hash, check_password_hash

from flask import current_app
from flask.ext.login import UserMixin, current_user

from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Unicode, Binary, DateTime
from sqlalchemy.orm import relationship, backref

from app import app
from app.exceptions import DatabaseValueError
from app.util import DataModelMixin

db = app.db



class MessageConfig(db.Model, DataModelMixin):
    __tablename__ = "message_configs"
    id= Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("message_templates.id"), nullable = False)
    template = relationship(
        "MessageTemplate",
        backref = backref("message_configs")
    )
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable = False)
    sponsor = relationship(
        "Sponsor",
        backref = backref("message_configs")
    )

class Sponsor(db.Model, DataModelMixin):
    __tablename__ = "sponsors"
    id= Column(Integer, primary_key=True)
    name = Column(Unicode, nullable = False, default = "")
    asset = Column(Unicode, nullable = False, default = "")

class MessageTemplate(db.Model, DataModelMixin):
    __tablename__ = "message_templates"
    id= Column(Integer, primary_key=True)
    name = Column(Unicode, nullable = False, default = "")
    template_file_name = Column(Unicode, nullable = False, default = "")