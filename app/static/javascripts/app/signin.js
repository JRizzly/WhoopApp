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

var main_vm = new Vue({
    "el": "#app",
    "data": {
        "email_address": "",
        "password": ""
    },
    "methods": {
        "sign_in": function (event) {
            var self = this;

            log.debug(fmt("sign_in called email_address = {} password = {}", self.email_address, self.password));
            
            UserManager.authenticate(self.email_address, self.password).then(
                function (result) {
                    log.debug("authenticate worked - will redirect");
                    var uri = new URI(window.location.href);
                    var query = uri.query(true);
                    if (!_.isUndefined(query["next"])) {
                        window.location.assign(query["next"]);
                    }
                    else {
                        window.location.assign("/");
                    }
                },
                function (reason) {
                    log.error("authentication failed", reason);
                    self.$refs.messages.messages.push({
                        "severity": "warning",
                        "message": reason.message
                    });
                }
            );
        }
    }
});