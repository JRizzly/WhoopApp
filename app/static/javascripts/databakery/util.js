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

RSVP.on("error", function(reason) {
  log.error(reason);
});

fmt = pystringformat;

Error.prototype.reason = null;
superagent.Request.prototype.promise = function() {
    var self = this;
    return new RSVP.Promise(function(resolve, reject){
        superagent.Request.prototype.end.call(self, function(error, response) {

            // Communication error.
            if (error) {
                reject(error);
                return;
            }

            // Application response.
            if (response.status == 200) {
                resolve(response.body);
                return;
            }

            // Application error.
            var reason;
            if (response.type == "application/json") {
                if (response.body["error_code"] == "AJAX_TOKEN_INVALID") {
                    window.location.reload();
                }
                reason = response.body;
            }
            else {
                reason = {
                    "error_code": "UNKNOWN_SERVER_ERROR",
                    "description": "Server error " + response.status
                };
            }

            var error = new Error(reason["description"]);
            error.reason = reason;
            reject(error);
        });
    });
};

function uuid() {
    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
    }
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
        s4() + '-' + s4() + s4() + s4();
}

var db_modal_mixin = {
    "created": function () {
        var self = this;
        $(window).on("beforeunload", self.modal_before_unload);
    },
    "destroyed": function () {
        var self = this;
        $(window).off("beforeunload", self.modal_before_unload);
    },
    "computed": {
        "is_modal": function () {
            var self = this;
            return self.modal_count > 0;
        }
    },
    "methods": {
        "modal_begin": function () {
            var self = this;
            self.modal_count += 1;
        },
        "modal_end": function () {
            var self = this;
            self.modal_count -= 1;
        },
        "modal_before_unload": function (event) {
            var self = this;
            if (self.is_modal) {
                return "If you leave the page now you may lose some data. Please finish the pending action.";
            }
        }
    }
};

var db_dialog_mixin = {
    "methods": {
        "dialog_open": function (selector) {
            var self = this;

            self.dialog_open_promise = new RSVP.Promise(function (resolve, reject) {
                var modal = self.dialog_modal = UIkit.modal(selector);
                modal.one("show.uk.modal", function (event) {
                    resolve();
                });
                self.dialog_close_promise = new RSVP.Promise(function (resolve, reject) {
                    modal.one("hide.uk.modal", function (event) {
                        resolve();
                    });
                });
                modal.show();
            });

            return self.dialog_open_promise;
        },
        "dialog_close": function () {
            var self = this;
            self.dialog_modal.hide();
            return self.dialog_close_promise;
        }
    }
};

Vue.directive("disabled", function (value) {
    this.el.disabled = !!value;
});

Vue.directive("restrict-input", {
    "bind": function () {
        var self = this;

        if (self.expression == null) {
            return;
        }

        self.restrict_filter = new RegExp(self.expression);

        self.keypress_handler = function (event) {
            if (event.which) {
                var key = event.which;

                if (event.metaKey || event.ctrlKey) {
                    return true;
                }

                // default to allow backspace, delete, tab, escape, enter
                if ($.inArray(key, [0, 46, 8, 9, 27, 13]) > -1) {
                    return true;   
                }

                var character = String.fromCharCode(key);
                if (self.restrict_filter.test(character)){
                    return true;
                }

                event.preventDefault();
                return false;
            }
        }

        $(this.el).on("keypress", self.keypress_handler);
    },
    "unbind": function () {
        $(this.el).off("keypress", self.keypress_handler);
    }
});

/* DEPENDENT ON jQueryUI */
Vue.directive("date", {
    "twoWay": true,
    "bind": function () {
        var self = this;

        $(self.el).datepicker({
            "onSelect": function (date_text, datepicker) {
                self.set(date_text);
            }
        });
    },
    "update": function (new_value, old_value) {
        var self = this;
        self.el.value = new_value;
    },
    "unbind": function () {
        var self = this;
        
        $(self.el).datepicker("destroy");
    }
});

/* DEPENDENT ON intl-tel-input */
Vue.directive("phone-number", {
    "twoWay": true,
    "bind": function () {
        var self = this;

        $(self.el).intlTelInput();

        self.change_handler = function () {
            var phone_number = $(self.el).intlTelInput("getNumber", intlTelInputUtils.numberFormat.E164);
            self.set(phone_number);
        };

        $(self.el).on("change", self.change_handler);
    },
    "unbind": function () {
        var self = this;
        
        $(self.el).off("change", self.change_handler);
        $(self.el).intlTelInput("destroy");
    }
});

Vue.directive("file", {
    "twoWay": true,
    "bind": function () {
        var self = this;

        self.change_handler = function (change_event) {
           var reader = new FileReader();
           reader.onload = function (load_event) {
                self.set(load_event.target.result);
                self.vm.$emit("file-loaded")
           }
           reader.readAsDataURL(change_event.target.files[0]);
        };

        $(self.el).on("change", self.change_handler);
    },
    "unbind": function () {
        var self = this;
        
        $(self.el).off("change", self.change_handler);
    }
});

DataBakery = {};

DataBakery.timeout = function (delay) {
    var timeout_id;
    var promise = new RSVP.Promise(function(resolve, reject) {
        timeout_id = window.setTimeout(resolve, delay);
    });

    return {
        "promise": promise,
        "cancel": function () {
            window.clearTimeout(timeout_id);
        }
    }
};

DataBakery.validators = {
    "email_address": function (email_address) {
        if (email_address == null || email_address == "") {
            return true;
        }

        return /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email_address);
    },
    "not_empty": function (value) {
        return value != null && value.length != 0;
    }
};

// Vue.use(window["vue-validator"]);
