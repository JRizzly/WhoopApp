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

import datetime
import random
import string
import gevent

from flask import render_template, flash, redirect, url_for, request, current_app, make_response, session, abort
from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from flask.ext.classy import route

from app import app
from app.exceptions import *
from app.util import require, JSONRESTView, login_required_json, DataModelMixin
from app.util import require, JSONRESTView, login_required_json
from app.models.users import User, AdministratorRole, StandardRole, Role
from app.models.messages import Message, ReceivedMessage, ReportedMessage
from app.models.contacts import Contact
from app.models.offnetwork import OffNetworkBucket, OffNetworkMessage, OffNetworkContact
from app.models.notifications import Device, DeviceCharacteristic, MessageActivity
from app.views.misc import authenticate
from app.views.userinfo import Devices

from sqlalchemy import update

@app.route("/users", methods=["GET"])
@login_required
@require("can_manage_settings")
def users():
    return render_template(
        "admin/users.html",
        title="Users",
        user=current_user
    )


class Users(JSONRESTView):
    route_base = "/api/v{}/users/".format(app.config["API_VERSION"])
    model = User

    def _ensure_one_admin(self, response):
        current_app.db.session.flush()

        if User.query.join(Role).filter(Role.type == "administrator").count() == 0:
            raise ConsistencyError("There must be at least one administrator in the system.")

        return response

    after_put = _ensure_one_admin
    after_delete = _ensure_one_admin

    @classmethod
    def _to_data(class_, user):
        user_data = user._to_data(
            exclude=[ "password", "_password" ],
            follow={
                "role": {
                    "exclude": [ "id", "user_id" ]
                }
            }
        )

        user_data["__meta__"] = {
            "type": "user",
            "href": url_for("Users:get", id=user.id)
        }
        
        return user_data

    def _role_type_to_role_class(self, role_type):
        return {
            "administrator": AdministratorRole,
            "standard": StandardRole
        }[role_type]

    @login_required_json
    @require("can_manage_settings")
    def index(self):
        result_data, query = self._process_pagination()
        user_data = [
            self._to_data(user)
            for user in query.all()
        ]

        result_data["items"] = user_data
        return self._respond(result_data)

    @login_required_json
    @require("can_get_user")
    def get(self, id):
        if id == "me":
            id = current_user.id

        user = User.query.get(id)
        if user is None:
            raise NotFoundError("user not found")

        user_data = self._to_data(user)
        return self._respond(user_data)

#    @login_required_json
#    @require("can_manage_settings")
    def post(self):
        print("In post user method")
        sign_up_data = request.json
        user_data = sign_up_data["user_info"]
        device_data = sign_up_data["device_info"]
#        print("device_data: " + str(device_data))

        if User.query.filter(User.email_address == user_data["email_address"]).first() is not None:
            raise ValidationError("That email address is already in use.")

        role_data = user_data.pop("role")
        user_data["role"] = self._role_type_to_role_class(role_data["type"])(**role_data)

        print("In post user method")
        user = User(**user_data)

        session = current_app.db.session
        session.add(user)

        new_user_id = session.query(User.id).filter(User.email_address == user_data["email_address"]).first()

        # Check for off-network version of new user. If found, create contacts for all on-network contacts that had new user as off-network contact and deletes off-network version
        list_off_network_ids = session.query(OffNetworkContact).filter(OffNetworkContact.email_address == user_data["email_address"]).all()
#        query_off_network_ids = off_network_ids.all()

        if list_off_network_ids:
#            print("off-network ids: " + str(list_off_network_ids))
            for off_network_id in list_off_network_ids:
                print("off_network_id: " + str(off_network_id))
                contact = Contact(off_network_id.owning_user_id, new_user_id)
                session.add(contact)

                off_network_id.active = False

        # Check for bucket for new user, and if found, dump messages from bucket into received_messages table
        bucket_id = session.query(OffNetworkBucket.id).filter(OffNetworkBucket.bucket_id == user_data["email_address"]).first()
        
        if bucket_id:
