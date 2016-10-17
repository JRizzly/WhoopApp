/* Copyright (c) 2014 Data Bakery LLC. All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without modification, are permitted
 * provided that the following conditions are met:
 * 
 *     1. Redistributions of source code must retain the above copyright notice, this list of
 * conditions and the following disclaimer.
 * 
 *     2. Redistributions in binary form must reproduce the above copyright notice, this list of
 * conditions and the following disclaimer in the documentation and/or other materials provided with
 * the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY DATA BAKERY LLC ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
 * PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DATA BAKERY LLC OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
 * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

Vue.component("edit-vue", {
    "template": "#edit-vue",
    "mixins": [ db_modal_mixin ],
    "data": function () {
        return {
            "user": {
                "first_name": "",
                "last_name": "",
                "email_address": "",
                "password": "",
                "role": {
                    "type": "standard"
                }
            },
            "submitted": false
        };
    },
    "props": [ "state" ],
    "computed": {
        "valid": function () {
            var self = this;
            var user = self.user;
            var not_empty = DataBakery.validators.not_empty;
            var email_address = DataBakery.validators.email_address;
            var v = {};

            v.first_name = v.first_name_required = not_empty(user.first_name);
            v.last_name = v.last_name_required = not_empty(user.last_name);

            v.email_address_required = not_empty(user.email_address);
            v.email_address_format = email_address(user.email_address);
            v.email_address =
                v.email_address_required &&
                v.email_address_format;

            v.password_require_on_new = 
                self.state.edit.mode == "Edit" || 
                not_empty(user.password);

            v.password = v.password_require_on_new;

            v.all = v.first_name_required && 
                    v.last_name_required &&
                    v.email_address &&
                    v.password;
            return v;
        }
    },
    "methods": {
        "load_user": function (user_id) {
            var self = this;
            UserManager.get_user(user_id).then(
                function success_callback(user) {
                    self.user = user;
                },
                function error_callback(message) {
                    self.$dispatch("add_message", "warning", message);
                }
            );
        },
        "cancel": function (event) {
            event.stopPropagation();

            var self = this;
            self.$dispatch("clear_messages");
            self.$dispatch("exit-edit-vue");
        },
        "save": function (event) {
            event.stopPropagation();

            var self = this;

            self.$dispatch("clear_messages");
            self.submitted = true;

            if (!self.valid.all) {
                self.$dispatch("add_message", "warning", "Please correct the errors below.");
                return;
            }

            self.modal_begin();

            if (self.state.edit.mode == "Edit") {
                // Make sure and don't attempt to update the password if one wasn't
                // specified.
                if (self.user.password == "") {
                    self.user.password = null;
                }
                promise = UserManager.update_user(self.user);
            }
            else if (self.state.edit.mode == "New") {
                promise = UserManager.create_user(self.user);
            }

            promise.finally(function () {
                self.modal_end(); // Must do this before we potentially destroy this vue.
            }).then(
                function success_callback() {
                    self.$dispatch("exit-edit-vue");
                },
                function error_callback(reason) {
                    self.$dispatch("add_message", "warning", reason);
                }
            );
        }
    },
    "attached": function () {
        var self = this;
        if (self.state.edit.user_id != null) {
            UserManager.get_user(self.state.edit.user_id).then(
                function success_callback(user) {
                    self.user = user;
                },
                function error_callback(message) {
                    self.$dispatch("add_message", "warning", message);
                }
            );
        }
    }
});

Vue.component("main-vue", {
    "template": "#main-vue",
    "data": function () {
        return {
            "users_table_options": {
                "columns": [
                    { "title": "First Name", "data": "first_name" },
                    { "title": "Last Name", "data": "last_name" },
                    { "title": "Email Address", "data": "email_address" },
                    { "title": "Role", "data": "role.type" }
                ],
                "scrollY": "400px"
            },
            "users_table_status": {
            },
            "users": []
        };
    },
    "props": [ "state" ],
    "attached": function () {
        var self = this;
        self.refresh_users();
    },
    "methods": {
        "refresh_users": function () {
            var self = this;
            self.state.main.users = [];
            UserManager.get_users().then(
                function success_callback(result) {
                    self.users = result["items"];
                },
                function error_callback(message) {
                    self.$dispatch("add_message", "warning", message);
                }
            );
        },
        "edit": function (event) {
            event.stopPropagation();

            var self = this;
            self.$dispatch("edit", self.users_table_status.selection[0]);
        },
        "new": function (event) {
            event.stopPropagation();

            var self = this;
            self.$dispatch("new");
        },
        "delete": function (event) {
            event.stopPropagation();

            var self = this;

            self.$dispatch("confirm", "Delete", "delete the selected user", function operation() {
                var user = self.users_table_status.selection[0];
                log.debug(fmt("will delete {}", JSON.stringify(user))); 
                UserManager.delete_user(user["id"]).then(
                    function success_callback() {
                        self.refresh_users();
                    },
                    function error_callback(reason) {
                        self.$emit("add_message", "danger", message);
                    }
                );
            });
        }
    }
});
 
var main_vm = new Vue({
    "el": "#app",
    "data": {
        "vue_name": "main-vue",
        "state": {
            "edit": {
                "mode": null,
                "user_id": null
            },
            "main": {
            }
        }
    },
    "events": {
        "confirm": function (operation, description, operation_function) {
            // We use the "self" pattern because many callbacks occur with 'this' pointing to some
            // other object than the Vue.
            var self = this;

            // Because we statically define this component in the template, we can reference it directly
            // rather than throwing events or setting scope parameters.
            self.$refs.confirm.open(operation, description, operation_function);
        },
        "add_message": function (severity, message) {
            var self = this;
            self.$refs.messages.add(severity, message);
        },
        "clear_messages": function () {
            var self = this;
            self.$refs.messages.clear();
        },
        "new": function (user) {
            var self = this;

            // Parameters are passed this way because the view loads asynchronously (when Vue is in non-debug mode) -
            // therefore, we can't reference it with v-ref right after we set the view name. Rather than have
            // it throw an event which would have to be caught here and then could be used to turn around and access
            // the vue (or throw an event back the other way), it is just easier to pass an object with props to the
            // component hosting the views. Then, when the vue's "attached" handler fires, it just looks right here
            // to see what it's configured behavior is.
            //
            // This is all as a result of using a dynamic component (since we can't dynamically change the props).
            self.state.edit.mode = "New";
            self.state.edit.user_id = null;

            // Once the vue_name is changed, the v-component attribtue re-evaluates and the new vue loads. Note that
            // in debug mode, this will happen synchronously right here. In non-debug mode, this will happen asynchrously.
            self.vue_name = "edit-vue";
        },
        "edit": function (user) {
            var self = this;
            self.state.edit.mode = "Edit";
            self.state.edit.user_id = user.id;
            self.vue_name = "edit-vue";
        },
        "exit-edit-vue": function () {
            var self = this;
            self.vue_name = "main-vue";
        }
    }
});

