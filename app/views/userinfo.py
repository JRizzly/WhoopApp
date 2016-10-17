
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
from app.util import require, JSONRESTView, login_required_json
from app.models.users import User, AdministratorRole, StandardRole, Role, BlockedUser
from app.models.contacts import Contact, Group, GroupMember
from app.models.notifications import Device, DeviceCharacteristic
from app.models.offnetwork import OffNetworkContact, OffNetworkBucket, OffNetworkGroupMember
from app.views.misc import authenticate

from gcm import GCM


class Contacts(JSONRESTView):
    route_base = "/api/v{}/users/".format(app.config["API_VERSION"])
    model = Contact

    def _to_data(class_, contact):
        contact_data = contact._to_data()

    @login_required_json
    @route("/<user_id>/contacts/<max_contact_id>/<max_offnetwork_id>", methods=[ "GET" ])
    def get (self, user_id, max_contact_id, max_offnetwork_id):
        sessiondb = current_app.db.session
        contacts = sessiondb.query(User.first_name, User.last_name, User.handle, User.email_address, User.mobile_no, Contact.id.label("contact_id"), Contact.timestamp).\
            join(Contact, User.id == Contact.contactee_user_id).filter((Contact.contactor_user_id == user_id) & (Contact.deleted == False) & (Contact.id > int(max_contact_id)) & (User.enabled == True))
        
        off_network_contacts = sessiondb.query(OffNetworkContact.id.label("off_network_id"), OffNetworkContact.first_name, OffNetworkContact.last_name, OffNetworkContact.email_address, OffNetworkContact.mobile_no, OffNetworkContact.timestamp).\
            filter((OffNetworkContact.owning_user_id == user_id) & (OffNetworkContact.active == True) & (OffNetworkContact.deleted == False) & (OffNetworkContact.id > int(max_offnetwork_id)))

        # On-network contacts list
        list_contacts = [ contact._asdict() for contact in contacts.all() ]

        # Off-network contacts list
        list_off_network_contacts = [ contact._asdict() for contact in off_network_contacts.all() ]

        # Concatenate off-network contacts and on-network contacts to get all contacts
        all_contacts = list_contacts + list_off_network_contacts
#        all_contacts.sort()
#        print("dict_contact: " + str(all_contacts))
        return self._respond(all_contacts)

    @login_required_json
    @route("/<user_id>/contacts", methods=[ "POST" ])
    def post (self, user_id):
        sessiondb = current_app.db.session
        contact_data = request.json

        contactee_id = sessiondb.query(User.id).filter(User.email_address == contact_data["email_address"]).\
            filter(User.mobile_no == contact_data["mobile_no"]).first()
#        print("contactee_id: " + str(contactee_id))        

        # If no contactee_id is found, creates off-network contact. 
        # Also checks if off_network_bucket_id is found for entered contactee. If no off_network_bucket_id is found, then creates an off-network bucket.
        # Also checks off-network contact is already added.
        if contactee_id is None:
            
            # Check to see if contactee was already added as off-network contact
            off_network_already_added = sessiondb.query(OffNetworkContact.id).filter(OffNetworkContact.email_address == contact_data['email_address']).\
                filter((OffNetworkContact.owning_user_id == int(user_id)) & (OffNetworkContact.deleted==False )).all()
            if off_network_already_added:
                return "Off-network contact already added"
            
            contact_data['active'] = True
            off_network_contact = OffNetworkContact(**contact_data)
            sessiondb.add(off_network_contact)
            sessiondb.flush()

            # Create off-network bucket for new off-network contact
            off_network_bucket_id = sessiondb.query(OffNetworkBucket.id).filter(OffNetworkBucket.bucket_id == contact_data["email_address"]).first()
            if off_network_bucket_id is None:
                off_network_bucket = OffNetworkBucket(contact_data["email_address"], "email_address")
                sessiondb.add(off_network_bucket)
                return "Off-network contact and bucket added"
            
            return "Off-network contact added."
        else:

            # Check to see if contactee is already added as a contact
            already_added = sessiondb.query(Contact.id).filter(Contact.contactor_user_id == int(user_id)).filter((Contact.contactee_user_id == contactee_id) &( Contact.deleted==False)).all()
            if already_added:
                return "Contact already added."

#            print("contactee_id query: " + str(contactee_id))
#            print("contactee_id: " + str(contactee_id))
            contact = Contact(int(user_id), contactee_id)
            sessiondb.add(contact)