#            list_message_id = session.query(OffNetworkMessage.message_id).filter(OffNetworkMessage.off_network_bucket_id == bucket_id).all()
            off_network_messages = session.query(OffNetworkMessage.message_id).filter(OffNetworkMessage.off_network_bucket_id == bucket_id).all()
#            list_contacts = [ message._asdict() for message in off_network_messages.all() ]

#            for message_id in list_message_id:
            for message in off_network_messages:
#                received_message = ReceivedMessage(new_user_id, message_id, 'unread')
                received_message = ReceivedMessage(new_user_id, message[0], 'unread')
                session.add(received_message)

        # Add device from which user signed up on
        device = Device(new_user_id, 'activated')
        session.add(device)

        # Add device characteristics including InstanceID
        device_id = session.query(Device.id).filter(Device.owner_user_id == new_user_id).first()
        device_data['device_id'] = device_id[0]
        device_char = DeviceCharacteristic(**device_data)
        session.add(device_char)

        session.flush()
#        return redirect(url_for("Users:get", id=user.id), 303)
        return "Success"

    @login_required_json
    @require("can_manage_settings")
    def put(self, id):
        user = User.query.get(id)

        if user is None:
            raise NotFoundError("user not found")

        user_data = request.json

        role_data = user_data.pop("role")
        if role_data["type"] == user.role.type:
            user.role._from_data(role_data)
        else:
            user.role = self._role_type_to_role_class(role_data["type"])(**role_data)

        l.debug("user_data = {}".format(user_data))

        user._from_data(user_data, exclude=["id"])

        response = redirect(url_for("Users:get", id=user.id), 303)
        return response

    @login_required_json
    @require("can_manage_settings")
    def delete(self, id):
        user = User.query.get(id)
        if user is None:
            raise NotFoundError("user not found")

        session = current_app.db.session
        session.delete(user)
        return self._respond({})

    @route("/authenticate", methods=[ "POST" ])
    def authenticate(self):
        if authenticate(
            request.json["email_address"],
            request.json["password"]
        ):
#            print("In authenticate")
            sessiondb = current_app.db.session                  
#            user_info = sessiondb.query(User.id, User.first_name, User.last_name, User.mobile_no, User.email_address, User.handle, Device.id.label("device_id")).\
#                join(Device, User.id == Device.owner_user_id).\
#                filter((User.email_address == request.json["email_address"]) & (Device.status == "activated")).first()
            user_info = sessiondb.query(User.id, User.first_name, User.last_name, User.mobile_no, User.email_address, User.handle).filter(User.email_address == request.json["email_address"]).first()
#            print("user dict: " + str(user_info._asdict()))
            return self._respond(user_info._asdict()) # JJH 2-19-2016: pass user info back to device on method call

        raise ForbiddenError("authentication failed")

    @login_required_json
    @route("/signout", methods=[ "POST" ])
    def signout(self):
        user_info = request.json
        sessiondb = current_app.db.session
        device = Device.query.filter((Device.owner_user_id == user_info["user_id"]) & (Device.status == 'activated')).first()
        device.status = 'deactivated'
        sessiondb.commit()

        # Clear out the CSRF token.
        if "xsrf_token" in session:
            del session["xsrf_token"]
        response = make_response()
        response.set_cookie("XSRF-TOKEN", "", expires=0, secure=current_app.config["SESSION_COOKIE_SECURE"])

        logout_user()
        return response
    
    @login_required_json
    @route("/<user_id>/messages/<max_id>", methods=[ "GET" ])
    def user_messages(self, user_id, max_id):
        sessiondb = current_app.db.session

        # Get info of recipient user that user_id sent msg to
        sent_messages_unread = sessiondb.query(User.first_name, User.last_name, Message.id, User.handle, Message.send_date, Message.creator_id, ReceivedMessage.status, ReceivedMessage.message_id, Message.message_text, Message.message_config_id, Message.sender_id, Message.message_forwarded,ReceivedMessage.timestamp ).\
            join(ReceivedMessage, (User.id == ReceivedMessage.recipient_id) & (ReceivedMessage.timestamp== ReceivedMessage.read_msg_timestamp) ).\
            join(Message, ReceivedMessage.message_id == Message.id).\
            filter((Message.sender_id == user_id) & (Message.deleted == False) & (Message.id > int(max_id)))
