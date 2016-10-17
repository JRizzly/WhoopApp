# Python file that gets following params:
#   registration tokens (list)
#   message contents (JSON)
# 
# Pushes stuff to GCM cloud server, and then I think GCM sends notifications to device

from gcm import GCM

API_KEY = "AIzaSyA0iP-0iDyc6Lgh0KXGbh0THh_0hHe-ol4"
gcm = GCM(API_KEY)

# Could put in icon under "message"
notification = {
    "title": "New WHOOP!!!",
    "message": ",
}

# Downstream message using JSON request
reg_ids = ['token1', 'token2', 'token3']

res = gcm.json_request(registration_ids = reg_ids, data = notification, delay_while_idle=True)
