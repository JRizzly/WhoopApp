# Brian Noyle
# Last Edit 2015-12-30
# View for Whoop!!! Messages

import logging
l = logging.getLogger(__name__)

import random
import string
import gevent

from flask import render_template, flash, redirect, url_for, request, current_app, make_response, session, abort
from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from flask.ext.classy import route

from app import app
from app.exceptions import *
from app.util import require, JSONRESTView, login_required_json, DataModelMixin
from app.models.messages import Message, ReceivedMessage
from app.models.offnetwork import OffNetworkContact, OffNetworkBucket, OffNetworkMessage
from app.models.users import User

import json

class Messages(JSONRESTView):
    route_base = "/api/v{}/messages/".format(app.config["API_VERSION"])
    model = Message

    def _to_data(class_, message):
        message_data = message._to_data()

    @login_required_json
    def index(self):
        result_data, query = self._process_pagination()
        message_data = [
            self._to_data()]

    # Posting a WHOOP message first inserts the message into the messages table, then 
    # finds that message_id by matching the send_date value and inserting a new associated
    # entry into the received_messages table 
    @login_required_json
    def post(self):
        sessiondb = current_app.db.session 
        message_data = request.json

        if not message_data["handles"]:
            list_handles = []
        else:
            list_handles = message_data["handles"].split(";") # grab 'handles' from json reference
#        print("list_handles: " + str(list_handles))

        ##  Modifications for posting message to groups
        if not message_data["group_ids"]:
            list_group_ids = []
        else:
            list_group_ids = message_data["group_ids"].split(";") # grab 'group_ids' from json reference
        ##--

        if not message_data["off_network_ids"]:
            list_off_network_ids = []
        else:
            list_off_network_ids = message_data["off_network_ids"].split(";")
        ##  Modifications for posting message to groups
        if not message_data["off_network_group_ids"]:
            list_off_network_group_ids = []
        else:
            list_off_network_group_ids = message_data["off_network_group_ids"].split(";") # grab 'off network group_id' from json reference		
        ##--
#        message_data.pop('handles', None) # delete 'handles' key from json reference so as to insert rest of data into messages table
#        message_data.pop('off_network_ids', None) # delete 'off_network_ids' key from json reference
        ##  Modifications for posting message to groups
#        message_data.pop('group_ids', None) # delete 'group_id' key from json reference so as to insert rest of data into messages table	
#        message_data.pop('off_network_group_ids', None) # delete 'off_network_ids' key from json reference		
        ##--
#        message_data["deleted"] = False
#        message_data["message_forwarded"] = False
#        print("message_data: " + str(message_data))
#        print("list_handles: " + str(list_handles))

        message_insert_data = { 'sender_id' : message_data["sender_id"], 'message_text' : message_data["message_text"], 'message_forwarded' : False, 'deleted' : False } # TODO: add message_config, gps, etc.
        # Insert new message into messages table
        message = Message(**message_insert_data)
        sessiondb.add(message)
        message_id = sessiondb.query(Message.id).filter(Message.message_text == message_data["message_text"]).order_by(Message.send_date.desc()).first() # find newly inserted message's id

        # Create entry in received_messages table per on-network recipient, as found by handle
        if ((list_handles) and (len(list_handles)== len(list_group_ids))):
            for handle in range(len(list_handles)):
                group_id=list_group_ids[handle]
                recipient_id = sessiondb.query(User.id).filter(User.handle == list_handles[handle]).first()
                received_message = ReceivedMessage(recipient_id=recipient_id, message_id= message_id,status='unread',group_id=group_id)
                sessiondb.add(received_message)

        # Sends messages to off-network contacts
        if ((list_off_network_ids) and (len(list_off_network_ids)== len(list_off_network_group_ids))):
            for off_network_id in range(len(list_off_network_ids)):
                group_id=list_off_network_group_ids[off_network_id]
                bucket_id = sessiondb.query(OffNetworkBucket.id).join(OffNetworkContact, OffNetworkBucket.bucket_id == OffNetworkContact.email_address).\
                    filter(OffNetworkContact.id == int(list_off_network_ids[off_network_id])).first()
#                print("bucket_id: " + str(bucket_id))

                off_network_message = OffNetworkMessage(bucket_id, message_id, False, group_id)
                sessiondb.add(off_network_message)        
        return self._respond({})

    @login_required_json
    def delete(self, id):
        message = Message.query.get(id)
        if message is None:
            raise NotFoundError("message not found")

        session = current_app.db.session
#        session.delete (message)
        return self._respond({})


    @login_required_json
    @route("/<message_id>/delete", methods=[ "POST" ])
#    @route("/deletemessage", methods=[ "POST" ])
    def delete_message(self, message_id):

        message_data = request.json

        sessiondb = current_app.db.session
#        message = sessiondb.query(Message).filter(Message.id == message_data['message_id']).first()
#        message = sessiondb.query(Message).filter(Message.id == int(message_id)).first()
        message = Message.query.filter(Message.id == int(message_id)).first()

        dict_result = {}

        if message is None:
            raise NotFoundError("message not found")

        if message.deleted is False:
            message.deleted = True
            return "deleted"

        sessiondb.commit()
        return "not deleted"


Messages.register(app)
