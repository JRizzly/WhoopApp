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

var UserManager;

(function () {

    var API_ROOT = "/api/v1/";

    function common_setup(request) {
        return request
                .set("X-XSRF-TOKEN", Cookies.get("XSRF-TOKEN"))
                .accept("json")
                .promise();
    }

    UserManager = function () {
        var self = {};

        self.delete_user = function (id) {
            var request = superagent.del(API_ROOT + "users/" + id);
            return common_setup(request);
        };

        self.create_user = function (user) {
            var request = superagent.post(API_ROOT + "users/").send(user);
            return common_setup(request);
        };

        self.update_user = function (user) {
            var request = superagent.put(API_ROOT + "users/" + user["id"]).send(user);
            return common_setup(request);
        };

        self.get_users = function () {
            var request = superagent.get(API_ROOT + "users/");
            return common_setup(request);
        };

        self.get_user = function (id) {
            var request = superagent.get(API_ROOT + "users/" + id);
            return common_setup(request);
        };

        self.authenticate = function (email_address, password) {
            var request = superagent
                            .post(API_ROOT + "users/authenticate")
                            .send({
                                "email_address": email_address,
                                "password": password
                            });
            return common_setup(request);
        };

        return self;
    }();

})();