#            filter((ReceivedMessage.recipient_id == user_id) & (Message.deleted == False) & (Message.message_forwarded == False) & (Message.id > int(max_id)))

        sent_messages_read = sessiondb.query(User.first_name, User.last_name, Message.id, User.handle, Message.send_date, Message.creator_id, ReceivedMessage.status, ReceivedMessage.message_id, Message.message_text, Message.message_config_id, Message.sender_id, Message.message_forwarded,ReceivedMessage.timestamp , ReceivedMessage.read_msg_timestamp).\
            join(ReceivedMessage, (User.id == ReceivedMessage.recipient_id) & (ReceivedMessage.timestamp != ReceivedMessage.read_msg_timestamp)).\
            join(Message, ReceivedMessage.message_id == Message.id).\
            filter((Message.sender_id == user_id) & (Message.deleted == False) & (Message.id > int(max_id)))


        sent_messages_unread_data = [ sent_message._asdict() for sent_message in sent_messages_unread.all() ]

        sent_messages_read_data = [ sent_message._asdict() for sent_message in sent_messages_read.all() ]

        sent_messages_data = sent_messages_unread_data + sent_messages_read_data

        for sent_message in sent_messages_data:
            sent_message["sent"] = True
#        print("sent_messages: " + str(sent_messages_data) + "\n")

        # Get info of senders that sent user_id msgs
        recd_messages = sessiondb.query(User.first_name, User.last_name, Message.id, User.handle, Message.send_date, Message.creator_id, ReceivedMessage.status, ReceivedMessage.message_id, Message.message_text, Message.message_config_id, Message.sender_id, Message.message_forwarded,ReceivedMessage.timestamp , ReceivedMessage.read_msg_timestamp).\
            join(Message, User.id == Message.sender_id).\
            join(ReceivedMessage, Message.id == ReceivedMessage.message_id).\
            filter((ReceivedMessage.recipient_id == user_id) & (Message.deleted == False) & (Message.id > int(max_id)))            
#            filter((ReceivedMessage.recipient_id == user_id) & (Message.deleted == False) & (Message.message_forwarded == False) & (Message.id > int(max_id)))
        recd_messages_data = [ recd_message._asdict() for recd_message in recd_messages.all() ]

        for recd_message in recd_messages_data:
            recd_message["sent"] = False
#        print("recd_messages: " + str(recd_messages_data) + "\n")
        
        forwarded_messages = sessiondb.query(MessageActivity.send_date, MessageActivity.fwded_message_id, ReceivedMessage.status, ReceivedMessage.message_id, Message.message_text, Message.id, User.first_name, User.last_name, User.handle, Message.message_config_id, MessageActivity.from_user_id, Message.message_forwarded, Message.sender_id, Message.creator_id,ReceivedMessage.timestamp , ReceivedMessage.read_msg_timestamp).\
            join(Message, MessageActivity.new_message_id == Message.id).\
            join(ReceivedMessage, MessageActivity.new_message_id == ReceivedMessage.message_id).\
            join(User, MessageActivity.from_user_id == User.id).\
            filter((((MessageActivity.to_user_id == user_id) & (ReceivedMessage.recipient_id == user_id)) | (MessageActivity.from_user_id == user_id)) & (Message.deleted == False) & (Message.id > int(max_id))).\
            order_by(MessageActivity.send_date.desc())

        forwarded_messages_data = [ forwarded_message._asdict() for forwarded_message in forwarded_messages.all() ]

        for forwarded_message in forwarded_messages_data:
            if forwarded_message["from_user_id"] == int(user_id):
                forwarded_message["sent"] = True
            else:
                forwarded_message["sent"] = False