#            return redirect(url_for("Contacts:get", id=contact.id), 303)
            return "Success"

      #---------------------------------------Start new code addition---delete contact from contact list and from all groups--08/08/2016----------------------------

    @login_required_json
    @route("/<user_id>/delete/<contact_id>", methods=["POST"])
    def delete_group(self, user_id, contact_id):

        sessiondb = current_app.db.session

        # Check if contact id is present in the contacts table
        contact_present = sessiondb.query(Contact).filter((Contact.id == contact_id) & (Contact.contactor_user_id == user_id) & (Contact.deleted == False) ).first()

        # If contact id is not present in the contacts table then check if contact id is present in off_network_contacts table
        if contact_present is None:
            off_ntwrk_contact_present = sessiondb.query(OffNetworkContact).filter((OffNetworkContact.id == contact_id) & (OffNetworkContact.owning_user_id == user_id) & (OffNetworkContact.deleted == False) ).first()
            
            if off_ntwrk_contact_present is None:
                raise NotFoundError("contact not found")
            # if contact id is present in the off_network_contacts table then update "deleted" column with True           
            if off_ntwrk_contact_present.deleted is False:
                print ("in off network contact deletion")
                off_ntwrk_contact_present.deleted = True
                sessiondb.commit()            

            off_network_contact_grpMbr_list = sessiondb.query(OffNetworkGroupMember.id).filter((OffNetworkGroupMember.off_network_contact_id == contact_id) & (OffNetworkGroupMember.deleted == False) ).all()	


            if off_network_contact_grpMbr_list is None:
                print ("Off network contact not present in any group")
            else:
                # if contact id is present in the off_network_group_members table then update "deleted" column with True  
                for off_con_id in off_network_contact_grpMbr_list:
                    off_network_grpMbr_delete_contact = sessiondb.query(OffNetworkGroupMember).filter(OffNetworkGroupMember.id == off_con_id).first()	
                    if off_network_grpMbr_delete_contact.deleted is False:
                        off_network_grpMbr_delete_contact.deleted = True
                sessiondb.flush()             
                sessiondb.commit() 
			    
            return "deleted contact from off network contact and off network group members"        
        
            
        # if contact id is present in the contacts table then update "deleted" column with True  
        if contact_present.deleted is False:
            contact_present.deleted = True
            sessiondb.commit()
			
            # if contact id is present in the group_members table then update "deleted" column with True  -- modified 08/11/2016
            contact_groupmember_list = sessiondb.query(GroupMember.id).filter((GroupMember.contact_id == contact_id) & (GroupMember.deleted == False) ).all()
            if contact_groupmember_list is None:
                print("contact not found in group members")
            else:
                for cont_id in contact_groupmember_list:
                    group_member_delete_contact = sessiondb.query(GroupMember).filter(GroupMember.id == cont_id).first()
                    if group_member_delete_contact.deleted is False:
                        group_member_delete_contact.deleted = True
                sessiondb.flush()             
                sessiondb.commit()  
           
            return "deleted user from contacts and groups"
        return "not deleted"

       #---------------------------------------End new code addition---delete contact from contact list and from all groups--08/08/2016----------------------------------   



class Groups(JSONRESTView):
    route_base = "/api/v{}/users/".format(app.config["API_VERSION"])
    model = Group

    def _to_data(class_, group):
        group_data = group._to_data()

    @login_required_json
    @route("/<user_id>/groups/<group_id>", methods=[ "GET" ])
    def get(self, user_id, group_id):
        # Groups table cols: id, name, owner_user_id
        # Since getting the entries, we want to pull groups that the user created (remember that groups are local to the user, so there aren't any global groups, but rather just groups each user makes for their own
            # account so they can send WHOOP!!!s to multiple people simultaneously
        # Similar to POST, it makes the most sense for the URL for the REST calls to be "/<user_id>/groups/"

        # Should be a simple "get groups where owner_user_id = user_id" type query using SQLAlchemy
        # Should return a dictionary (key-value pairs) of data we can use in the client side
            # Ex.: Group name and all the contacts in each group. There may be more, but it's not coming to mind. If you want, you can look at the screens in the mockups doc, and see what's displayed on the screen. 
                # From that, you could determine what else needs to be displayed
        sessiondb = current_app.db.session
        groups = sessiondb.query(Group.name, Group.id, Group.owner_user_id, Group.timestamp).\
            join(User, User.id == Group.owner_user_id).filter((Group.owner_user_id == user_id) & (Group.id > int(group_id)) & (User.enabled == True) & (Group.deleted == False))         
        # Group list of groups
        list_groups = [ group._asdict() for group in groups.all() ] 
        print("dict_group: " + str(list_groups))
        return self._respond(list_groups)  

    @login_required_json
    @route("/<user_id>/groups", methods=[ "POST" ])
    def post(self, user_id):
        # Groups table cols: id, name, owner_user_id
        # Since posting to db, we need the name and the owner_user_id to be passed in order to create a full entry in the Groups table
        # If you look at the other URLs used in REST calls, you'll see that the user_id is already being passed in, so I would follow the REST API guide in Whoop Mockups v.4 in Drive and make it "/<user_id>/groups/"

        # This should be a simple insert into the db using SQLAlchemy
        print("in posting new group")
        sessiondb = current_app.db.session
        group_data = request.json      

        group_id_already_added = sessiondb.query(Group.id).filter(Group.owner_user_id== user_id).\
            filter((Group.name == group_data["name"]) & (Group.deleted == False) ).first()
        print("group_id = " + str(group_id_already_added))
        if group_id_already_added is None:           
