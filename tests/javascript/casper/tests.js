var casper = require("casper").create();

function loginFormPresent() {
    return $("#login-form").length == 1;
}

casper.start("http://localhost:5002", function() {
    var result = this.evaluate(loginFormPresent);
    this.test.assert(result, "login form is present");
});

casper.run();