#        print("forwarded_messages data: " + str(forwarded_messages_data) + "\n")

        unsorted_message_data = sent_messages_data + recd_messages_data + forwarded_messages_data

        for message in unsorted_message_data:
            orig_senders = sessiondb.query(MessageActivity.orig_message_id, User.first_name, User.last_name, User.handle).\
                join(User, MessageActivity.creator_id == User.id).\
                filter((MessageActivity.to_user_id == user_id) | (MessageActivity.from_user_id == user_id))

            orig_sender_data = [ orig_sender._asdict() for orig_sender in orig_senders.all() ]

            for orig_sender in orig_sender_data:
                if message['id'] == orig_sender['orig_message_id']:
                    message['orig_first_name'] = orig_sender['first_name']
                    message['orig_last_name'] = orig_sender['last_name']
                    message['orig_handle'] = orig_sender['handle']
                    break

        from operator import itemgetter
        sorted_message_data = sorted(unsorted_message_data, key=lambda k: k['send_date'], reverse=True) 

#        print("sorted_message_data: " + str(sorted_message_data) + "/n")

        return self._respond(sorted_message_data)


       #---------------------------------------Start new code addition---return the status (sent, received, read) for given message id --Modified on 08/15/2016----------------------------

    @login_required_json
    @route("/<user_id>/messages/<message_id>/statustime", methods=[ "GET" ])
    def user_message_statustime(self, user_id, message_id):
        sessiondb = current_app.db.session
        message_read = sessiondb.query(ReceivedMessage.id, ReceivedMessage.message_id , ReceivedMessage.timestamp , ReceivedMessage.read_msg_timestamp ).filter((ReceivedMessage.message_id==message_id) & (ReceivedMessage.timestamp !=ReceivedMessage.read_msg_timestamp) ).all()

        message_unread = sessiondb.query(ReceivedMessage.id, ReceivedMessage.message_id , ReceivedMessage.timestamp ).filter((ReceivedMessage.message_id==message_id) & (ReceivedMessage.timestamp ==ReceivedMessage.read_msg_timestamp)  ).all()
			
        # Message status timestamp list
        list_status= [ message._asdict() for message in message_read ]

        # Unread message status timestamp list
        list_unread_status = [ message._asdict() for message in message_unread ]

        # All message status timestamp list
        all_message_status = list_status + list_unread_status

        return self._respond(all_message_status)	
       #---------------------------------------End new code addition---return the status (sent, received, read) for given message id --Modified on 08/15/2016----------------------------

    @login_required_json
    @route("/<user_id>/messages/<message_id>/status", methods=[ "POST" ])
    def user_message_status(self, user_id, message_id):
        sessiondb = current_app.db.session
        message = sessiondb.query(ReceivedMessage).filter(ReceivedMessage.message_id==message_id).all()
     
        dict_message = {}

        if message is None:
            raise NotFoundError("message not found")
        
        for msg in message:
            # If received message
            if msg.recipient_id == int(user_id):
                if msg.status.lower() == "unread":
                    msg.status = "read"
                    # Update message read time in the table received_messages -- Modified on 08/13/2016
                    msg.read_msg_timestamp = datetime.datetime.now()
                    message_text = sessiondb.query(Message.message_text).filter(Message.id == msg.message_id).first()
                    sender_info = sessiondb.query(User.first_name, User.last_name, User.handle, User.id).join(Message, User.id == Message.sender_id).filter(Message.id == msg.message_id).first()
