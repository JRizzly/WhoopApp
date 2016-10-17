import unittest

from . import *

from app.users.models import User

class UserViewTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(class_):
        db.drop_all()
        db.create_all()

        session = db.session
        for user in (
            User(username="admin-user", role="admin",
                 password="admin", email="admin@example.com"),
                User(username="user", role="user", password="user", email="user@example.com")):
            session.add(user)
        session.commit()
        class_.login()

    @classmethod
    def tearDownClass(class_):
        class_.logout()
        db.drop_all()

    @classmethod
    def login(class_):
        return client.post(
            "/login",
            data={
                "username": "admin-user",
                "password": "admin"
            },
            follow_redirects=True
        )

    @classmethod
    def logout(class_):
        return client.get("/logout", follow_redirects=True)

    def test_users_listing(self):
        response = client.get("/users")
        assert "var users = [" in response.data