#            group = Group(**group_data)
            group = Group(group_data["name"], user_id)
            sessiondb.add(group)
            sessiondb.flush()
            sessiondb.commit()
#            groups = sessiondb.query( Group.id, Group.owner_user_id, Group.timestamp).\
#                join(User, User.id == Group.owner_user_id).filter((Group.owner_user_id == user_id) & (Group.name == group_data["name"])  & (User.enabled == True) & (Group.deleted == False)).order_by(Group.timestamp.desc()).first()
            # Group list of groups
            groups = sessiondb.query( Group.id, Group.owner_user_id, Group.timestamp).\
                join(User, User.id == Group.owner_user_id).filter((Group.owner_user_id == user_id) & (Group.name == group_data["name"])  & (User.enabled == True) & (Group.deleted == False))

            print ("in grp dict")

            #print (groups)
            #group_dict={'group_id':groups[0]}
            #print (group_dict)
            #group_list=[group_dict]
            #return self._respond(group_list)

            list_groups = [ group._asdict() for group in groups.all() ]
            return self._respond(list_groups)
            #return "New group added."
        else:
            return "Group already added."

        #---------------------------------------Start new code addition----------------------------------------------------------------------------------------------------
    @login_required_json
#    @route("/<user_id>/groups/<group_id>/<max_group_member_id>", methods=[ "GET" ])
    @route("/<user_id>/groups/<group_id>/<max_group_member_id>/<max_offnetwork_group_member_id>", methods=[ "GET" ])
    def get_group_members (self, user_id, group_id, max_group_member_id, max_offnetwork_group_member_id ):
        sessiondb = current_app.db.session
        group_members = sessiondb.query(GroupMember.id, GroupMember.contact_id , GroupMember.group_id, GroupMember.timestamp, User.first_name, User.last_name, User.handle, User.email_address, User.mobile_no, Contact.id.label("contact_id")).\
            join(Contact, GroupMember.contact_id == Contact.id).filter((Contact.contactor_user_id == user_id) & (GroupMember.group_id == group_id) & (GroupMember.id > int(max_group_member_id))& (GroupMember.deleted == False) ).\
            join(User, User.id == Contact.contactee_user_id).filter(User.enabled == True) #& (Contact.deleted == False)    

        Off_Network_group_members = sessiondb.query(OffNetworkGroupMember.id, OffNetworkGroupMember.off_network_contact_id , OffNetworkGroupMember.group_id, OffNetworkGroupMember.timestamp, OffNetworkContact.first_name, OffNetworkContact.last_name, OffNetworkContact.email_address, OffNetworkContact.mobile_no, OffNetworkContact.id.label("off_network_id")).\
            join(OffNetworkContact, OffNetworkGroupMember.off_network_contact_id== OffNetworkContact.id).filter((OffNetworkContact.owning_user_id == user_id) & (OffNetworkGroupMember.group_id == group_id) &(OffNetworkContact.active == True) & (OffNetworkGroupMember.id > int(max_offnetwork_group_member_id)) & (OffNetworkGroupMember.deleted == False) )
            

        # Group member list
        list_group_members = [ GroupMember._asdict() for GroupMember in group_members.all() ] 