#                    print("sender: " + str(sender_name))
                    dict_message = dict(msg.__dict__)
                    dict_message['message_text'] = message_text[0]
                    dict_message['sender'] = sender_info[0] + " " + sender_info[1]
                    dict_message['handle'] = sender_info[2]
                    dict_message['sender_id'] = sender_info[3]
                    dict_message['sent'] = False
                    dict_message.pop('_sa_instance_state', None)
                else:                
                    message_text = sessiondb.query(Message.message_text).filter(Message.id == msg.message_id).first()
                    sender_info = sessiondb.query(User.first_name, User.last_name, User.handle, User.id).join(Message, User.id == Message.sender_id).filter(Message.id == msg.message_id).first()
                    dict_message = dict(msg.__dict__)
                    dict_message['message_text'] = message_text[0]
                    dict_message['sender'] = sender_info[0] + " " + sender_info[1]
                    dict_message['handle'] = sender_info[2]
                    dict_message['sender_id'] = sender_info[3]
                    dict_message['sent'] = False
                    dict_message.pop('_sa_instance_state', None)
            # If sent message
            else:
                message_text = sessiondb.query(Message.message_text).filter(Message.id == msg.message_id).first()
#                sender_info = sessiondb.query(User.first_name, User.last_name, User.handle).join(Message, User.id == Message.sender_id).filter(Message.id == msg.message_id).first()

                recipients_list = sessiondb.query(User.first_name, User.last_name, User.handle).\
                    join(ReceivedMessage, User.id == ReceivedMessage.recipient_id).\
                    join(Message, ReceivedMessage.message_id == Message.id).\
                    filter(Message.id == msg.message_id)

                recipients = [ recipient._asdict() for recipient in recipients_list.all() ]
                
                dict_message = dict(msg.__dict__)
                dict_message['message_text'] = message_text[0]
#                dict_message['sender'] = sender_info[0] + " " + sender_info[1]
#                dict_message['handle'] = sender_info[2]
                dict_message['recipients'] = recipients
                dict_message['sent'] = True
                dict_message.pop('_sa_instance_state', None)

        sessiondb.commit()
#        print("message data: " + str(dict_message))
        return self._respond(dict_message)


    @login_required_json
    @route("/<user_id>/messages/<message_id>/forward", methods=[ "POST" ])
    def forward(self, user_id, message_id):
        # user_id = currently logged in user who sent/forwarded message
        # message_id = original message id that was forwarded, not the new fwd message's id

        sessiondb = current_app.db.session
        message_data = request.json
        gps_data = message_data["gps_data"] # TODO: get GPS data

        # Get message id and creator_id of original message
        # Assuming forwarded messages can't change message text
        message_text_list = sessiondb.query(Message.message_text).filter(Message.id == message_id).first()
        message_text = message_text_list[0]
        orig_message_list = sessiondb.query(Message.sender_id, Message.id).filter(Message.message_text == message_text).order_by(Message.send_date.asc()).first()
        orig_message_id = orig_message_list[1]
        creator_id = orig_message_list[0]

        # Set forwarded of forwarded message to True
        message = Message.query.filter(Message.id == int(message_id)).first()
        if message.message_forwarded is False:
            message.message_forwarded = True

        if not message_data["handles"]:
            list_handles = []
        else:
            list_handles = message_data["handles"].split(";") # grab 'handles' from json reference
 #       print("list_handles: " + str(list_handles))

###############
        if not message_data["group_ids"]:
            list_group_ids = []
        else:
            list_group_ids = message_data["group_ids"].split(";") # grab 'group_ids' from json reference		
###############-- 
        if not message_data["off_network_ids"]:
            list_off_network_ids = []
        else:
            list_off_network_ids = message_data["off_network_ids"].split(";")
#            print("handles: " + str(list_off_network_ids))
###############
        if not message_data["off_network_group_ids"]:
            list_off_network_group_ids = []
        else:
            list_off_network_group_ids = message_data["off_network_group_ids"].split(";") # grab 'off network group_id' from json reference
