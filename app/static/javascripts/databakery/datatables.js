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

Vue.component("data-tables", {
    "props": [ "options", "status", "data" ],
    "template": "<table></table>",
    "ready": function () {
        var self = this;

        self.local_options = _.assign(self.options, {
            "dom": '<"uk-hidden"T>lfrtp',
            "paging": false,
            "tableTools": {
                "sRowSelect": "os",
                "aButtons": [ "select_all", "select_none" ],
                "fnRowDeselected": function (nodes) {
                    self.selection_changed();
                },
                "fnRowSelected": function (nodes) {
                    self.selection_changed();
                }
            }
        });

        self.data_table = $(self.$el).DataTable(self.options);
        self.status.$set("one_row_selected", false);
        self.status.$set("one_or_more_rows_selected", false);
        self.status.$set("selection", []);
    },
    "watch": {
        "data": function (value, old_value) {
            var self = this;

            if (_.isUndefined(self.data) || _.isNull(self.data_table)) {
                return;
            }

            self.data_table.clear().rows.add(self.data).draw();
        }
    },
    "methods": {
        "selection_changed": function () {
            var self = this;
            var table_tools = TableTools.fnGetInstance(self.data_table.table().node());
            var nodes = table_tools.fnGetSelected();
            self.status.one_row_selected = nodes.length == 1;
            self.status.one_or_more_rows_selected = nodes.length >= 1;
            self.status.selection = table_tools.fnGetSelectedData();
        }
    }
});