#        print("dict_group: " + str(list_groups))

        

        # Off-network group member list list
        list_off_network_group_members = [ GroupMember._asdict() for GroupMember in Off_Network_group_members.all() ]

        # Concatenate off-network contacts and on-network contacts to get all contacts
        all_group_members = list_group_members + list_off_network_group_members

#       print("dict_contact: " + str(all_contacts))

        return self._respond(all_group_members)          

        #---------------------------------------End new code addition ----------------------------------------------------------------------------------------------------  

        #---------------------------------------Start new code addition----------------------------------------------------------------------------------------------------
    @login_required_json
    @route("/<user_id>/groups/<group_id>", methods=[ "POST" ])
    def add_contact_to_group(self, user_id, group_id):
        # According to REST API in WhoopMockups v.4, the URL would be "/<user_id>/groups/<group_id>
        #print("In Add Contact to Group")

        sessiondb = current_app.db.session
        group_member_data = request.json      

            # Check to see if group member is present in on network contacts
        group_member_contact_id = sessiondb.query(Contact.id).filter( (Contact.id== group_member_data["group_member_contact_id"]) & (Contact.contactor_user_id == int(user_id)) & (Contact.deleted == False)).first()   
        #print(group_member_contact_id)
        #print("in line 3")
        #print(group_member_data["group_member_contact_id"])


        if group_member_contact_id is None:

            #print("GroupMember not added")
            
            # Check to see if group member was already added as off-network group members
            off_network_grp_already_added = sessiondb.query(OffNetworkGroupMember.id).filter((OffNetworkGroupMember.group_id == group_id) & (OffNetworkGroupMember.off_network_contact_id == group_member_data["group_member_contact_id"] ) & (OffNetworkGroupMember.deleted == False)).first()
            if off_network_grp_already_added :
                return "Off-network group member already added"           
           
          #  group_member_data['active'] = True
            off_network_group_member = OffNetworkGroupMember(off_network_contact_id=group_member_data["group_member_contact_id"], group_id=group_id)
            sessiondb.add(off_network_group_member)
            sessiondb.flush()
            return "Off-network group member added"

        else:
            # Check to see if group member is already added
          
            print("GroupMember already added")

            group_member_already_added = sessiondb.query(GroupMember.id).filter( (GroupMember.group_id == group_id) & (GroupMember.contact_id == group_member_data["group_member_contact_id"]) & (GroupMember.deleted == False) ).first()


            if group_member_already_added:

                return "Group member already added"

            group_member = GroupMember(contact_id=group_member_data["group_member_contact_id"], group_id=group_id)
            sessiondb.add(group_member)
            sessiondb.flush()            
#            return redirect(url_for("Contacts:get", id=contact.id), 303)
            return "New group member added"  


        #---------------------------------------End new code addition ----------------------------------------------------------------------------------------------------

       #---------------------------------------Start new code addition----delete group member-----------------------------------------------------

    @login_required_json
    @route("/<user_id>/delete/<group_id>/<group_member_contact_id>", methods=["POST"])
    def delete_group_member(self, user_id, group_id,group_member_contact_id):

        sessiondb = current_app.db.session
       # group_member_present = sessiondb.query(GroupMember.id,GroupMember.contact_id,GroupMember.group_id,GroupMember.timestamp,GroupMember.deleted).filter((GroupMember.group_id == group_id) & (GroupMember.contact_id == group_member_contact_id) & (GroupMember.deleted == False) ).first()


        group_member_present = sessiondb.query(GroupMember).filter((GroupMember.group_id == group_id) & (GroupMember.contact_id == group_member_contact_id) & (GroupMember.deleted == False) ).first()

        print ("in group member ")
        if group_member_present is None:
            print ("in off netowrk")


            off_network_grpMbr_present = sessiondb.query( OffNetworkGroupMember ).filter((OffNetworkGroupMember.group_id == group_id) & (OffNetworkGroupMember.off_network_contact_id == group_member_contact_id ) & (OffNetworkGroupMember.deleted == False)).first()

            if off_network_grpMbr_present is None:
                raise NotFoundError("Group member not found")
            else:
                if off_network_grpMbr_present.deleted is False:
                    off_network_grpMbr_present.deleted = True
                    print ("in delete off network")

                    sessiondb.commit()
                    return "deleted off network group member"