###############--
        # Insert forwarded message as new message in Messages table
        message_insert_data = { 'sender_id' : user_id, 'message_text' : message_text, 'message_forwarded' : False, 'deleted' : False, 'creator_id' : creator_id } # TODO: add message_config, gps, etc.
        message = Message(**message_insert_data)
        sessiondb.add(message)
        fwd_message_id_list = sessiondb.query(Message.id).\
            filter((Message.sender_id == user_id) & (Message.message_text == message_text) & (Message.deleted == False) & (Message.creator_id != None)).\
            order_by(Message.send_date.desc()).first() # find newly inserted message's id
        fwd_message_id = fwd_message_id_list[0]

        # Check to see if this message has been forwarded before
        prev_forwarded_msg_id = sessiondb.query(MessageActivity.id).filter(MessageActivity.orig_message_id == message_id).order_by(MessageActivity.send_date.desc()).first()
#        print("forwarded_message_list = " + str(prev_forwarded_msg_id))

        # Insert forwarded messages in Received Messages table and Message Activity table to mark as forwarded message
        # Create entry in received_messages table per on-network recipient, as found by handle
        if ((list_handles) and (len(list_handles)== len(list_group_ids))):
            for handle in range(len(list_handles)):
                group_id=list_group_ids[handle]
                recipient_id_list = sessiondb.query(User.id).filter(User.handle == list_handles[handle]).first()
                recipient_id = recipient_id_list[0]
#                received_message = ReceivedMessage(recipient_id, fwd_message_id, 'unread', True)
                received_message = ReceivedMessage(recipient_id, fwd_message_id, 'unread',group_id)
                sessiondb.add(received_message)
                # If i == 0, then message was not previously forwarded
                if prev_forwarded_msg_id:
                    forward_insert_data = { 'to_user_id' : recipient_id, 'from_user_id' : int(user_id), 'orig_message_id' : orig_message_id, 'parent_id' : prev_forwarded_msg_id, 'off_network' : False, 'creator_id' : creator_id, 'new_message_id' : fwd_message_id, 'fwded_message_id' : int(message_id) }
                else:
                    forward_insert_data = { 'to_user_id' : recipient_id, 'from_user_id' : int(user_id), 'orig_message_id' : orig_message_id, 'off_network' : False, 'creator_id' : creator_id, 'new_message_id' : fwd_message_id, 'fwded_message_id' : int(message_id) }

                forward_message = MessageActivity(**forward_insert_data)
                sessiondb.add(forward_message)
        else:
            raise NotFoundError("handle not found or handle are not equal to number of groups")


        # Sends messages to off-network contacts' buckets
        if ((list_off_network_ids) and (len(list_off_network_ids)==len(list_off_network_group_ids))):
            for off_network_id in range(len(list_off_network_ids)):
                bucket_id = sessiondb.query(OffNetworkBucket.id).join(OffNetworkContact, OffNetworkBucket.bucket_id == OffNetworkContact.email_address).\
                    filter(OffNetworkContact.id == int(list_off_network_ids[off_network_id])).first()
#                print("bucket_id: " + str(bucket_id))

                off_network_message = OffNetworkMessage(bucket_id, message_id, True,group_id)
                sessiondb.add(off_network_message)

                # If i == 0, then message was not previously forwarded
                if prev_forwarded_msg_id:
                    forward_insert_data = { 'to_user_id' : int(off_network_id), 'from_user_id' : int(user_id), 'orig_message_id' : orig_message_id, 'parent_id' : prev_forwarded_msg_id, 'off_network' : True, 'creator_id' : creator_id, 'new_message_id' : fwd_message_id, 'new_message_id': int(message_id) }
                else:
                    forward_insert_data = { 'to_user_id' : int(off_network_id), 'from_user_id' : int(user_id), 'orig_message_id' : orig_message_id, 'off_network' : True, 'creator_id' : creator_id, 'new_message_id' : fwd_message_id, 'fwded_message_id' : int(message_id) }
                    
                forward_message = MessageActivity(**forward_insert_data)
                sessiondb.add(forward_message)

        return self._respond({})

Users.register(app)