#        session = current_app.db.session
#        session.delete(group)
#       NEVER DELETE ANYTHING!! Per David, we keep all data and never permenantly remove it from the database. Instead, we add an Active column where if set to False,
#           then it simply won't be displayed :)
#        return self._respond({})

        if group_member_present.deleted is False:
            group_member_present.deleted = True

            sessiondb.commit()
            return "deleted group member"
            

        #sessiondb.commit()
        return "not deleted"

       #---------------------------------------End new code addition ----------------------------------------------------------------------------------------------------


       #---------------------------------------Start new code addition---delete group and all group members present in that group--08/03/2016----------------------------


    @login_required_json
    @route("/<user_id>/delete", methods=["POST"])
    def delete_group(self, user_id):

        sessiondb = current_app.db.session
        group_data_delete = request.json

        group_present = sessiondb.query(Group).filter((Group.id == group_data_delete["group_id"]) & (Group.owner_user_id  == user_id) & (Group.deleted == False) ).first()


        if group_present is None:
            raise NotFoundError("Group not found")

        if group_present.deleted is False:
            print ("in group deletion")
            group_present.deleted = True
            sessiondb.commit()
			
            # Check if group members are associated with the deleted group id 			
            group_member_list = sessiondb.query(GroupMember.id).filter((GroupMember.group_id == group_data_delete["group_id"]) & (GroupMember.deleted == False) ).all()
            
            # Modified code for deletion of all group members of the group --  08/11/2016 
       
            if group_member_list is None:
                print("Group members not found")
            # if group members are associated with the deleted group id then update "Deleted" column as True 	
            else:
                for _id in group_member_list:
                    group_member_delete_list = sessiondb.query(GroupMember).filter(GroupMember.id == _id).first()
                    if group_member_delete_list.deleted is False:
                        print ("in group member deletion")
                        group_member_delete_list.deleted = True
                sessiondb.flush()             
                sessiondb.commit()            

            # Check if off network group members are associated with the deleted group id 	
            off_network_grpMbr_list = sessiondb.query(OffNetworkGroupMember.id).filter((OffNetworkGroupMember.group_id == group_data_delete["group_id"]) & (OffNetworkGroupMember.deleted == False) ).all()	
            if off_network_grpMbr_list is None:
                print("off network Group members not found")
            # if off network group members are associated with the deleted group id then update "Deleted" column as True 	
            else:
                for off_id in off_network_grpMbr_list:
                    off_network_grpMbr_delete_list = sessiondb.query(OffNetworkGroupMember).filter(OffNetworkGroupMember.id == off_id).first()	
                    if off_network_grpMbr_delete_list.deleted is False:
                        print ("in off network group member deletion")
                        off_network_grpMbr_delete_list.deleted = True
                sessiondb.flush()             
                sessiondb.commit()              
		    
            return "deleted group and related group members"

        return "not deleted"

       #---------------------------------------End new code addition---delete group and all group members present in that group--08/03/2016----------------------------------   


class Blocks(JSONRESTView):
    route_base = "api/v{}/users/".format(app.config["API_VERSION"])
    model = BlockedUser

    def _to_data(class_, block):
        block_data = block._to_data()

    @login_required_json
    def post (self, user_id):
        pass

    @login_required_json
    def get (self, user_id):
        pass

    @login_required_json
    def delete (self, user_id, blocked_id):
        pass

class Devices(JSONRESTView):
    route_base = "api/v{}/devices/".format(app.config["API_VERSION"])
    model = Device

    def _to_data(class_, device):
        device_data = device._to_data()

    def get(self, id):
        pass

    def post(self, device_id):
        pass

    @login_required_json
#    @route("/<user_id>", methods=["POST"])
    @route("/add", methods=["POST"])
    def add_device(self):
        sessiondb = current_app.db.session

        device_data = request.json
        user_email_address = device_data["email_address"]
        device_data.pop("email_address", None)
        
        user_id = sessiondb.query(User.id).filter(User.email_address == user_email_address).first()
        if user_id:
            # Add device from which user signed up on
            device = Device(user_id, 'activated')
            sessiondb.add(device)

            # Add device characteristics including InstanceID
            device_id = sessiondb.query(Device.id).filter((Device.owner_user_id == user_id) & (Device.status == 'activated')).first()
#            print("device_id: " + str(device_id))
            device_data['device_id'] = device_id[0]
            device_char = DeviceCharacteristic(**device_data)
            sessiondb.add(device_char)

            sessiondb.flush()
            return self._respond(device_data)
        else:
            raise NotFoundError("User not found")


    @login_required_json
    @route("/instanceid/<user_id>", methods=["POST"])
    def add_instance_id(self, user_id):
        json_instance_id = request.json
        sessiondb = current_app.db.session
        curr_device_data = {} 
        
        curr_device = sessiondb.query(DeviceCharacteristic).join(Device, DeviceCharacteristic.device_id == Device.id).\
            filter((Device.owner_user_id == int(user_id)) & (Device.status == 'activated')).first()
        if curr_device is None:
           print("Instance id - device not found")
        curr_device.instance_id = json_instance_id["instance_id"]
        sessiondb.commit()

        curr_device_data = dict(curr_device.__dict__)
        curr_device_data.pop('_sa_instance_state', None)
#        print("curr_device_data: " + str(curr_device_data))

        return self._respond(curr_device_data)

    @login_required_json
    @route("/<user_id>/check", methods=["POST"])
    def check_device_id(self, user_id):
        sessiondb = current_app.db.session
        
        device_id = sessiondb.query(Device.id).join(User, Device.owner_user_id == User.id).filter((Device.owner_user_id == int(user_id)) & (Device.status == 'activated')).first()
        if device_id:
            return_data["device_id"] = device_id[0]
            instance_id = sessiondb.query(DeviceCharacteristic.instance_id).filter(DeviceCharacteristic.device_id == device_id)
            if instance_id:
                return_data["id_status"] = "exists"
            else:
                return_data["id_status"] = "not_exists"
            
            return self._respond(return_data)
        else:
            # Add device from which user signed up on
            device = Device(user_id, 'activated')
            sessiondb.add(device)

            # Add device characteristics including InstanceID
            device_id = sessiondb.query(Device.id).filter((Device.owner_user_id == user_id) & (Device.status == 'activated')).first()
#            print("device_id: " + str(device_id))
            device_data['device_id'] = device_id[0]
            device_char = DeviceCharacteristic(**device_data)
            sessiondb.add(device_char)

            return_data["device_id"] = device_id[0]
            return_data["id_status"] = "not_exists"

            sessiondb.flush()
            return self._respond(return_data)

 
    # Pushes stuff to GCM cloud server, and then I think GCM sends notifications to device
    @login_required_json
    @route("/sendpush", methods=["POST"])
    def send_push_message(self):
        sessiondb = current_app.db.session
        push_data = request.json

        API_KEY = "AIzaSyA0iP-0iDyc6Lgh0KXGbh0THh_0hHe-ol4"
        gcm = GCM(API_KEY)

        # Could put in icon under "message"
        notification = {
            "title": "New WHOOP!!!",
            "message": push_data["message_text"]
        }

        # Downstream message using JSON request
        if not push_data["handles"]:
            list_handles = []
        else:
            list_handles = push_data["handles"].split(";") # grab 'handles' from json reference

        # Get instance_id for each handle and append to instance_id to pass as reg_ids
        instance_ids = []
        if list_handles:
            for handle in list_handles:
                instance_id = sessiondb.query(DeviceCharacteristic.instance_id).\
                    join(Device, DeviceCharacteristic.device_id == Device.id).\
                    join(User, Device.owner_user_id == User.id).\
                    filter(User.handle == handle).order_by(Device.id.desc()).first()
                if instance_id is None:
                    print("Instance Id Not found")
                else:
                    instance_ids.append(instance_id[0])
#                print("instance_ids: " + str(instance_ids))
#                received_message = ReceivedMessage(recipient_id, message_id, 'unread', False)
#                sessiondb.add(received_message)

        reg_ids = instance_ids
        response = gcm.json_request(registration_ids = reg_ids, data = notification, delay_while_idle=True)

        # Successfully handled registration_ids
        if response and 'success' in response:
            for reg_id, success_id in response['success'].items():
                print('Successfully sent notification for reg_id {0}'.format(reg_id))

        # Handling errors
        if 'errors' in response:
            for error, reg_ids in response['errors'].items():
                # Check for errors and act accordingly
                if error in ['NotRegistered', 'InvalidRegistration']:
                    # Remove reg_ids from database
                    for reg_id in reg_ids:
                        print("Removing reg_id: {0} from db".format(reg_id))

        # Repace reg_id with canonical_id in your database
        if 'canonical' in response:
            for reg_id, canonical_id in response['canonical'].items():
                print("Replacing reg_id: {0} with canonical_id: {1} in db".format(reg_id, canonical_id))

        print("GCM Response: " + str(response))
        return  self._respond(response)


Contacts.register(app)
Groups.register(app)
Devices.register(app)
